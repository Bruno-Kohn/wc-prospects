import streamlit as st
import requests
import re
import json
import base64
import pandas as pd
from datetime import date

st.set_page_config(page_title="WC Prospects 2030/2034", page_icon="⚽", layout="centered")

# --- Autenticação para edição ---
if "modo_edicao" not in st.session_state:
    st.session_state["modo_edicao"] = False

with st.sidebar:
    st.subheader("Modo Edição")
    if st.session_state["modo_edicao"]:
        st.success("Edição desbloqueada")
        if st.button("Bloquear edição"):
            st.session_state["modo_edicao"] = False
            st.rerun()
    else:
        senha = st.text_input("Senha de edição", type="password")
        if st.button("Desbloquear"):
            if senha == st.secrets.get("EDIT_PASSWORD", ""):
                st.session_state["modo_edicao"] = True
                st.rerun()
            else:
                st.error("Senha incorreta")

MODO_EDICAO = st.session_state["modo_edicao"]

st.title("⚽ World Cup Prospects")
st.caption("Monitoramento de promessas para 2030 e 2034")

# CSS para botão "Apagar" vermelho
st.markdown("""
<style>
button[kind="primary"] {
    background-color: #dc3545;
    border-color: #dc3545;
    color: white;
    font-weight: bold;
}
button[kind="primary"]:hover {
    background-color: #a71d2a;
    border-color: #a71d2a;
}
table {
    width: 100%;
}
thead tr th {
    background-color: #262730 !important;
    color: white !important;
    font-size: 0.8rem;
}
tbody tr:nth-child(even) {
    background-color: #f0f2f6;
}
tbody tr:nth-child(odd) {
    background-color: #ffffff;
}
tbody tr td {
    font-size: 0.85rem;
    vertical-align: middle !important;
}
</style>
""", unsafe_allow_html=True)

BASE_URL = "https://transfermarkt-api.fly.dev"
GITHUB_REPO = "Bruno-Kohn/wc-prospects"
WATCHLIST_PATH = "watchlist.json"

POSICOES_DEFAULT = [
    "Goleiros",
    "Zagueiros",
    "Laterais Esquerdos",
    "Laterais Direitos",
    "Volantes",
    "Meias",
    "Pontas Esquerdas",
    "Pontas Direitas",
    "Atacantes",
]

TOP_TEAM_LIMITES = {
    "Goleiros": 3,
    "Zagueiros": 4,
    "Laterais Esquerdos": 2,
    "Laterais Direitos": 2,
    "Volantes": 4,
    "Meias": 4,
    "Pontas Esquerdas": 2,
    "Pontas Direitas": 2,
    "Atacantes": 3,
}


# --- GitHub Storage ---
def _github_headers():
    return {
        "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }


def _carregar_watchlist_github() -> dict:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{WATCHLIST_PATH}"
    try:
        resp = requests.get(url, headers=_github_headers(), timeout=10)
        if resp.status_code == 200:
            content = base64.b64decode(resp.json()["content"]).decode()
            return json.loads(content)
        return {"_ordem_posicoes": POSICOES_DEFAULT, "_jogadores": {}}
    except Exception:
        return {"_ordem_posicoes": POSICOES_DEFAULT, "_jogadores": {}}


def _salvar_watchlist_github(data: dict):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{WATCHLIST_PATH}"
    content_b64 = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode()
    payload = {"message": "Update watchlist", "content": content_b64}
    try:
        resp = requests.get(url, headers=_github_headers(), timeout=10)
        if resp.status_code == 200:
            payload["sha"] = resp.json()["sha"]
    except Exception:
        pass
    requests.put(url, headers=_github_headers(), json=payload, timeout=10)


def get_watchlist() -> dict:
    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = _carregar_watchlist_github()
    wl = st.session_state["watchlist"]
    if "_ordem_posicoes" not in wl:
        wl["_ordem_posicoes"] = POSICOES_DEFAULT
    if "_jogadores" not in wl:
        # Migrate old format
        jogadores = {}
        for k, v in wl.items():
            if k not in ("_ordem_posicoes", "_jogadores") and isinstance(v, list):
                jogadores[k] = v
        wl["_jogadores"] = jogadores
        for k in list(jogadores.keys()):
            if k in wl and k not in ("_ordem_posicoes", "_jogadores"):
                del wl[k]
    return wl


def salvar_watchlist():
    wl = st.session_state["watchlist"]
    _salvar_watchlist_github(wl)


# --- API Functions ---
@st.cache_data(ttl=3600)
def buscar_jogadores(nome: str) -> list:
    try:
        resp = requests.get(f"{BASE_URL}/players/search/{nome}", timeout=10)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {e}")
        return []


@st.cache_data(ttl=3600)
def buscar_perfil(player_id: str) -> dict | None:
    try:
        resp = requests.get(f"{BASE_URL}/players/{player_id}/profile", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {e}")
        return None


@st.cache_data(ttl=3600)
def buscar_clube(club_id: str) -> dict | None:
    try:
        resp = requests.get(f"{BASE_URL}/clubs/{club_id}/profile", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


@st.cache_data(ttl=3600)
def buscar_historico_valor(player_id: str) -> list:
    try:
        resp = requests.get(f"{BASE_URL}/players/{player_id}/market_value", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("marketValueHistory", [])
    except Exception:
        return []


@st.cache_data(ttl=300)
def _carregar_stats_cache() -> dict:
    """Carrega stats_cache.json do repositório via GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/stats_cache.json"
    try:
        resp = requests.get(url, headers=_github_headers(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("content")
            if content:
                return json.loads(base64.b64decode(content).decode())
            # Arquivo grande: usar download_url
            download_url = data.get("download_url")
            if download_url:
                resp2 = requests.get(download_url, timeout=15)
                if resp2.status_code == 200:
                    return resp2.json()
    except Exception:
        pass
    return {}


# --- Helpers ---
def extrair_nascimento(description: str) -> str | None:
    match = re.search(r"\*\s*(\d{2}/\d{2}/\d{4})", description or "")
    if match:
        parts = match.group(1).split("/")
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return None


def calcular_idades(data_nascimento: str):
    ano_nasc = int(data_nascimento.split("-")[0])
    mes_nasc = int(data_nascimento.split("-")[1])
    dia_nasc = int(data_nascimento.split("-")[2])
    hoje = date.today()
    idade_atual = hoje.year - ano_nasc - ((hoje.month, hoje.day) < (mes_nasc, dia_nasc))
    return idade_atual, 2030 - ano_nasc, 2034 - ano_nasc


def badge(idade: int) -> str:
    if idade < 24:
        return "👶 Promessa Jovem"
    elif 24 <= idade <= 29:
        return "🔥 Auge Físico/Técnico!"
    else:
        return "👴 Fase de Transição/Veterano"


def formatar_valor(valor):
    if not valor:
        return "N/A"
    if valor >= 1_000_000_000:
        return f"€ {valor / 1_000_000_000:.2f} B"
    if valor >= 1_000_000:
        return f"€ {valor / 1_000_000:.0f} M"
    if valor >= 1_000:
        return f"€ {valor / 1_000:.0f} K"
    return f"€ {valor}"


POSICAO_MAP = {
    "Centre-Forward": "Centroavante",
    "Second Striker": "Segundo Atacante",
    "Left Winger": "Ponta Esquerda",
    "Right Winger": "Ponta Direita",
    "Attacking Midfield": "Meia Atacante",
    "Central Midfield": "Volante",
    "Defensive Midfield": "Volante",
    "Left Midfield": "Meia Esquerda",
    "Right Midfield": "Meia Direita",
    "Left-Back": "Lateral Esquerdo",
    "Right-Back": "Lateral Direito",
    "Centre-Back": "Zagueiro",
    "Goalkeeper": "Goleiro",
}


def traduzir_posicao(pos: str) -> str:
    return POSICAO_MAP.get(pos, pos)


PAIS_MAP = {
    "Spain": "Espanha",
    "England": "Inglaterra",
    "Germany": "Alemanha",
    "Italy": "Itália",
    "France": "França",
    "Brazil": "Brasil",
    "Portugal": "Portugal",
    "Netherlands": "Holanda",
    "Argentina": "Argentina",
    "Belgium": "Bélgica",
    "Scotland": "Escócia",
    "United States": "Estados Unidos",
    "Mexico": "México",
    "Japan": "Japão",
    "South Korea": "Coreia do Sul",
    "Saudi Arabia": "Arábia Saudita",
    "United Arab Emirates": "Emirados Árabes",
    "Qatar": "Catar",
    "Turkey": "Turquia",
    "Russia": "Rússia",
    "Denmark": "Dinamarca",
    "Sweden": "Suécia",
    "Norway": "Noruega",
    "Switzerland": "Suíça",
    "Austria": "Áustria",
    "Poland": "Polônia",
    "Uruguay": "Uruguai",
    "Colombia": "Colômbia",
    "Greece": "Grécia",
    "Croatia": "Croácia",
    "Serbia": "Sérvia",
    "Czech Republic": "República Tcheca",
    "Romania": "Romênia",
    "Ukraine": "Ucrânia",
    "China": "China",
    "Australia": "Austrália",
}


def traduzir_pais(pais: str) -> str:
    return PAIS_MAP.get(pais, pais)


def traduzir_pe(foot: str) -> str:
    foot_map = {"left": "Canhoto", "right": "Destro", "both": "Ambidestro"}
    return foot_map.get((foot or "").lower(), foot or "N/A")


def exibir_card_jogador(perfil, nascimento, mostrar_salvar=True):
    idade_atual, idade_2030, idade_2034 = calcular_idades(nascimento)

    st.divider()

    col_foto, col_info = st.columns([1, 3])
    with col_foto:
        img = perfil.get("imageUrl")
        if img:
            st.image(img, width=90)
    with col_info:
        st.subheader(perfil.get("fullName") or perfil.get("name"))
        clube = perfil.get("club", {})
        pos_traduzida = traduzir_posicao(perfil.get("position", {}).get("main", "N/A"))
        st.markdown(
            f"**Clube:** {clube.get('name', 'N/A')} | "
            f"**Posição:** {pos_traduzida} | "
            f"**Pé:** {traduzir_pe(perfil.get('foot'))}  \n"
            f"**Altura:** {perfil.get('height', 'N/A')} cm | "
            f"**Valor de mercado:** {formatar_valor(perfil.get('marketValue'))}  \n"
            f"**Nascimento:** {nascimento} | **Idade atual:** {idade_atual} anos"
        )

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Copa 2030", f"{idade_2030} anos")
        st.caption(badge(idade_2030))
    with c2:
        st.metric("Copa 2034", f"{idade_2034} anos")
        st.caption(badge(idade_2034))

    if mostrar_salvar:
        st.divider()
        wl = get_watchlist()
        col_pos, col_btn = st.columns([2, 1])
        with col_pos:
            posicao = st.selectbox("Salvar na posição", POSICOES_DEFAULT, key=f"pos_{perfil.get('id')}")
        with col_btn:
            st.write("")
            st.write("")
            if st.button("💾 Salvar", use_container_width=True, key=f"save_{perfil.get('id')}", disabled=not MODO_EDICAO):
                jogadores = wl["_jogadores"]
                if posicao not in jogadores:
                    jogadores[posicao] = []
                player_ids = [p["id"] for p in jogadores[posicao]]
                pid = str(perfil.get("id"))
                if pid in player_ids:
                    st.warning("Jogador já está nessa posição!")
                else:
                    club_country = ""
                    club_id = perfil.get("club", {}).get("id")
                    if club_id:
                        club_data = buscar_clube(str(club_id))
                        if club_data:
                            club_country = club_data.get("league", {}).get("countryName", "")
                    jogadores[posicao].append({
                        "id": pid,
                        "name": perfil.get("fullName") or perfil.get("name"),
                        "club": perfil.get("club", {}).get("name", "N/A"),
                        "clubCountry": club_country,
                        "nascimento": nascimento,
                        "imageUrl": perfil.get("imageUrl"),
                        "marketValue": perfil.get("marketValue"),
                        "position": perfil.get("position", {}).get("main", "N/A"),
                        "foot": perfil.get("foot", "N/A"),
                        "height": perfil.get("height"),
                    })
                    salvar_watchlist()
                    st.success(f"✅ {perfil.get('name')} salvo em {posicao}!")


# --- UI ---
tab_busca, tab_watchlist, tab_topteam, tab_comparador, tab_campo = st.tabs(["Buscar", "Watchlist", "Top Team", "Comparador", "Campinho"])

with tab_busca:
    nome = st.text_input("Nome do jogador", placeholder="Ex: Lamine Yamal")

    if st.button("Buscar", use_container_width=True):
        if not nome.strip():
            st.warning("Digite o nome de um jogador.")
        else:
            with st.spinner("Buscando dados em tempo real..."):
                resultados = buscar_jogadores(nome.strip())
            if not resultados:
                st.warning("Nenhum jogador encontrado. Tente outro nome.")
            else:
                st.session_state["resultados"] = resultados
                st.session_state["perfil"] = None
                st.session_state["nascimento"] = None

    if "resultados" in st.session_state and st.session_state["resultados"]:
        resultados = st.session_state["resultados"]
        opcoes = {
            f"{r['name']} ({r.get('club', {}).get('name', 'N/A')})": r
            for r in resultados
        }
        escolha = st.selectbox("Selecione o jogador", options=list(opcoes.keys()))
        jogador = opcoes[escolha]

        if st.session_state.get("perfil_id") != jogador["id"]:
            with st.spinner("Carregando perfil..."):
                perfil = buscar_perfil(jogador["id"])
            if perfil:
                st.session_state["perfil"] = perfil
                st.session_state["perfil_id"] = jogador["id"]
                st.session_state["nascimento"] = extrair_nascimento(perfil.get("description"))

        perfil = st.session_state.get("perfil")
        nascimento = st.session_state.get("nascimento")

        if perfil and nascimento:
            exibir_card_jogador(perfil, nascimento, mostrar_salvar=True)
        elif perfil and not nascimento:
            st.error("Data de nascimento indisponível.")

with tab_watchlist:
    wl = get_watchlist()
    posicoes = wl["_ordem_posicoes"]
    jogadores = wl["_jogadores"]

    if not jogadores:
        st.info("Nenhum jogador salvo ainda. Use a aba Buscar para adicionar.")
    else:
        @st.dialog("Atualizar dados dos jogadores")
        def modal_atualizar():
            st.write("Esta ação irá buscar os dados mais recentes de todos os jogadores salvos na sua Watchlist (clube, valor de mercado, etc).")
            st.write("Dependendo da quantidade de jogadores, isso pode levar alguns segundos.")
            col_cancel, col_confirm = st.columns(2)
            with col_cancel:
                if st.button("Cancelar", use_container_width=True):
                    st.rerun()
            with col_confirm:
                if st.button("Atualizar", use_container_width=True, type="primary"):
                    total = sum(len(v) for v in jogadores.values())
                    progress = st.progress(0, text="Atualizando...")
                    count = 0
                    for pos, lista in jogadores.items():
                        for j in lista:
                            perfil = buscar_perfil(j["id"])
                            if perfil:
                                nascimento = extrair_nascimento(perfil.get("description"))
                                j["name"] = perfil.get("fullName") or perfil.get("name") or j["name"]
                                j["club"] = perfil.get("club", {}).get("name", "N/A")
                                j["imageUrl"] = perfil.get("imageUrl")
                                j["marketValue"] = perfil.get("marketValue")
                                j["position"] = perfil.get("position", {}).get("main", "N/A")
                                j["foot"] = perfil.get("foot", "N/A")
                                j["height"] = perfil.get("height")
                                if nascimento:
                                    j["nascimento"] = nascimento
                                club_id = perfil.get("club", {}).get("id")
                                if club_id:
                                    club_data = buscar_clube(str(club_id))
                                    if club_data:
                                        j["clubCountry"] = club_data.get("league", {}).get("countryName", "")
                            count += 1
                            progress.progress(count / total, text=f"Atualizando {count}/{total}...")
                    salvar_watchlist()
                    st.session_state["watchlist"] = wl
                    st.success("Dados atualizados com sucesso!")
                    st.rerun()

        if st.button("Atualizar dados", use_container_width=True, disabled=not MODO_EDICAO):
            modal_atualizar()

        # --- Filtros ---
        with st.expander("Filtros"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_idade_max = st.number_input("Idade máxima", min_value=15, max_value=45, value=45, step=1, key="f_idade")
                filtro_pe = st.selectbox("Pé", ["Todos", "Canhoto", "Destro", "Ambidestro"], key="f_pe")
            with col_f2:
                filtro_valor_min = st.selectbox(
                    "Valor mínimo",
                    options=[0, 5, 10, 25, 50, 75, 100, 125, 150, 175, 200],
                    format_func=lambda x: f"€{x}M" if x > 0 else "Sem mínimo",
                    key="f_valor",
                )
                filtro_posicao = st.multiselect("Posição", options=POSICOES_DEFAULT, default=[], key="f_posicao")
            # Coletar clubes únicos dos jogadores
            clubes_unicos = sorted(set(
                j.get("club", "")
                for pos in POSICOES_DEFAULT
                for j in jogadores.get(pos, [])
                if j.get("club")
            ))
            filtro_clube = st.multiselect("Clube", options=clubes_unicos, default=[], key="f_clube")
            filtro_top = st.checkbox("Apenas jogadores do Top Team", key="f_top")

            col_btn_f, col_btn_c = st.columns(2)
            with col_btn_f:
                if st.button("Filtrar", use_container_width=True):
                    st.session_state["filtros_ativos"] = {
                        "idade_max": filtro_idade_max,
                        "pe": filtro_pe,
                        "valor_min": filtro_valor_min * 1_000_000,
                        "posicao": filtro_posicao,
                        "clube": filtro_clube,
                        "top": filtro_top,
                    }
            with col_btn_c:
                if st.button("Limpar filtros", use_container_width=True):
                    st.session_state.pop("filtros_ativos", None)
                    st.rerun()

        filtros = st.session_state.get("filtros_ativos")

        def aplicar_filtros(jogador):
            if not filtros:
                return True
            nasc = jogador.get("nascimento")
            if nasc:
                idade, _, _ = calcular_idades(nasc)
            else:
                idade = 0
            if idade > filtros["idade_max"]:
                return False
            valor = jogador.get("marketValue") or 0
            if valor < filtros["valor_min"]:
                return False
            if filtros["pe"] != "Todos":
                pe_map = {"left": "Canhoto", "right": "Destro", "both": "Ambidestro"}
                pe_jogador = pe_map.get((jogador.get("foot") or "").lower(), "")
                if pe_jogador != filtros["pe"]:
                    return False
            if filtros["clube"] and jogador.get("club") not in filtros["clube"]:
                return False
            if filtros["top"] and not jogador.get("top_team"):
                return False
            return True

        posicoes_exibir = filtros["posicao"] if filtros and filtros["posicao"] else POSICOES_DEFAULT
        total_filtrado = 0
        for pos in posicoes_exibir:
            lista_filtrada = [j for j in jogadores.get(pos, []) if aplicar_filtros(j)]
            total_filtrado += len(lista_filtrada)

        total_geral = sum(len(jogadores.get(p, [])) for p in POSICOES_DEFAULT)
        if filtros:
            st.caption(f"Filtro ativo — Exibindo {total_filtrado} de {total_geral} jogadores")
        else:
            st.caption(f"Total de jogadores na Watchlist: {total_geral}")

        for posicao in posicoes_exibir:
            lista = [j for j in jogadores.get(posicao, []) if aplicar_filtros(j)]
            if not lista:
                continue

            st.subheader(f"{posicao} ({len(lista)})")

            for j_idx, j in enumerate(lista):
                nascimento = j.get("nascimento")
                if nascimento:
                    idade_atual, idade_2030, idade_2034 = calcular_idades(nascimento)
                else:
                    idade_atual = idade_2030 = idade_2034 = "?"

                is_top = j.get("top_team", False)
                with st.container(border=True):
                    col_star, col_foto, col_dados, col_rm = st.columns([0.5, 1, 4, 1])
                    with col_star:
                        star_label = "★" if is_top else "☆"
                        if st.button(star_label, key=f"star_{posicao}_{j['id']}", disabled=not MODO_EDICAO):
                            if is_top:
                                j["top_team"] = False
                                salvar_watchlist()
                                st.rerun()
                            else:
                                # Check limit
                                lista_original = jogadores.get(posicao, [])
                                top_count = sum(1 for p in lista_original if p.get("top_team"))
                                limite = TOP_TEAM_LIMITES.get(posicao, 0)
                                if top_count >= limite:
                                    st.session_state[f"top_team_full_{posicao}"] = True
                                    st.rerun()
                                else:
                                    j["top_team"] = True
                                    salvar_watchlist()
                                    st.rerun()
                    with col_foto:
                        if j.get("imageUrl"):
                            st.image(j["imageUrl"], width=55)
                    with col_dados:
                        pos_traduzida = traduzir_posicao(j.get("position", ""))
                        st.markdown(
                            f"**{j['name']}** | {j.get('club', 'N/A')}  \n"
                            f"{pos_traduzida} | {j.get('height', '?')} cm | {traduzir_pe(j.get('foot'))} | {formatar_valor(j.get('marketValue'))}  \n"
                            f"Idade: {idade_atual} anos | Em 2030: {idade_2030} anos | Em 2034: {idade_2034} anos",
                        )
                    with col_rm:
                        if st.button("Apagar", key=f"rm_{posicao}_{j['id']}", type="primary", disabled=not MODO_EDICAO):
                            lista_original = jogadores.get(posicao, [])
                            jogadores[posicao] = [p for p in lista_original if p["id"] != j["id"]]
                            if not jogadores[posicao]:
                                del jogadores[posicao]
                            salvar_watchlist()
                            st.rerun()

                    # Histórico de valor de mercado e estatísticas
                    with st.expander("Mais detalhes", expanded=False):
                        # Estatísticas de carreira consolidadas
                        stats_cache = _carregar_stats_cache()
                        player_stats = stats_cache.get(j["id"], {})
                        metricas = player_stats.get("metricas", {})
                        if metricas:
                            st.markdown(f"**Estatísticas de carreira** ({player_stats.get('sofascore_name', '')})")
                            for label, valor in metricas.items():
                                st.caption(f"{label}: {valor}")
                        else:
                            st.caption("Estatísticas não disponíveis. Execute 'python coletar_stats.py' localmente.")

                        # Histórico de valor de mercado (Transfermarkt)
                        historico = buscar_historico_valor(j["id"])
                        if historico:
                            st.markdown("**Evolução do valor de mercado**")
                            datas = [h.get("date", "") for h in historico]
                            valores = [h.get("value", 0) for h in historico]
                            df = pd.DataFrame({"Data": datas, "Valor (€)": valores})
                            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
                            df = df.dropna(subset=["Data"]).sort_values("Data")
                            st.line_chart(df.set_index("Data")["Valor (€)"])

            # Show warning if limit reached
            if st.session_state.pop(f"top_team_full_{posicao}", False):
                limite = TOP_TEAM_LIMITES.get(posicao, 0)
                st.warning(f"Limite de {limite} jogadores para {posicao} atingido. Remova um antes de adicionar outro.")

with tab_topteam:
    wl = get_watchlist()
    jogadores = wl.get("_jogadores", {})

    total_convocados = 0
    idades = []
    for posicao in POSICOES_DEFAULT:
        lista = jogadores.get(posicao, [])
        convocados = [j for j in lista if j.get("top_team")]
        total_convocados += len(convocados)
        for j in convocados:
            nasc = j.get("nascimento")
            if nasc:
                idade, _, _ = calcular_idades(nasc)
                idades.append(idade)

    media_str = f" | Média de idade: {sum(idades) / len(idades):.1f} anos" if idades else ""
    st.subheader(f"Convocação — 26 jogadores{media_str}")

    # Valor de mercado total
    valor_total = sum(
        j.get("marketValue", 0) or 0
        for pos in POSICOES_DEFAULT
        for j in jogadores.get(pos, [])
        if j.get("top_team")
    )
    st.caption(f"Convocados: {total_convocados}/26 | Valor de mercado total: {formatar_valor(valor_total)}")
    st.divider()

    for posicao in POSICOES_DEFAULT:
        lista = jogadores.get(posicao, [])
        convocados = [j for j in lista if j.get("top_team")]
        limite = TOP_TEAM_LIMITES[posicao]

        if not convocados:
            st.markdown(f"**{posicao}** ({0}/{limite})")
            st.caption("Nenhum jogador selecionado.")
            st.divider()
            continue

        st.markdown(f"**{posicao}** ({len(convocados)}/{limite})")
        for j in convocados:
            nascimento = j.get("nascimento")
            if nascimento:
                idade_atual, idade_2030, idade_2034 = calcular_idades(nascimento)
            else:
                idade_atual = idade_2030 = idade_2034 = "?"

            col_foto, col_dados = st.columns([1, 5])
            with col_foto:
                if j.get("imageUrl"):
                    st.image(j["imageUrl"], width=45)
            with col_dados:
                pos_traduzida = traduzir_posicao(j.get("position", ""))
                st.markdown(
                    f"**{j['name']}** — {j.get('club', 'N/A')}  \n"
                    f"{pos_traduzida} | {j.get('height', '?')} cm | {formatar_valor(j.get('marketValue'))} | "
                    f"Idade: {idade_atual} | 2030: {idade_2030} | 2034: {idade_2034}"
                )
        st.divider()

with tab_comparador:
    wl = get_watchlist()
    jogadores = wl.get("_jogadores", {})

    todos_jogadores = []
    for pos in POSICOES_DEFAULT:
        for j in jogadores.get(pos, []):
            todos_jogadores.append(j)

    if len(todos_jogadores) < 2:
        st.info("Adicione pelo menos 2 jogadores na Watchlist para usar o comparador.")
    else:
        opcoes_comp = {f"{j['name']} — {traduzir_posicao(j.get('position', ''))} ({j.get('club', 'N/A')})": j for j in todos_jogadores}
        nomes = list(opcoes_comp.keys())

        selecionados = st.multiselect(
            "Selecione 2 ou 3 jogadores para comparar",
            options=nomes,
            max_selections=3,
        )

        if len(selecionados) >= 2:
            jogadores_comp = [opcoes_comp[s] for s in selecionados]
            cols = st.columns(len(jogadores_comp))

            for idx, j in enumerate(jogadores_comp):
                with cols[idx]:
                    if j.get("imageUrl"):
                        st.image(j["imageUrl"], width=80)
                    st.markdown(f"**{j['name']}**")

                    nascimento = j.get("nascimento")
                    if nascimento:
                        idade_atual, idade_2030, idade_2034 = calcular_idades(nascimento)
                    else:
                        idade_atual = idade_2030 = idade_2034 = "?"

                    pos_traduzida = traduzir_posicao(j.get("position", ""))

                    st.markdown(
                        f"**Clube:** {j.get('club', 'N/A')}  \n"
                        f"**País:** {traduzir_pais(j.get('clubCountry', ''))}  \n"
                        f"**Posição:** {pos_traduzida}  \n"
                        f"**Altura:** {j.get('height', '?')} cm  \n"
                        f"**Pé:** {traduzir_pe(j.get('foot'))}  \n"
                        f"**Valor:** {formatar_valor(j.get('marketValue'))}  \n"
                        f"**Idade atual:** {idade_atual}  \n"
                        f"**Em 2030:** {idade_2030}  \n"
                        f"**Em 2034:** {idade_2034}"
                    )
        elif selecionados:
            st.warning("Selecione pelo menos 2 jogadores.")

with tab_campo:
    wl = get_watchlist()
    jogadores_campo = wl.get("_jogadores", {})

    todos = []
    for pos in POSICOES_DEFAULT:
        for j in jogadores_campo.get(pos, []):
            todos.append(j)

    FORMACOES = {
        "4-3-3": {
            "GOL": (50, 92),
            "LD": (85, 72), "ZAG1": (65, 75), "ZAG2": (35, 75), "LE": (15, 72),
            "VOL": (50, 52), "MC1": (25, 45), "MC2": (75, 45),
            "PD": (85, 20), "CA": (50, 12), "PE": (15, 20),
        },
        "4-4-2": {
            "GOL": (50, 92),
            "LD": (85, 72), "ZAG1": (65, 75), "ZAG2": (35, 75), "LE": (15, 72),
            "MD": (85, 48), "VOL1": (65, 50), "VOL2": (35, 50), "ME": (15, 48),
            "ATA1": (35, 15), "ATA2": (65, 15),
        },
        "4-2-3-1": {
            "GOL": (50, 92),
            "LD": (85, 72), "ZAG1": (65, 75), "ZAG2": (35, 75), "LE": (15, 72),
            "VOL1": (35, 55), "VOL2": (65, 55),
            "PD": (80, 35), "MEI": (50, 32), "PE": (20, 35),
            "CA": (50, 12),
        },
        "4-1-4-1": {
            "GOL": (50, 92),
            "LD": (85, 72), "ZAG1": (65, 75), "ZAG2": (35, 75), "LE": (15, 72),
            "VOL": (50, 58),
            "MD": (85, 38), "MC1": (62, 40), "MC2": (38, 40), "ME": (15, 38),
            "CA": (50, 12),
        },
        "4-4-1-1": {
            "GOL": (50, 92),
            "LD": (85, 72), "ZAG1": (65, 75), "ZAG2": (35, 75), "LE": (15, 72),
            "MD": (85, 48), "VOL1": (62, 50), "VOL2": (38, 50), "ME": (15, 48),
            "MEI": (50, 28),
            "CA": (50, 12),
        },
        "4-3-1-2": {
            "GOL": (50, 92),
            "LD": (85, 72), "ZAG1": (65, 75), "ZAG2": (35, 75), "LE": (15, 72),
            "VOL": (50, 55), "MC1": (25, 50), "MC2": (75, 50),
            "MEI": (50, 32),
            "ATA1": (35, 15), "ATA2": (65, 15),
        },
        "3-4-3": {
            "GOL": (50, 92),
            "ZAG1": (25, 75), "ZAG2": (50, 78), "ZAG3": (75, 75),
            "ALD": (90, 50), "VOL1": (62, 52), "VOL2": (38, 52), "ALE": (10, 50),
            "PD": (80, 20), "CA": (50, 12), "PE": (20, 20),
        },
        "3-5-2": {
            "GOL": (50, 92),
            "ZAG1": (25, 75), "ZAG2": (50, 78), "ZAG3": (75, 75),
            "ALD": (90, 50), "VOL1": (65, 52), "MEI": (50, 42), "VOL2": (35, 52), "ALE": (10, 50),
            "ATA1": (35, 15), "ATA2": (65, 15),
        },
        "5-3-2": {
            "GOL": (50, 92),
            "ALD": (90, 70), "LD": (72, 75), "ZAG": (50, 78), "LE": (28, 75), "ALE": (10, 70),
            "VOL": (50, 50), "MC1": (30, 45), "MC2": (70, 45),
            "ATA1": (35, 15), "ATA2": (65, 15),
        },
        "5-4-1": {
            "GOL": (50, 92),
            "ALD": (90, 70), "LD": (72, 75), "ZAG": (50, 78), "LE": (28, 75), "ALE": (10, 70),
            "MD": (85, 45), "VOL1": (62, 48), "VOL2": (38, 48), "ME": (15, 45),
            "CA": (50, 12),
        },
    }

    formacao_escolhida = st.selectbox("Formação", list(FORMACOES.keys()), key="formacao_campo")
    posicoes_form = FORMACOES[formacao_escolhida]

    # Carregar escalação salva
    escalacao_salva = wl.get("_campinho", {})

    if not todos:
        st.info("Adicione jogadores na Watchlist para montar o time.")
    else:
        # Mapeamento de posição no campo → posição na watchlist
        POS_KEY_TO_WATCHLIST = {
            "GOL": "Goleiros",
            "ZAG": "Zagueiros", "ZAG1": "Zagueiros", "ZAG2": "Zagueiros", "ZAG3": "Zagueiros",
            "LD": "Laterais Direitos", "ALD": "Laterais Direitos",
            "LE": "Laterais Esquerdos", "ALE": "Laterais Esquerdos",
            "VOL": "Volantes", "VOL1": "Volantes", "VOL2": "Volantes",
            "MC1": "Meias", "MC2": "Meias", "MEI": "Meias",
            "MD": "Pontas Direitas", "PD": "Pontas Direitas",
            "ME": "Pontas Esquerdas", "PE": "Pontas Esquerdas",
            "CA": "Atacantes", "ATA1": "Atacantes", "ATA2": "Atacantes",
        }

        # Layout: campinho à esquerda, dropdowns à direita
        col_campo, col_dropdowns = st.columns([1, 1])

        # Seleção de jogadores por posição
        escalacao = {}
        with col_dropdowns:
            st.caption("Selecione um jogador para cada posição:")
            for pos_key in posicoes_form.keys():
                watchlist_pos = POS_KEY_TO_WATCHLIST.get(pos_key, "")
                jogadores_pos = jogadores_campo.get(watchlist_pos, [])
                opcoes_pos = {f"{j['name']} ({j.get('club', '')})": j for j in jogadores_pos}
                nomes_pos = ["(vazio)"] + list(opcoes_pos.keys())

                # Restaurar seleção salva
                saved_id = escalacao_salva.get(formacao_escolhida, {}).get(pos_key)
                default_idx = 0
                if saved_id:
                    for i, label in enumerate(nomes_pos):
                        if i > 0 and opcoes_pos.get(label, {}).get("id") == saved_id:
                            default_idx = i
                            break

                c_label, c_select = st.columns([1, 3])
                with c_label:
                    st.markdown(f"**{pos_key}**")
                with c_select:
                    escolha = st.selectbox(
                        pos_key,
                        options=nomes_pos,
                        index=default_idx,
                        key=f"campo_{formacao_escolhida}_{pos_key}",
                        label_visibility="collapsed",
                    )
                if escolha != "(vazio)":
                    escalacao[pos_key] = opcoes_pos[escolha]

            # Botão salvar escalação
            if st.button("Salvar escalação", use_container_width=True, disabled=not MODO_EDICAO):
                if "_campinho" not in wl:
                    wl["_campinho"] = {}
                wl["_campinho"][formacao_escolhida] = {
                    pos_key: escalacao[pos_key]["id"]
                    for pos_key in escalacao
                }
                salvar_watchlist()
                st.success("Escalação salva!")

        # Desenhar campo
        with col_campo:
            campo_html = """
            <div style="position:relative;width:100%;aspect-ratio:2/3;background:linear-gradient(to bottom, #2d8a4e 0%, #3da060 50%, #2d8a4e 100%);
                        border-radius:12px;border:3px solid white;overflow:hidden;">
                <div style="position:absolute;top:50%;left:10%;right:10%;height:2px;background:rgba(255,255,255,0.4);"></div>
                <div style="position:absolute;top:50%;left:50%;width:70px;height:70px;
                            border:2px solid rgba(255,255,255,0.4);border-radius:50%;
                            transform:translate(-50%,-50%);"></div>
                <div style="position:absolute;bottom:0;left:25%;right:25%;height:50px;
                            border:2px solid rgba(255,255,255,0.4);border-bottom:none;"></div>
            """

            for pos_key, (x, y) in posicoes_form.items():
                jogador = escalacao.get(pos_key)
                if jogador and jogador.get("imageUrl"):
                    img_html = f"<img src='{jogador['imageUrl']}' style='width:45px;height:auto;border-radius:4px;display:block;'/>"
                else:
                    img_html = f"<div style='width:45px;height:58px;border-radius:8px;background:rgba(255,255,255,0.3);border:2px solid white;display:flex;align-items:center;justify-content:center;font-size:0.55rem;color:white;'>{pos_key}</div>"

                campo_html += f"""
                <div style="position:absolute;left:{x}%;top:{y}%;transform:translate(-50%,-50%);text-align:center;">
                    {img_html}
                </div>
                """

            campo_html += "</div>"
            import streamlit.components.v1 as components
            components.html(campo_html, height=700)

        # Estatísticas da escalação
        if escalacao:
            st.divider()
            idades_campo = []
            valor_campo = 0
            for j in escalacao.values():
                nasc = j.get("nascimento")
                if nasc:
                    idade, _, _ = calcular_idades(nasc)
                    idades_campo.append(idade)
                valor_campo += j.get("marketValue") or 0

            c1, c2 = st.columns(2)
            with c1:
                if idades_campo:
                    st.metric("Idade média", f"{sum(idades_campo) / len(idades_campo):.1f} anos")
            with c2:
                st.metric("Valor de mercado total", formatar_valor(valor_campo))

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
    from components.campinho import campinho

    wl = get_watchlist()
    jogadores_campo = wl.get("_jogadores", {})

    # Todos os jogadores do Top Team para escalar
    todos_top = []
    for pos in POSICOES_DEFAULT:
        for j in jogadores_campo.get(pos, []):
            if j.get("top_team"):
                todos_top.append(j)

    # Templates de formação (ponto de partida)
    FORMACOES_TEMPLATE = {
        "4-3-3": [(50, 92), (85, 72), (65, 75), (35, 75), (15, 72), (50, 52), (25, 42), (75, 42), (85, 18), (50, 10), (15, 18)],
        "4-4-2": [(50, 92), (85, 72), (65, 75), (35, 75), (15, 72), (85, 48), (62, 50), (38, 50), (15, 48), (35, 15), (65, 15)],
        "4-2-3-1": [(50, 92), (85, 72), (65, 75), (35, 75), (15, 72), (35, 55), (65, 55), (80, 35), (50, 32), (20, 35), (50, 12)],
        "3-5-2": [(50, 92), (25, 75), (50, 78), (75, 75), (90, 50), (65, 52), (50, 42), (35, 52), (10, 50), (35, 15), (65, 15)],
        "3-4-3": [(50, 92), (25, 75), (50, 78), (75, 75), (90, 50), (62, 52), (38, 52), (10, 50), (80, 18), (50, 10), (20, 18)],
    }

    # Carregar posições salvas
    posicoes_salvas = wl.get("_campinho_pos", {})

    # Seleção de jogadores escalados
    if not todos_top:
        st.info("Marque jogadores como ⭐ Top Team na Watchlist para escalá-los aqui.")
    else:
        # Estatísticas no topo
        if posicoes_salvas:
            escalados = [j for j in todos_top if j["id"] in posicoes_salvas]
            if escalados:
                _idades = []
                _valor = 0
                for j in escalados:
                    nasc = j.get("nascimento")
                    if nasc:
                        idade, _, _ = calcular_idades(nasc)
                        _idades.append(idade)
                    _valor += j.get("marketValue") or 0
                media_str = f"Média de idade: {sum(_idades)/len(_idades):.1f} anos" if _idades else ""
                valor_str = f"Valor de mercado total: {formatar_valor(_valor)}"
                st.caption(f"{len(escalados)} jogadores escalados | {media_str} | {valor_str}")

        # Seleção de jogadores + template
        col_sel, col_template = st.columns([3, 1])
        with col_sel:
            opcoes = {f"{j['name']} ({j.get('club', '')})": j for j in todos_top}
            # Default: jogadores já no campo
            default_sel = [k for k, v in opcoes.items() if v["id"] in posicoes_salvas]
            selecionados = st.multiselect(
                "Jogadores no campo",
                options=list(opcoes.keys()),
                default=default_sel,
                max_selections=11,
                key="campo_jogadores_sel",
            )
        with col_template:
            template = st.selectbox("Template", ["(manter)"] + list(FORMACOES_TEMPLATE.keys()), key="campo_template")

        # Montar posicoes para o componente
        jogadores_sel = [opcoes[s] for s in selecionados if s in opcoes]

        # Se aplicou template, resetar posições
        if template != "(manter)":
            coords = FORMACOES_TEMPLATE[template]
            posicoes_input = {}
            for i, j in enumerate(jogadores_sel):
                if i < len(coords):
                    posicoes_input[j["id"]] = {"x": coords[i][0], "y": coords[i][1]}
                else:
                    posicoes_input[j["id"]] = {"x": 50, "y": 50}
        else:
            # Usar posições salvas, ou distribuir novos jogadores
            posicoes_input = {}
            idx_new = 0
            default_positions = [(50, 92), (80, 72), (60, 75), (40, 75), (20, 72),
                                 (70, 50), (50, 50), (30, 50), (75, 25), (50, 15), (25, 25)]
            for j in jogadores_sel:
                if j["id"] in posicoes_salvas:
                    posicoes_input[j["id"]] = posicoes_salvas[j["id"]]
                else:
                    pos = default_positions[idx_new % len(default_positions)]
                    posicoes_input[j["id"]] = {"x": pos[0], "y": pos[1]}
                    idx_new += 1

        # Dados para o componente
        jogadores_data = [
            {"id": j["id"], "name": j["name"], "imageUrl": j.get("imageUrl", "")}
            for j in jogadores_sel
        ]

        # Renderizar componente interativo
        novas_posicoes = campinho(jogadores=jogadores_data, posicoes=posicoes_input, key="campinho_main")

        # Botão salvar
        if st.button("💾 Salvar posições", use_container_width=True, disabled=not MODO_EDICAO):
            wl["_campinho_pos"] = novas_posicoes
            salvar_watchlist()
            st.success("Posições salvas!")



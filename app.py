import streamlit as st
import requests
import re
import json
import base64
from datetime import date

st.set_page_config(page_title="WC Prospects 2030/2034", page_icon="⚽", layout="centered")

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
    if valor >= 1_000_000:
        return f"€{valor / 1_000_000:.0f}M"
    if valor >= 1_000:
        return f"€{valor / 1_000:.0f}K"
    return f"€{valor}"


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
            f"**Pé:** {perfil.get('foot', 'N/A')}  \n"
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
            if st.button("💾 Salvar", use_container_width=True, key=f"save_{perfil.get('id')}"):
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
tab_busca, tab_watchlist = st.tabs(["🔍 Buscar", "📋 Watchlist"])

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

        if st.button("Atualizar dados", use_container_width=True):
            modal_atualizar()

        for posicao in POSICOES_DEFAULT:
            lista = jogadores.get(posicao, [])
            if not lista:
                continue

            st.subheader(posicao)

            for j_idx, j in enumerate(lista):
                nascimento = j.get("nascimento")
                if nascimento:
                    idade_atual, idade_2030, idade_2034 = calcular_idades(nascimento)
                else:
                    idade_atual = idade_2030 = idade_2034 = "?"

                with st.container(border=True):
                    col_foto, col_dados, col_rm = st.columns([1, 4, 1])
                    with col_foto:
                        if j.get("imageUrl"):
                            st.image(j["imageUrl"], width=55)
                    with col_dados:
                        pos_traduzida = traduzir_posicao(j.get("position", ""))
                        st.markdown(
                            f"**{j['name']}** | {j.get('club', 'N/A')}  \n"
                            f"{pos_traduzida} | {j.get('height', '?')} cm | {formatar_valor(j.get('marketValue'))}  \n"
                            f"Idade: {idade_atual} anos | Em 2030: {idade_2030} anos | Em 2034: {idade_2034} anos",
                        )
                    with col_rm:
                        if st.button("Apagar", key=f"rm_{posicao}_{j['id']}", type="primary"):
                            lista.pop(j_idx)
                            if not lista:
                                del jogadores[posicao]
                            salvar_watchlist()
                            st.rerun()

import streamlit as st
import requests
import re
import json
import base64
from datetime import date

st.set_page_config(page_title="WC Prospects 2030/2034", page_icon="⚽", layout="centered")

st.title("⚽ World Cup Prospects")
st.caption("Monitoramento de promessas para 2030 e 2034")

BASE_URL = "https://transfermarkt-api.fly.dev"
GITHUB_REPO = "Bruno-Kohn/wc-prospects"
WATCHLIST_PATH = "watchlist.json"

POSICOES = [
    "Goleiros",
    "Laterais Direitos",
    "Zagueiros",
    "Laterais Esquerdos",
    "Volantes",
    "Meias",
    "Meias Atacantes",
    "Pontas Direitas",
    "Pontas Esquerdas",
    "Atacantes",
]


# --- GitHub Storage ---
def _github_headers():
    return {
        "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }


def carregar_watchlist() -> dict:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{WATCHLIST_PATH}"
    try:
        resp = requests.get(url, headers=_github_headers(), timeout=10)
        if resp.status_code == 200:
            content = base64.b64decode(resp.json()["content"]).decode()
            return json.loads(content)
        return {}
    except Exception:
        return {}


def salvar_watchlist(data: dict):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{WATCHLIST_PATH}"
    content_b64 = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode()
    payload = {
        "message": "Update watchlist",
        "content": content_b64,
    }
    try:
        resp = requests.get(url, headers=_github_headers(), timeout=10)
        if resp.status_code == 200:
            payload["sha"] = resp.json()["sha"]
    except Exception:
        pass
    requests.put(url, headers=_github_headers(), json=payload, timeout=10)


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


def exibir_card_jogador(perfil, nascimento, mostrar_salvar=True):
    idade_atual, idade_2030, idade_2034 = calcular_idades(nascimento)

    st.divider()

    col_foto, col_info = st.columns([1, 2])
    with col_foto:
        img = perfil.get("imageUrl")
        if img:
            st.image(img, width=100)
    with col_info:
        st.subheader(perfil.get("fullName") or perfil.get("name"))
        clube = perfil.get("club", {})
        st.write(f"**Clube:** {clube.get('name', 'N/A')}")
        st.write(f"**Idade atual:** {idade_atual} anos")
        st.write(f"**Altura:** {perfil.get('height', 'N/A')} cm")
        st.write(f"**Posição:** {perfil.get('position', {}).get('main', 'N/A')}")
        st.write(f"**Pé:** {perfil.get('foot', 'N/A')}")
        st.write(f"**Valor de mercado:** {formatar_valor(perfil.get('marketValue'))}")
        st.write(f"**Nascimento:** {nascimento}")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Copa 2030 🏆", f"{idade_2030} anos")
        st.info(badge(idade_2030))
    with c2:
        st.metric("Copa 2034 🏆", f"{idade_2034} anos")
        st.info(badge(idade_2034))

    if mostrar_salvar:
        st.divider()
        col_pos, col_btn = st.columns([2, 1])
        with col_pos:
            posicao = st.selectbox("Salvar na posição", POSICOES, key=f"pos_{perfil.get('id')}")
        with col_btn:
            st.write("")
            st.write("")
            if st.button("💾 Salvar", use_container_width=True, key=f"save_{perfil.get('id')}"):
                watchlist = carregar_watchlist()
                if posicao not in watchlist:
                    watchlist[posicao] = []
                player_ids = [p["id"] for p in watchlist[posicao]]
                pid = str(perfil.get("id"))
                if pid in player_ids:
                    st.warning("Jogador já está nessa posição!")
                else:
                    watchlist[posicao].append({
                        "id": pid,
                        "name": perfil.get("fullName") or perfil.get("name"),
                        "club": perfil.get("club", {}).get("name", "N/A"),
                        "nascimento": nascimento,
                        "imageUrl": perfil.get("imageUrl"),
                        "marketValue": perfil.get("marketValue"),
                        "position": perfil.get("position", {}).get("main", "N/A"),
                        "foot": perfil.get("foot", "N/A"),
                        "height": perfil.get("height"),
                    })
                    salvar_watchlist(watchlist)
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
    watchlist = carregar_watchlist()

    if not watchlist:
        st.info("Nenhum jogador salvo ainda. Use a aba Buscar para adicionar.")
    else:
        for posicao in POSICOES:
            jogadores = watchlist.get(posicao, [])
            if not jogadores:
                continue
            st.subheader(f"📌 {posicao}")
            for j in jogadores:
                with st.expander(f"{j['name']} — {j['club']}"):
                    nascimento = j.get("nascimento")
                    if nascimento:
                        idade_atual, idade_2030, idade_2034 = calcular_idades(nascimento)
                        col_f, col_i = st.columns([1, 2])
                        with col_f:
                            if j.get("imageUrl"):
                                st.image(j["imageUrl"], width=80)
                        with col_i:
                            st.write(f"**Clube:** {j['club']}")
                            st.write(f"**Idade atual:** {idade_atual} anos")
                            st.write(f"**Posição real:** {j.get('position', 'N/A')}")
                            st.write(f"**Valor:** {formatar_valor(j.get('marketValue'))}")

                        c1, c2 = st.columns(2)
                        with c1:
                            st.metric("2030 🏆", f"{idade_2030} anos")
                            st.caption(badge(idade_2030))
                        with c2:
                            st.metric("2034 🏆", f"{idade_2034} anos")
                            st.caption(badge(idade_2034))

                    if st.button("🗑️ Remover", key=f"rm_{posicao}_{j['id']}"):
                        watchlist[posicao] = [p for p in watchlist[posicao] if p["id"] != j["id"]]
                        if not watchlist[posicao]:
                            del watchlist[posicao]
                        salvar_watchlist(watchlist)
                        st.rerun()

import streamlit as st
import requests
from datetime import datetime
from utils import POSICOES_DEFAULT, calcular_idades, formatar_valor, badge, traduzir_pe
from github_api import get_watchlist, salvar_watchlist

SOFASCORE_BASE = "https://www.sofascore.com/api/v1"
SOFASCORE_HEADERS = {"User-Agent": "Mozilla/5.0"}

SOFASCORE_POSITION_MAP = {
    "G": "Goleiro",
    "D": "Zagueiro",
    "M": "Meia",
    "F": "Atacante",
}

SOFASCORE_POSITION_TO_WATCHLIST = {
    "G": "Goleiros",
    "D": "Zagueiros",
    "M": "Meias",
    "F": "Atacantes",
}


def _buscar_sofascore(nome: str) -> list:
    """Busca jogadores no SofaScore."""
    try:
        resp = requests.get(
            f"{SOFASCORE_BASE}/search/all",
            params={"q": nome, "page": 0},
            headers=SOFASCORE_HEADERS,
            timeout=10,
        )
        if resp.status_code == 403:
            st.error("SofaScore bloqueou a requisição (403). Tente rodar localmente.")
            return []
        resp.raise_for_status()
        data = resp.json()
        return [r["entity"] for r in data.get("results", []) if r.get("type") == "player"]
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {e}")
        return []


def _buscar_perfil_sofascore(player_id: int) -> dict | None:
    """Busca perfil completo do jogador no SofaScore."""
    try:
        resp = requests.get(
            f"{SOFASCORE_BASE}/player/{player_id}",
            headers=SOFASCORE_HEADERS,
            timeout=10,
        )
        if resp.status_code == 403:
            st.error("SofaScore bloqueou a requisição (403).")
            return None
        resp.raise_for_status()
        return resp.json().get("player")
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {e}")
        return None


def _timestamp_to_date(ts: int) -> str:
    """Converte timestamp Unix para YYYY-MM-DD."""
    return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")


def _get_image_url(player_id: int) -> str:
    return f"https://api.sofascore.app/api/v1/player/{player_id}/image"


def render(modo_edicao: bool):
    nome = st.text_input("Nome do jogador", placeholder="Ex: Raphinha, Savinho, Endrick")

    if st.button("Buscar", use_container_width=True):
        if not nome.strip():
            st.warning("Digite o nome de um jogador.")
        else:
            with st.spinner("Buscando no SofaScore..."):
                resultados = _buscar_sofascore(nome.strip())
            if not resultados:
                st.warning("Nenhum jogador encontrado.")
            else:
                st.session_state["resultados_sf"] = resultados
                st.session_state["perfil_sf"] = None

    if "resultados_sf" in st.session_state and st.session_state["resultados_sf"]:
        resultados = st.session_state["resultados_sf"]
        opcoes = {
            f"{r['name']} ({r.get('team', {}).get('name', 'N/A')})": r
            for r in resultados
        }
        escolha = st.selectbox("Selecione o jogador", options=list(opcoes.keys()))
        jogador = opcoes[escolha]

        if st.session_state.get("perfil_sf_id") != jogador["id"]:
            with st.spinner("Carregando perfil..."):
                perfil = _buscar_perfil_sofascore(jogador["id"])
            if perfil:
                st.session_state["perfil_sf"] = perfil
                st.session_state["perfil_sf_id"] = jogador["id"]

        perfil = st.session_state.get("perfil_sf")

        if perfil:
            _exibir_card(perfil, modo_edicao)


def _exibir_card(perfil: dict, modo_edicao: bool):
    player_id = perfil["id"]
    nome = perfil.get("name", "")
    nascimento_ts = perfil.get("dateOfBirthTimestamp")

    if not nascimento_ts:
        st.error("Data de nascimento indisponível.")
        return

    nascimento = _timestamp_to_date(nascimento_ts)
    idade_atual, idade_2030, idade_2034 = calcular_idades(nascimento)

    st.divider()

    col_foto, col_info = st.columns([1, 3])
    with col_foto:
        st.image(_get_image_url(player_id), width=90)
    with col_info:
        st.subheader(nome)
        clube = perfil.get("team", {}).get("name", "N/A")
        posicao = SOFASCORE_POSITION_MAP.get(perfil.get("position", ""), perfil.get("position", "N/A"))
        foot = perfil.get("preferredFoot", "")
        foot_map = {"Left": "Canhoto", "Right": "Destro", "Both": "Ambidestro"}
        pe = foot_map.get(foot, foot or "N/A")
        altura = perfil.get("height", "N/A")
        valor = perfil.get("proposedMarketValue")

        st.markdown(
            f"**Clube:** {clube} | "
            f"**Posição:** {posicao} | "
            f"**Pé:** {pe}  \n"
            f"**Altura:** {altura} cm | "
            f"**Valor de mercado:** {formatar_valor(valor)}  \n"
            f"**Nascimento:** {nascimento} | **Idade atual:** {idade_atual} anos"
        )

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Copa 2030", f"{idade_2030} anos")
        st.caption(badge(idade_2030))
    with c2:
        st.metric("Copa 2034", f"{idade_2034} anos")
        st.caption(badge(idade_2034))

    # Salvar na watchlist
    st.divider()
    wl = get_watchlist()
    col_pos, col_btn = st.columns([2, 1])
    with col_pos:
        posicao_wl = st.selectbox("Salvar na posição", POSICOES_DEFAULT, key=f"pos_sf_{player_id}")
    with col_btn:
        st.write("")
        st.write("")
        if st.button("💾 Salvar", use_container_width=True, key=f"save_sf_{player_id}", disabled=not modo_edicao):
            jogadores = wl["_jogadores"]
            if posicao_wl not in jogadores:
                jogadores[posicao_wl] = []
            player_ids = [p["id"] for p in jogadores[posicao_wl]]
            pid = str(player_id)
            if pid in player_ids:
                st.warning("Jogador já está nessa posição!")
            else:
                foot_save = {"Left": "left", "Right": "right", "Both": "both"}.get(foot, "")
                clube_country = perfil.get("team", {}).get("country", {}).get("name", "")
                jogadores[posicao_wl].append({
                    "id": pid,
                    "sofascore_id": player_id,
                    "name": nome,
                    "club": perfil.get("team", {}).get("name", "N/A"),
                    "clubCountry": clube_country,
                    "nascimento": nascimento,
                    "imageUrl": _get_image_url(player_id),
                    "marketValue": valor,
                    "position": perfil.get("position", ""),
                    "foot": foot_save,
                    "height": perfil.get("height"),
                })
                salvar_watchlist()
                st.success(f"✅ {nome} salvo em {posicao_wl}!")

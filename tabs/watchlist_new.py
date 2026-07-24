import streamlit as st
import requests
import re
from datetime import datetime
from utils import POSICOES_DEFAULT, TOP_TEAM_LIMITES, calcular_idades, formatar_valor, traduzir_posicao, traduzir_pe
from github_api import get_watchlist_new, salvar_watchlist_new


def _get_sofascore_base():
    return st.secrets.get("SOFASCORE_PROXY_URL", "https://www.sofascore.com/api/v1")


SOFASCORE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Cache-Control": "no-cache",
}

POSICAO_SOFASCORE_MAP = {
    "G": "Goleiro",
    "D": "Zagueiro",
    "M": "Volante",
    "F": "Atacante",
}

POSICAO_GRUPO_MAP = {
    "Goleiro": "Goleiros",
    "Zagueiro": "Zagueiros",
    "Lateral Esquerdo": "Laterais Esquerdos",
    "Lateral Direito": "Laterais Direitos",
    "Volante": "Volantes",
    "Meia": "Meias",
    "Meia Atacante": "Meias Atacantes",
    "Ponta Esquerda": "Pontas Esquerdas",
    "Ponta Direita": "Pontas Direitas",
    "Atacante": "Atacantes",
    "Centroavante": "Atacantes",
    "Segundo Atacante": "Atacantes",
}


def _buscar_jogadores(query: str) -> list[dict]:
    """Busca jogadores no SofaScore."""
    try:
        resp = requests.get(
            f"{_get_sofascore_base()}/search/all",
            params={"q": query, "type": "player"},
            headers=SOFASCORE_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        jogadores = []
        for r in results:
            entity = r.get("entity", {})
            team = entity.get("team", {})
            sport = team.get("sport", {})
            if sport.get("slug") == "football" and r.get("type") == "player":
                jogadores.append({
                    "sofascore_id": entity["id"],
                    "name": entity.get("name", ""),
                    "team": team.get("name", ""),
                    "team_country": team.get("country", {}).get("name", ""),
                    "position": POSICAO_SOFASCORE_MAP.get(entity.get("position", ""), entity.get("position", "")),
                    "country": entity.get("country", {}).get("name", ""),
                })
        return jogadores
    except Exception as e:
        st.error(f"Erro na busca: {e}")
        return []


def _buscar_perfil(sofascore_id: int) -> dict | None:
    """Busca perfil completo do jogador."""
    try:
        resp = requests.get(
            f"{_get_sofascore_base()}/player/{sofascore_id}",
            headers=SOFASCORE_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("player", {})
    except Exception:
        return None


def _montar_jogador(perfil: dict, sofascore_id: int) -> dict:
    """Monta dict do jogador no formato da watchlist."""
    nascimento = ""
    ts = perfil.get("dateOfBirthTimestamp")
    if ts:
        nascimento = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")

    foot_map = {"Left": "left", "Right": "right", "Both": "both"}
    foot = foot_map.get(perfil.get("preferredFoot", ""), "")

    return {
        "id": str(sofascore_id),
        "name": perfil.get("name", ""),
        "club": perfil.get("team", {}).get("name", "N/A"),
        "clubCountry": perfil.get("team", {}).get("country", {}).get("name", ""),
        "nascimento": nascimento,
        "imageUrl": f"https://api.sofascore.app/api/v1/player/{sofascore_id}/image",
        "marketValue": perfil.get("proposedMarketValue"),
        "position": perfil.get("position", ""),
        "foot": foot,
        "height": perfil.get("height"),
        "sofascore_id": sofascore_id,
    }


@st.dialog("Adicionar jogador")
def _modal_adicionar(jogador_sel: dict):
    st.write(f"**{jogador_sel['name']}** — {jogador_sel['team']}")

    posicoes_disponiveis = POSICOES_DEFAULT
    posicao_sugerida = POSICAO_GRUPO_MAP.get(jogador_sel.get("position", ""), "Atacantes")
    idx_default = posicoes_disponiveis.index(posicao_sugerida) if posicao_sugerida in posicoes_disponiveis else 0

    grupo = st.selectbox("Posição na Watchlist", options=posicoes_disponiveis, index=idx_default)

    posicao_individual = st.text_input(
        "Posição específica (ex: Volante, Ponta Direita, Meia)",
        value=jogador_sel.get("position", ""),
    )

    col_cancel, col_confirm = st.columns(2)
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            del st.session_state["jogador_selecionado"]
            st.rerun()
    with col_confirm:
        if st.button("Confirmar", use_container_width=True, type="primary"):
            with st.spinner("Buscando dados completos..."):
                perfil = _buscar_perfil(jogador_sel["sofascore_id"])

            if perfil:
                jogador = _montar_jogador(perfil, jogador_sel["sofascore_id"])
                jogador["position"] = posicao_individual or jogador["position"]
            else:
                jogador = {
                    "id": str(jogador_sel["sofascore_id"]),
                    "name": jogador_sel["name"],
                    "club": jogador_sel["team"],
                    "clubCountry": jogador_sel["team_country"],
                    "nascimento": "",
                    "imageUrl": f"https://api.sofascore.app/api/v1/player/{jogador_sel['sofascore_id']}/image",
                    "marketValue": None,
                    "position": posicao_individual or jogador_sel.get("position", ""),
                    "foot": "",
                    "height": None,
                    "sofascore_id": jogador_sel["sofascore_id"],
                }

            wl = get_watchlist_new()
            jogadores = wl["_jogadores"]
            if grupo not in jogadores:
                jogadores[grupo] = []

            # Verificar duplicata
            ids_existentes = [j.get("sofascore_id") for j in jogadores[grupo]]
            if jogador["sofascore_id"] in ids_existentes:
                st.error("Jogador já existe nessa posição!")
            else:
                jogadores[grupo].append(jogador)
                salvar_watchlist_new()
                st.success(f"{jogador['name']} adicionado em {grupo}!")
                del st.session_state["jogador_selecionado"]
                st.session_state.pop("busca_resultados", None)
                st.rerun()


def render(modo_edicao: bool):
    wl = get_watchlist_new()
    jogadores = wl["_jogadores"]

    # --- Busca ---
    st.subheader("Adicionar jogador")
    if not modo_edicao:
        st.info("Desbloqueie o modo edição para adicionar jogadores.")

    st.markdown("[🔍 Buscar no SofaScore](https://www.sofascore.com/search?q=)", unsafe_allow_html=True)
    st.caption("Busque o jogador no SofaScore e cole a URL aqui (ex: https://www.sofascore.com/football/player/alisson/243609)")

    url_input = st.text_input("URL do SofaScore", key="sofascore_url_input", placeholder="https://www.sofascore.com/football/player/.../12345")

    if st.button("Adicionar", disabled=not url_input or not modo_edicao):
        # Extrair ID da URL
        import re
        match = re.search(r"/(\d+)$", url_input.strip())
        if match:
            sf_id = int(match.group(1))
        elif url_input.strip().isdigit():
            sf_id = int(url_input.strip())
        else:
            st.error("URL inválida. Cole a URL da página do jogador no SofaScore.")
            sf_id = None

        if sf_id:
            with st.spinner("Buscando dados do jogador..."):
                perfil = _buscar_perfil(sf_id)
            if perfil:
                st.session_state["jogador_selecionado"] = {
                    "sofascore_id": sf_id,
                    "name": perfil.get("name", ""),
                    "team": perfil.get("team", {}).get("name", ""),
                    "team_country": perfil.get("team", {}).get("country", {}).get("name", ""),
                    "position": POSICAO_SOFASCORE_MAP.get(perfil.get("position", ""), perfil.get("position", "")),
                    "country": perfil.get("country", {}).get("name", ""),
                }
            else:
                st.error("Não foi possível buscar dados do jogador. Tente novamente.")

    if "jogador_selecionado" in st.session_state:
        _modal_adicionar(st.session_state["jogador_selecionado"])

    # --- Lista de jogadores já adicionados ---
    st.divider()
    total_geral = sum(len(jogadores.get(p, [])) for p in POSICOES_DEFAULT)
    st.subheader(f"Jogadores na Watchlist ({total_geral})")

    if total_geral == 0:
        st.info("Nenhum jogador adicionado ainda. Use a busca acima.")
        return

    for posicao in POSICOES_DEFAULT:
        lista = jogadores.get(posicao, [])
        if not lista:
            continue

        st.markdown(f"**{posicao} ({len(lista)})**")
        for j in lista:
            nascimento = j.get("nascimento")
            if nascimento:
                idade_atual, _, _ = calcular_idades(nascimento)
            else:
                idade_atual = "?"

            with st.container(border=True):
                col_foto, col_dados, col_rm = st.columns([1, 4, 1])
                with col_foto:
                    if j.get("imageUrl"):
                        st.image(j["imageUrl"], width=50)
                with col_dados:
                    pos_traduzida = traduzir_posicao(j.get("position", ""))
                    st.markdown(
                        f"**{j['name']}** | {j.get('club', 'N/A')}  \n"
                        f"{pos_traduzida} | {j.get('height', '?')} cm | {traduzir_pe(j.get('foot'))} | {formatar_valor(j.get('marketValue'))}  \n"
                        f"Idade: {idade_atual}"
                    )
                with col_rm:
                    if st.button("🗑️", key=f"rm_new_{posicao}_{j.get('sofascore_id', j.get('id'))}", disabled=not modo_edicao):
                        jogadores[posicao] = [p for p in jogadores[posicao] if p.get("sofascore_id") != j.get("sofascore_id")]
                        if not jogadores[posicao]:
                            del jogadores[posicao]
                        salvar_watchlist_new()
                        st.rerun()

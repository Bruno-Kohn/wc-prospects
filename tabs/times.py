import streamlit as st
from utils import POSICOES_DEFAULT, calcular_idades
from github_api import get_watchlist


def render(modo_edicao: bool):
    wl = get_watchlist()
    jogadores_times = wl.get("_jogadores", {})

    clubes = {}
    for pos in POSICOES_DEFAULT:
        for j in jogadores_times.get(pos, []):
            clube = j.get("club", "Sem clube") or "Sem clube"
            if clube not in clubes:
                clubes[clube] = []
            clubes[clube].append(j)

    clubes_ordenados = sorted(clubes.items(), key=lambda x: (-len(x[1]), x[0]))

    if not clubes_ordenados:
        st.info("Adicione jogadores na Watchlist para ver os times.")
        return

    for clube, jogadores_clube in clubes_ordenados:
        with st.expander(f"{clube} ({len(jogadores_clube)})"):
            for j in sorted(jogadores_clube, key=lambda x: x.get("name", "")):
                col_img, col_info = st.columns([1, 5])
                with col_img:
                    if j.get("imageUrl"):
                        st.image(j["imageUrl"], width=40)
                with col_info:
                    nasc = j.get("nascimento")
                    idade_str = ""
                    if nasc:
                        idade, _, _ = calcular_idades(nasc)
                        idade_str = f" • {idade} anos"
                    st.markdown(f"**{j['name']}**{idade_str}")

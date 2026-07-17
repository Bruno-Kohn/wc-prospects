import streamlit as st
from utils import POSICOES_DEFAULT, TOP_TEAM_LIMITES, calcular_idades, formatar_valor, traduzir_posicao, traduzir_pe
from github_api import get_watchlist


def render(modo_edicao: bool):
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

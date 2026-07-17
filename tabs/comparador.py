import streamlit as st
from utils import POSICOES_DEFAULT, calcular_idades, formatar_valor, traduzir_posicao, traduzir_pe, traduzir_pais
from github_api import get_watchlist


def render(modo_edicao: bool):
    wl = get_watchlist()
    jogadores = wl.get("_jogadores", {})

    todos_jogadores = []
    for pos in POSICOES_DEFAULT:
        for j in jogadores.get(pos, []):
            todos_jogadores.append(j)

    if len(todos_jogadores) < 2:
        st.info("Adicione pelo menos 2 jogadores na Watchlist para usar o comparador.")
        return

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

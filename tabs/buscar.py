import streamlit as st
from utils import POSICOES_DEFAULT, calcular_idades, formatar_valor, traduzir_posicao, traduzir_pe, badge, extrair_nascimento
from github_api import get_watchlist, salvar_watchlist, buscar_jogadores, buscar_perfil, buscar_clube


def exibir_card_jogador(perfil, nascimento, mostrar_salvar=True, modo_edicao=False):
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
            if st.button("💾 Salvar", use_container_width=True, key=f"save_{perfil.get('id')}", disabled=not modo_edicao):
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


def render(modo_edicao: bool):
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
            exibir_card_jogador(perfil, nascimento, mostrar_salvar=True, modo_edicao=modo_edicao)
        elif perfil and not nascimento:
            st.error("Data de nascimento indisponível.")

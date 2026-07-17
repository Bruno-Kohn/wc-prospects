import streamlit as st
import pandas as pd
from utils import POSICOES_DEFAULT, TOP_TEAM_LIMITES, calcular_idades, formatar_valor, traduzir_posicao, traduzir_pe, extrair_nascimento
from github_api import get_watchlist, salvar_watchlist, buscar_perfil, buscar_clube, buscar_historico_valor, carregar_stats_cache


def render(modo_edicao: bool):
    wl = get_watchlist()
    posicoes = wl["_ordem_posicoes"]
    jogadores = wl["_jogadores"]

    if not jogadores:
        st.info("Nenhum jogador salvo ainda. Use a aba Buscar para adicionar.")
        return

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

    if st.button("Atualizar dados", use_container_width=True, disabled=not modo_edicao):
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
                    if st.button(star_label, key=f"star_{posicao}_{j['id']}", disabled=not modo_edicao):
                        if is_top:
                            j["top_team"] = False
                            salvar_watchlist()
                            st.rerun()
                        else:
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
                    if st.button("Apagar", key=f"rm_{posicao}_{j['id']}", type="primary", disabled=not modo_edicao):
                        lista_original = jogadores.get(posicao, [])
                        jogadores[posicao] = [p for p in lista_original if p["id"] != j["id"]]
                        if not jogadores[posicao]:
                            del jogadores[posicao]
                        salvar_watchlist()
                        st.rerun()

                with st.expander("Mais detalhes", expanded=False):
                    stats_cache = carregar_stats_cache()
                    player_stats = stats_cache.get(j["id"], {})
                    metricas = player_stats.get("metricas", {})
                    if metricas:
                        st.markdown(f"**Estatísticas de carreira** ({player_stats.get('sofascore_name', '')})")
                        for label, valor in metricas.items():
                            st.caption(f"{label}: {valor}")
                    else:
                        st.caption("Estatísticas não disponíveis. Execute 'python coletar_stats.py' localmente.")

                    historico = buscar_historico_valor(j["id"])
                    if historico:
                        st.markdown("**Evolução do valor de mercado**")
                        datas = [h.get("date", "") for h in historico]
                        valores = [h.get("value", 0) for h in historico]
                        df = pd.DataFrame({"Data": datas, "Valor (€)": valores})
                        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
                        df = df.dropna(subset=["Data"]).sort_values("Data")
                        st.line_chart(df.set_index("Data")["Valor (€)"])

        if st.session_state.pop(f"top_team_full_{posicao}", False):
            limite = TOP_TEAM_LIMITES.get(posicao, 0)
            st.warning(f"Limite de {limite} jogadores para {posicao} atingido. Remova um antes de adicionar outro.")

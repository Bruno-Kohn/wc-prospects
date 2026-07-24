import streamlit as st
from utils import POSICOES_DEFAULT, calcular_idades, formatar_valor, traduzir_posicao, traduzir_pe
from github_api import get_watchlist, get_watchlist_new, salvar_watchlist_new


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
}


@st.dialog("Adicionar jogador")
def _modal_adicionar_backup(jogador_sel: dict):
    st.write(f"**{jogador_sel['name']}** — {jogador_sel.get('club', 'N/A')}")

    posicoes_disponiveis = POSICOES_DEFAULT
    pos_backup = jogador_sel.get("_pos_backup", "")
    idx_default = posicoes_disponiveis.index(pos_backup) if pos_backup in posicoes_disponiveis else 0

    grupo = st.selectbox("Posição na Watchlist", options=posicoes_disponiveis, index=idx_default)

    posicao_individual = st.text_input(
        "Posição específica (ex: Volante, Ponta Direita, Meia)",
        value=jogador_sel.get("position", ""),
    )

    col_cancel, col_confirm = st.columns(2)
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            del st.session_state["jogador_selecionado_backup"]
            st.rerun()
    with col_confirm:
        if st.button("Confirmar", use_container_width=True, type="primary"):
            # Copiar dados do backup
            jogador = {
                "id": jogador_sel.get("id", str(jogador_sel.get("sofascore_id", ""))),
                "name": jogador_sel["name"],
                "club": jogador_sel.get("club", "N/A"),
                "clubCountry": jogador_sel.get("clubCountry", ""),
                "nascimento": jogador_sel.get("nascimento", ""),
                "imageUrl": jogador_sel.get("imageUrl", ""),
                "marketValue": jogador_sel.get("marketValue"),
                "position": posicao_individual or jogador_sel.get("position", ""),
                "foot": jogador_sel.get("foot", ""),
                "height": jogador_sel.get("height"),
                "sofascore_id": jogador_sel.get("sofascore_id"),
            }
            if jogador_sel.get("top_team"):
                jogador["top_team"] = True

            wl = get_watchlist_new()
            jogadores_wl = wl["_jogadores"]
            if grupo not in jogadores_wl:
                jogadores_wl[grupo] = []

            # Verificar duplicata
            ids_existentes = [j.get("sofascore_id") for j in jogadores_wl[grupo]]
            if jogador.get("sofascore_id") in ids_existentes:
                st.error("Jogador já existe nessa posição!")
            else:
                jogadores_wl[grupo].append(jogador)
                salvar_watchlist_new()
                st.success(f"{jogador['name']} adicionado em {grupo}!")
                del st.session_state["jogador_selecionado_backup"]
                st.rerun()


def render(modo_edicao: bool):
    wl = get_watchlist_new()
    jogadores = wl["_jogadores"]

    # --- Adicionar do Backup ---
    st.subheader("Adicionar jogador")
    if not modo_edicao:
        st.info("Desbloqueie o modo edição para adicionar jogadores.")

    # Listar todos os jogadores do backup para busca
    backup = get_watchlist()
    backup_jogadores = backup.get("_jogadores", {})

    # Montar lista flat para busca
    todos_backup = []
    for pos, lista in backup_jogadores.items():
        for j in lista:
            todos_backup.append({**j, "_pos_backup": pos})

    # Campo de busca por nome
    query = st.text_input("Buscar por nome", key="busca_nome_backup", placeholder="Digite o nome do jogador...")

    if query:
        query_lower = query.lower()
        resultados = [j for j in todos_backup if query_lower in j.get("name", "").lower()]
    else:
        resultados = []

    # IDs já na nova watchlist (para marcar duplicatas)
    ids_na_nova = set()
    for pos, lista in jogadores.items():
        for j in lista:
            ids_na_nova.add(j.get("sofascore_id"))

    if query and resultados:
        st.caption(f"{len(resultados)} resultado(s)")
        for i, r in enumerate(resultados):
            ja_adicionado = r.get("sofascore_id") in ids_na_nova
            with st.container(border=True):
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    pos_traduzida = traduzir_posicao(r.get("position", ""))
                    badge = " ✅" if ja_adicionado else ""
                    st.markdown(
                        f"**{r['name']}**{badge} | {r.get('club', 'N/A')}  \n"
                        f"{pos_traduzida} | {r.get('height', '?')} cm | {formatar_valor(r.get('marketValue'))}"
                    )
                with col_btn:
                    if ja_adicionado:
                        st.caption("Já adicionado")
                    elif st.button("Adicionar", key=f"add_backup_{r.get('sofascore_id', i)}_{i}", disabled=not modo_edicao):
                        st.session_state["jogador_selecionado_backup"] = r
    elif query:
        st.warning("Nenhum jogador encontrado no backup com esse nome.")

    # Modal de adição
    if "jogador_selecionado_backup" in st.session_state:
        _modal_adicionar_backup(st.session_state["jogador_selecionado_backup"])

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

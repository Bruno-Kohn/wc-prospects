import streamlit as st

st.set_page_config(page_title="WC Prospects 2030/2034", page_icon="⚽", layout="centered")

# --- Autenticação para edição ---
if "modo_edicao" not in st.session_state:
    st.session_state["modo_edicao"] = False

with st.sidebar:
    st.subheader("Modo Edição")
    if st.session_state["modo_edicao"]:
        st.success("Edição desbloqueada")
        if st.button("Bloquear edição"):
            st.session_state["modo_edicao"] = False
            st.rerun()
    else:
        senha = st.text_input("Senha de edição", type="password")
        if st.button("Desbloquear"):
            if senha == st.secrets.get("EDIT_PASSWORD", ""):
                st.session_state["modo_edicao"] = True
                st.rerun()
            else:
                st.error("Senha incorreta")

MODO_EDICAO = st.session_state["modo_edicao"]

st.title("⚽ World Cup Prospects")
st.caption("Monitoramento de promessas para 2030 e 2034")

# CSS
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
table { width: 100%; }
thead tr th { background-color: #262730 !important; color: white !important; font-size: 0.8rem; }
tbody tr:nth-child(even) { background-color: #f0f2f6; }
tbody tr:nth-child(odd) { background-color: #ffffff; }
tbody tr td { font-size: 0.85rem; vertical-align: middle !important; }
</style>
""", unsafe_allow_html=True)

# --- Tabs ---
from tabs import watchlist, top_team, comparador, campinho_tab, times, copas

tab_watchlist, tab_topteam, tab_comparador, tab_campo, tab_times, tab_copas = st.tabs(
    ["Watchlist", "Top Team", "Comparador", "Campinho", "Times", "Copas"]
)

with tab_watchlist:
    watchlist.render(MODO_EDICAO)

with tab_topteam:
    top_team.render(MODO_EDICAO)

with tab_comparador:
    comparador.render(MODO_EDICAO)

with tab_campo:
    campinho_tab.render(MODO_EDICAO)

with tab_times:
    times.render(MODO_EDICAO)

with tab_copas:
    copas.render(MODO_EDICAO)

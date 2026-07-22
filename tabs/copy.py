import streamlit as st
from utils import POSICOES_DEFAULT, calcular_idades
from github_api import get_watchlist


def render(modo_edicao: bool):
    st.subheader("📋 Copiar Watchlist")
    st.caption("Lista formatada com idade em 2030 — clique para copiar")

    wl = get_watchlist()
    jogadores = wl.get("_jogadores", {})

    linhas = []
    for posicao in POSICOES_DEFAULT:
        lista = jogadores.get(posicao, [])
        if not lista:
            continue
        nomes = []
        for j in lista:
            nasc = j.get("nascimento")
            if nasc:
                _, idade_2030, _ = calcular_idades(nasc)
                nomes.append(f"{j['name']} - {j.get('club', 'N/A')} ({idade_2030})")
            else:
                nomes.append(f"{j['name']} - {j.get('club', 'N/A')}")
        linhas.append(f"{posicao}: {', '.join(nomes)}")

    texto = "\n".join(linhas)

    st.code(texto, language=None)

    st.button("📋 Copiar", on_click=lambda: st.session_state.update({"_copy_text": texto}), use_container_width=True)
    if "_copy_text" in st.session_state:
        st.components.v1.html(
            f"""<textarea id="copyarea" style="position:absolute;left:-9999px">{st.session_state['_copy_text']}</textarea>
            <script>
            var t=document.getElementById('copyarea');t.select();document.execCommand('copy');
            </script>""",
            height=0,
        )
        del st.session_state["_copy_text"]
        st.success("Copiado!")

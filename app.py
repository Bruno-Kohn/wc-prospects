import streamlit as st
import requests
import re
from datetime import date

st.set_page_config(page_title="WC Prospects 2030/2034", page_icon="⚽", layout="centered")

st.title("⚽ World Cup Prospects")
st.caption("Monitoramento de promessas para 2030 e 2034")

BASE_URL = "https://transfermarkt-api.fly.dev"


@st.cache_data(ttl=3600)
def buscar_jogadores(nome: str) -> list:
    try:
        resp = requests.get(f"{BASE_URL}/players/search/{nome}", timeout=10)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {e}")
        return []


@st.cache_data(ttl=3600)
def buscar_perfil(player_id: str) -> dict | None:
    try:
        resp = requests.get(f"{BASE_URL}/players/{player_id}/profile", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {e}")
        return None


def extrair_nascimento(description: str) -> str | None:
    match = re.search(r"\*\s*(\d{2}/\d{2}/\d{4})", description or "")
    if match:
        parts = match.group(1).split("/")
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return None


def calcular_idades(data_nascimento: str):
    ano_nasc = int(data_nascimento.split("-")[0])
    mes_nasc = int(data_nascimento.split("-")[1])
    dia_nasc = int(data_nascimento.split("-")[2])
    hoje = date.today()
    idade_atual = hoje.year - ano_nasc - ((hoje.month, hoje.day) < (mes_nasc, dia_nasc))
    return idade_atual, 2030 - ano_nasc, 2034 - ano_nasc


def badge(idade: int) -> str:
    if idade < 24:
        return "👶 Promessa Jovem"
    elif 24 <= idade <= 29:
        return "🔥 Auge Físico/Técnico!"
    else:
        return "👴 Fase de Transição/Veterano"


def formatar_valor(valor):
    if not valor:
        return "N/A"
    if valor >= 1_000_000:
        return f"€{valor / 1_000_000:.0f}M"
    if valor >= 1_000:
        return f"€{valor / 1_000:.0f}K"
    return f"€{valor}"


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
            opcoes = {
                f"{r['name']} ({r.get('club', {}).get('name', 'N/A')})": r
                for r in resultados
            }
            escolha = st.selectbox("Selecione o jogador", options=list(opcoes.keys()))
            jogador = opcoes[escolha]

            with st.spinner("Carregando perfil..."):
                perfil = buscar_perfil(jogador["id"])

            if not perfil:
                st.error("Não foi possível carregar o perfil.")
            else:
                nascimento = extrair_nascimento(perfil.get("description"))

                if not nascimento:
                    st.error("Data de nascimento indisponível.")
                else:
                    idade_atual, idade_2030, idade_2034 = calcular_idades(nascimento)

                    st.divider()

                    col_foto, col_info = st.columns([1, 2])
                    with col_foto:
                        img = perfil.get("imageUrl")
                        if img:
                            st.image(img, width=100)
                    with col_info:
                        st.subheader(perfil.get("fullName") or perfil.get("name"))
                        clube = perfil.get("club", {})
                        st.write(f"**Clube:** {clube.get('name', 'N/A')}")
                        st.write(f"**Idade atual:** {idade_atual} anos")
                        st.write(f"**Altura:** {perfil.get('height', 'N/A')} cm")
                        st.write(f"**Posição:** {perfil.get('position', {}).get('main', 'N/A')}")
                        st.write(f"**Pé:** {perfil.get('foot', 'N/A')}")
                        st.write(f"**Valor de mercado:** {formatar_valor(perfil.get('marketValue'))}")
                        st.write(f"**Nascimento:** {nascimento}")

                    st.divider()

                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("Copa 2030 🏆", f"{idade_2030} anos")
                        st.info(badge(idade_2030))
                    with c2:
                        st.metric("Copa 2034 🏆", f"{idade_2034} anos")
                        st.info(badge(idade_2034))

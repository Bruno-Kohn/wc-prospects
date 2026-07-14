import streamlit as st
import requests
from datetime import date

st.set_page_config(page_title="WC Prospects 2030/2034", page_icon="⚽", layout="centered")

st.title("⚽ World Cup Brazilian Prospects")
st.caption("Monitoramento de promessas para 2030 e 2034")


LIGAS = {
    "Premier League - England": 39,
    "Championship - England": 40,
    "La Liga - Spain": 140,
    "La Liga 2 - Spain": 141,
    "Serie A - Italy": 135,
    "Serie B - Italy": 136,
    "Bundesliga - Germany": 78,
    "2. Bundesliga - Germany": 79,
    "Ligue 1 - France": 61,
    "Brasileirão Série A - Brazil": 71,
    "Brasileirão Série B - Brazil": 72,
    "Liga Portugal - Portugal": 94,
    "Eredivisie - Netherlands": 88,
    "Primera División - Argentina": 128,
    "Belgian Pro League - Belgium": 144,
    "Scottish Premiership - Scotland": 179,
    "MLS - USA": 253,
    "Liga MX - Mexico": 262,
    "J1 League - Japan": 98,
    "K League 1 - South Korea": 292,
    "Saudi Pro League - Saudi Arabia": 307,
    "UAE Pro League - UAE": 320,
    "Qatar Stars League - Qatar": 305,
    "Super Lig - Turkey": 203,
    "Russian Premier League - Russia": 235,
    "Superliga - Denmark": 119,
    "Allsvenskan - Sweden": 113,
    "Eliteserien - Norway": 103,
    "Super League - Switzerland": 207,
    "Bundesliga - Austria": 218,
    "Ekstraklasa - Poland": 106,
    "Primera División - Uruguay": 268,
    "Liga Colombiana - Colombia": 239,
    "Copa Libertadores - South America": 13,
    "UEFA Champions League - Europe": 2,
    "UEFA Europa League - Europe": 3,
}


@st.cache_data(ttl=3600)
def buscar_jogador(nome: str, league_id: int) -> dict | None:
    url = "https://v3.football.api-sports.io/players"
    headers = {
        "x-apisports-key": st.secrets["API_KEY"],
    }
    season = date.today().year if date.today().month >= 8 else date.today().year - 1
    params = {"search": nome, "league": league_id, "season": season}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("response", [])
        if results:
            return results[0]
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão com a API: {e}")
        return None


def calcular_idades(data_nascimento: str):
    ano_nasc = int(data_nascimento.split("-")[0])
    hoje = date.today()
    idade_atual = hoje.year - ano_nasc - (
        (hoje.month, hoje.day) < (int(data_nascimento.split("-")[1]), int(data_nascimento.split("-")[2]))
    )
    return idade_atual, 2030 - ano_nasc, 2034 - ano_nasc


def badge(idade: int) -> str:
    if idade < 24:
        return "👶 Promessa Jovem"
    elif 24 <= idade <= 29:
        return "🔥 Auge Físico/Técnico!"
    else:
        return "👴 Fase de Transição/Veterano"


nome = st.text_input("Nome do jogador", placeholder="Ex: Lamine Yamal")
liga_nome = st.selectbox("Liga", options=list(LIGAS.keys()))

if st.button("Buscar", use_container_width=True):
    if not nome.strip():
        st.warning("Digite o nome de um jogador.")
    else:
        with st.spinner("Buscando dados em tempo real..."):
            resultado = buscar_jogador(nome.strip(), LIGAS[liga_nome])

        if resultado is None:
            st.warning("Nenhum jogador encontrado. Tente outro nome.")
        else:
            player = resultado["player"]
            stats = resultado["statistics"][0] if resultado.get("statistics") else {}

            nome_completo = player.get("name", "N/A")
            nascimento = player.get("birth", {}).get("date")
            altura = player.get("height", "N/A")
            foto = player.get("photo")
            clube = stats.get("team", {}).get("name", "N/A") if stats else "N/A"
            logo_clube = stats.get("team", {}).get("logo") if stats else None

            if not nascimento:
                st.error("Data de nascimento indisponível para este jogador.")
            else:
                idade_atual, idade_2030, idade_2034 = calcular_idades(nascimento)

                st.divider()

                col_foto, col_info = st.columns([1, 2])
                with col_foto:
                    if foto:
                        st.image(foto, width=100)
                with col_info:
                    st.subheader(nome_completo)
                    st.write(f"**Clube:** {clube}")
                    st.write(f"**Idade atual:** {idade_atual} anos")
                    st.write(f"**Altura:** {altura}")
                    st.write(f"**Nascimento:** {nascimento}")

                st.divider()

                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Copa 2030 🏆", f"{idade_2030} anos")
                    st.info(badge(idade_2030))
                with c2:
                    st.metric("Copa 2034 🏆", f"{idade_2034} anos")
                    st.info(badge(idade_2034))

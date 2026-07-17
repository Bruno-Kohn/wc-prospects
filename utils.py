import re
import pandas as pd
from datetime import date


POSICOES_DEFAULT = [
    "Goleiros",
    "Zagueiros",
    "Laterais Esquerdos",
    "Laterais Direitos",
    "Volantes",
    "Meias",
    "Pontas Esquerdas",
    "Pontas Direitas",
    "Atacantes",
]

TOP_TEAM_LIMITES = {
    "Goleiros": 3,
    "Zagueiros": 4,
    "Laterais Esquerdos": 2,
    "Laterais Direitos": 2,
    "Volantes": 4,
    "Meias": 4,
    "Pontas Esquerdas": 2,
    "Pontas Direitas": 2,
    "Atacantes": 3,
}

BASE_URL = "https://transfermarkt-api.fly.dev"
GITHUB_REPO = "Bruno-Kohn/wc-prospects"
WATCHLIST_PATH = "watchlist.json"

POSICAO_MAP = {
    "Centre-Forward": "Centroavante",
    "Second Striker": "Segundo Atacante",
    "Left Winger": "Ponta Esquerda",
    "Right Winger": "Ponta Direita",
    "Attacking Midfield": "Meia Atacante",
    "Central Midfield": "Volante",
    "Defensive Midfield": "Volante",
    "Left Midfield": "Meia Esquerda",
    "Right Midfield": "Meia Direita",
    "Left-Back": "Lateral Esquerdo",
    "Right-Back": "Lateral Direito",
    "Centre-Back": "Zagueiro",
    "Goalkeeper": "Goleiro",
}

PAIS_MAP = {
    "Spain": "Espanha",
    "England": "Inglaterra",
    "Germany": "Alemanha",
    "Italy": "Itália",
    "France": "França",
    "Brazil": "Brasil",
    "Portugal": "Portugal",
    "Netherlands": "Holanda",
    "Argentina": "Argentina",
    "Belgium": "Bélgica",
    "Scotland": "Escócia",
    "United States": "Estados Unidos",
    "Mexico": "México",
    "Japan": "Japão",
    "South Korea": "Coreia do Sul",
    "Saudi Arabia": "Arábia Saudita",
    "United Arab Emirates": "Emirados Árabes",
    "Qatar": "Catar",
    "Turkey": "Turquia",
    "Russia": "Rússia",
    "Denmark": "Dinamarca",
    "Sweden": "Suécia",
    "Norway": "Noruega",
    "Switzerland": "Suíça",
    "Austria": "Áustria",
    "Poland": "Polônia",
    "Uruguay": "Uruguai",
    "Colombia": "Colômbia",
    "Greece": "Grécia",
    "Croatia": "Croácia",
    "Serbia": "Sérvia",
    "Czech Republic": "República Tcheca",
    "Romania": "Romênia",
    "Ukraine": "Ucrânia",
    "China": "China",
    "Australia": "Austrália",
}


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
    if valor >= 1_000_000_000:
        return f"€ {valor / 1_000_000_000:.2f} B"
    if valor >= 1_000_000:
        return f"€ {valor / 1_000_000:.0f} M"
    if valor >= 1_000:
        return f"€ {valor / 1_000:.0f} K"
    return f"€ {valor}"


def traduzir_posicao(pos: str) -> str:
    return POSICAO_MAP.get(pos, pos)


def traduzir_pais(pais: str) -> str:
    return PAIS_MAP.get(pais, pais)


def traduzir_pe(foot: str) -> str:
    foot_map = {"left": "Canhoto", "right": "Destro", "both": "Ambidestro"}
    return foot_map.get((foot or "").lower(), foot or "N/A")

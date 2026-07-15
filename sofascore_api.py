"""
Módulo de integração com a API do SofaScore.
Busca estatísticas de carreira de jogadores via API interna.
"""

import requests
from datetime import datetime

SOFASCORE_BASE = "https://www.sofascore.com/api/v1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Cache-Control": "no-cache",
}


def _buscar_perfil_sofascore(player_id: int) -> dict | None:
    """Busca perfil individual do jogador no SofaScore (com altura e nascimento)."""
    try:
        resp = requests.get(
            f"{SOFASCORE_BASE}/player/{player_id}",
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("player", {})
    except Exception:
        return None


def _validar_candidato_por_perfil(candidato: dict, nascimento: str = "", altura: int = 0) -> bool:
    """
    Valida um candidato buscando seu perfil e comparando nascimento/altura.
    Retorna True se os dados batem.
    """
    if not nascimento and not altura:
        return True  # Sem dados para validar

    perfil = _buscar_perfil_sofascore(candidato["id"])
    if not perfil:
        return True  # Não conseguiu buscar, aceita

    # Validar data de nascimento
    if nascimento and perfil.get("dateOfBirthTimestamp"):
        try:
            dob_sofascore = datetime.fromtimestamp(perfil["dateOfBirthTimestamp"]).strftime("%Y-%m-%d")
            # Comparar apenas o ano (tolerância)
            ano_wl = int(nascimento.split("-")[0])
            ano_ss = int(dob_sofascore.split("-")[0])
            if abs(ano_wl - ano_ss) > 1:
                return False
        except Exception:
            pass

    # Validar altura (tolerância de 3cm)
    if altura and perfil.get("height"):
        if abs(altura - perfil["height"]) > 3:
            return False

    return True


def _buscar_candidatos(query: str) -> list[dict]:
    """Busca todos os candidatos de futebol para uma query."""
    try:
        resp = requests.get(
            f"{SOFASCORE_BASE}/search/all",
            params={"q": query, "type": "player"},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        candidatos = []
        for r in results:
            entity = r.get("entity", {})
            team = entity.get("team", {})
            sport = team.get("sport", {})
            if sport.get("slug") == "football" and r.get("type") == "player":
                candidatos.append({
                    "id": entity["id"],
                    "name": entity.get("name", ""),
                    "team": team.get("name", ""),
                    "position": entity.get("position", ""),
                    "country": entity.get("country", {}).get("name", ""),
                })
        return candidatos
    except Exception:
        return []


def _nome_similar(nome_busca: str, nome_encontrado: str) -> bool:
    """Verifica se o nome encontrado é compatível com o nome buscado."""
    busca_lower = nome_busca.lower()
    encontrado_lower = nome_encontrado.lower()
    # Match exato ou contém
    if encontrado_lower in busca_lower or busca_lower in encontrado_lower:
        return True
    # Alguma parte significativa do nome buscado está no encontrado
    palavras_ignorar = {"de", "da", "do", "dos", "das", "e", "junior", "filho", "neto",
                        "silva", "santos", "oliveira", "souza", "sousa", "lima", "costa",
                        "ferreira", "pereira", "almeida", "rodrigues", "carvalho", "dias"}
    partes_busca = busca_lower.split()
    partes_encontrado = encontrado_lower.split()
    partes_busca_sig = [p for p in partes_busca if p not in palavras_ignorar and len(p) > 3]
    partes_encontrado_sig = [p for p in partes_encontrado if p not in palavras_ignorar and len(p) > 3]
    if not partes_busca_sig:
        return False
    matches = sum(1 for p in partes_busca_sig if any(p in e or e in p for e in partes_encontrado_sig))
    # Precisa de pelo menos 1 match em palavras significativas
    return matches >= 1


def _pontuar_candidato(candidato: dict, nome_busca: str, clube: str = "", country: str = "Brazil") -> int:
    """Pontua um candidato por compatibilidade. Maior = melhor."""
    pontos = 0
    nome_candidato = candidato.get("name", "")

    # Nome similar (+5)
    if _nome_similar(nome_busca, nome_candidato):
        pontos += 5

    # País correto (+10)
    if candidato.get("country") == country:
        pontos += 10

    # Clube bate (+20)
    if clube and candidato.get("team"):
        if _clube_compativel(clube, candidato["team"]):
            pontos += 20

    return pontos


def _clube_compativel(clube_watchlist: str, clube_sofascore: str) -> bool:
    """Verifica se dois nomes de clube se referem ao mesmo time."""
    a = clube_watchlist.lower().strip()
    b = clube_sofascore.lower().strip()

    # Match direto
    if a in b or b in a:
        return True

    # Remover sufixos comuns
    sufixos = [" fc", " cf", "fc ", "cf ", " sc", " ec", " fr"]
    a_clean = a
    b_clean = b
    for s in sufixos:
        a_clean = a_clean.replace(s, "").strip()
        b_clean = b_clean.replace(s, "").strip()

    if a_clean in b_clean or b_clean in a_clean:
        return True

    # Aliases conhecidos
    ALIASES = {
        "psg": ["paris saint-germain", "paris saint germain", "paris sg"],
        "paris saint-germain": ["psg", "paris sg"],
        "real madrid": ["real madrid cf"],
        "barcelona": ["fc barcelona", "barça"],
        "nottingham forest": ["nottm forest", "nott'm forest"],
        "wolverhampton": ["wolverhampton wanderers", "wolves"],
        "tottenham": ["tottenham hotspur", "spurs"],
        "manchester united": ["man united", "man utd"],
        "manchester city": ["man city"],
        "newcastle united": ["newcastle"],
        "atletico madrid": ["atlético madrid", "atlético de madrid", "atl. madrid"],
        "botafogo": ["botafogo fr", "botafogo de futebol e regatas"],
        "flamengo": ["cr flamengo", "clube de regatas do flamengo"],
        "palmeiras": ["se palmeiras", "sociedade esportiva palmeiras"],
        "corinthians": ["sc corinthians", "sport club corinthians paulista"],
        "são paulo": ["são paulo fc", "spfc"],
        "santos": ["santos fc"],
        "fluminense": ["fluminense fc"],
        "vasco": ["vasco da gama", "cr vasco da gama"],
        "grêmio": ["grêmio fbpa"],
        "internacional": ["sc internacional", "sport club internacional"],
        "atlético mineiro": ["atlético-mg", "atletico mineiro", "clube atlético mineiro"],
        "cruzeiro": ["cruzeiro ec"],
        "inter milan": ["internazionale", "inter"],
        "ac milan": ["milan"],
        "juventus": ["juventus fc"],
        "lyon": ["olympique lyonnais", "olympique lyon"],
        "marseille": ["olympique de marseille", "olympique marseille", "om"],
        "monaco": ["as monaco"],
        "dortmund": ["borussia dortmund", "bvb"],
        "bayern munich": ["fc bayern münchen", "bayern münchen", "bayern"],
        "leverkusen": ["bayer leverkusen", "bayer 04 leverkusen"],
        "brighton": ["brighton & hove albion", "brighton and hove albion"],
        "west ham": ["west ham united"],
        "leicester": ["leicester city"],
        "aston villa": ["aston villa fc"],
        "fulham": ["fulham fc"],
        "stade reims": ["reims", "stade de reims"],
        "espanyol": ["rcd espanyol"],
        "betis": ["real betis", "real betis balompié"],
    }

    for key, aliases in ALIASES.items():
        all_names = [key] + aliases
        a_match = any(n in a or a in n for n in all_names)
        b_match = any(n in b or b in n for n in all_names)
        if a_match and b_match:
            return True

    # Comparar palavras significativas (ignorar artigos)
    ignorar = {"de", "da", "do", "fc", "sc", "ec", "cf", "fr", "cr", "se", "the"}
    palavras_a = {p for p in a.split() if p not in ignorar and len(p) > 2}
    palavras_b = {p for p in b.split() if p not in ignorar and len(p) > 2}
    if palavras_a and palavras_b:
        comum = palavras_a & palavras_b
        if len(comum) >= 1 and len(max(comum, key=len)) >= 4:
            return True

    return False


def buscar_id_sofascore(nome: str, clube: str = "", nascimento: str = "", altura: int = 0) -> dict | None:
    """
    Busca um jogador pelo nome no SofaScore.
    Usa nome + clube + nascimento + altura para desambiguação.
    Só retorna se tiver confiança razoável.
    """
    partes = nome.split()
    todas_queries = []

    # 1. Combinações de duas palavras consecutivas
    if len(partes) >= 2:
        for i in range(len(partes) - 1):
            combo = f"{partes[i]} {partes[i+1]}"
            if len(combo) > 5:
                todas_queries.append(combo)

    # 2. Primeiro nome
    if partes:
        todas_queries.append(partes[0])

    # 3. Partes com mais de 4 letras
    for parte in partes[1:]:
        if len(parte) > 4 and parte not in todas_queries:
            todas_queries.append(parte)

    melhor = None
    melhor_pontos = -1

    for query in todas_queries:
        candidatos = _buscar_candidatos(query)
        for c in candidatos:
            pontos = _pontuar_candidato(c, nome, clube)
            if pontos > melhor_pontos:
                melhor_pontos = pontos
                melhor = c
            # Match perfeito (nome + país + clube): valida e retorna
            if pontos >= 35:
                if _validar_candidato_por_perfil(melhor, nascimento, altura):
                    return melhor

    # Aceitar apenas se tiver confiança alta + validação por perfil
    if melhor and melhor_pontos >= 20:
        if _validar_candidato_por_perfil(melhor, nascimento, altura):
            return melhor
    if melhor and melhor_pontos >= 15 and _nome_similar(nome, melhor.get("name", "")):
        if _validar_candidato_por_perfil(melhor, nascimento, altura):
            return melhor
        return melhor

    return None


def buscar_temporadas(player_id: int) -> list[dict]:
    """
    Retorna lista de temporadas disponíveis para o jogador.
    Cada item: {'tournament_id', 'tournament_name', 'season_id', 'season_name'}
    """
    try:
        resp = requests.get(
            f"{SOFASCORE_BASE}/player/{player_id}/statistics/seasons",
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        temporadas = []
        for t in data.get("uniqueTournamentSeasons", []):
            ut = t["uniqueTournament"]
            # Apenas futebol
            cat = ut.get("category", {})
            sport = cat.get("sport", {})
            if sport.get("slug") != "football":
                continue
            for s in t.get("seasons", []):
                temporadas.append({
                    "tournament_id": ut["id"],
                    "tournament_name": ut.get("name", ""),
                    "season_id": s["id"],
                    "season_name": s.get("name", ""),
                })
        return temporadas
    except Exception:
        return []


def buscar_stats_temporada(player_id: int, tournament_id: int, season_id: int) -> dict:
    """
    Busca estatísticas gerais de um jogador em uma temporada específica.
    Retorna o dict de 'statistics' do SofaScore.
    """
    try:
        resp = requests.get(
            f"{SOFASCORE_BASE}/player/{player_id}/unique-tournament/{tournament_id}/season/{season_id}/statistics/overall",
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("statistics", {})
    except Exception:
        return {}


# --- Formatação de stats por posição ---

def stats_relevantes_atacante(stats: dict) -> dict:
    """Stats relevantes para atacantes/centroavantes."""
    minutos = stats.get("minutesPlayed", 0)
    gols = stats.get("goals", 0)
    return {
        "Gols": gols,
        "Assistências": stats.get("assists", 0),
        "Minutos jogados": minutos,
        "Gols/90min": round(gols / (minutos / 90), 2) if minutos > 0 else 0,
        "Finalizações no gol": stats.get("shotsOnTarget", 0),
        "Finalizações total": stats.get("totalShots", 0),
        "Conversão de gols (%)": round(stats.get("goalConversionPercentage", 0), 1),
        "Grandes chances perdidas": stats.get("bigChancesMissed", 0),
        "Dribles certos": stats.get("successfulDribbles", 0),
        "Duelos aéreos ganhos": stats.get("aerialDuelsWon", 0),
        "Impedimentos": stats.get("offsides", 0),
        "Nota média": round(stats.get("rating", 0), 2),
    }


def stats_relevantes_meia(stats: dict) -> dict:
    """Stats relevantes para meias/armadores."""
    minutos = stats.get("minutesPlayed", 0)
    return {
        "Gols": stats.get("goals", 0),
        "Assistências": stats.get("assists", 0),
        "Minutos jogados": minutos,
        "Passes certos": stats.get("accuratePasses", 0),
        "Precisão de passes (%)": round(stats.get("accuratePassesPercentage", 0), 1),
        "Passes decisivos": stats.get("keyPasses", 0),
        "Grandes chances criadas": stats.get("bigChancesCreated", 0),
        "Dribles certos": stats.get("successfulDribbles", 0),
        "Finalizações no gol": stats.get("shotsOnTarget", 0),
        "Nota média": round(stats.get("rating", 0), 2),
    }


def stats_relevantes_ponta(stats: dict) -> dict:
    """Stats relevantes para pontas."""
    minutos = stats.get("minutesPlayed", 0)
    gols = stats.get("goals", 0)
    return {
        "Gols": gols,
        "Assistências": stats.get("assists", 0),
        "Minutos jogados": minutos,
        "Gols/90min": round(gols / (minutos / 90), 2) if minutos > 0 else 0,
        "Dribles certos": stats.get("successfulDribbles", 0),
        "Dribles (%)": round(stats.get("successfulDribblesPercentage", 0), 1),
        "Grandes chances criadas": stats.get("bigChancesCreated", 0),
        "Passes decisivos": stats.get("keyPasses", 0),
        "Finalizações no gol": stats.get("shotsOnTarget", 0),
        "Nota média": round(stats.get("rating", 0), 2),
    }


def stats_relevantes_volante(stats: dict) -> dict:
    """Stats relevantes para volantes."""
    minutos = stats.get("minutesPlayed", 0)
    return {
        "Desarmes": stats.get("tackles", 0),
        "Interceptações": stats.get("interceptions", 0),
        "Minutos jogados": minutos,
        "Passes certos": stats.get("accuratePasses", 0),
        "Precisão de passes (%)": round(stats.get("accuratePassesPercentage", 0), 1),
        "Duelos ganhos": stats.get("totalDuelsWon", 0),
        "Duelos ganhos (%)": round(stats.get("totalDuelsWonPercentage", 0), 1),
        "Gols": stats.get("goals", 0),
        "Assistências": stats.get("assists", 0),
        "Cartões amarelos": stats.get("yellowCards", 0),
        "Nota média": round(stats.get("rating", 0), 2),
    }


def stats_relevantes_zagueiro(stats: dict) -> dict:
    """Stats relevantes para zagueiros."""
    minutos = stats.get("minutesPlayed", 0)
    return {
        "Desarmes": stats.get("tackles", 0),
        "Interceptações": stats.get("interceptions", 0),
        "Cortes": stats.get("clearances", 0),
        "Minutos jogados": minutos,
        "Duelos aéreos ganhos": stats.get("aerialDuelsWon", 0),
        "Duelos aéreos (%)": round(stats.get("aerialDuelsWonPercentage", 0), 1),
        "Passes certos": stats.get("accuratePasses", 0),
        "Precisão de passes (%)": round(stats.get("accuratePassesPercentage", 0), 1),
        "Clean sheets": stats.get("cleanSheet", 0),
        "Erros para gol": stats.get("errorLeadToGoal", 0),
        "Gols": stats.get("goals", 0),
        "Nota média": round(stats.get("rating", 0), 2),
    }


def stats_relevantes_lateral(stats: dict) -> dict:
    """Stats relevantes para laterais."""
    minutos = stats.get("minutesPlayed", 0)
    return {
        "Assistências": stats.get("assists", 0),
        "Passes decisivos": stats.get("keyPasses", 0),
        "Cruzamentos certos": stats.get("accurateCrosses", 0),
        "Minutos jogados": minutos,
        "Desarmes": stats.get("tackles", 0),
        "Interceptações": stats.get("interceptions", 0),
        "Dribles certos": stats.get("successfulDribbles", 0),
        "Duelos ganhos (%)": round(stats.get("totalDuelsWonPercentage", 0), 1),
        "Gols": stats.get("goals", 0),
        "Nota média": round(stats.get("rating", 0), 2),
    }


def stats_relevantes_goleiro(stats: dict) -> dict:
    """Stats relevantes para goleiros."""
    minutos = stats.get("minutesPlayed", 0)
    return {
        "Defesas": stats.get("saves", 0),
        "Clean sheets": stats.get("cleanSheet", 0),
        "Gols sofridos": stats.get("goalsConcededInsideTheBox", 0) + stats.get("goalsConcededOutsideTheBox", 0),
        "Minutos jogados": minutos,
        "Pênaltis defendidos": stats.get("penaltySave", 0),
        "Defesas dentro da área": stats.get("savedShotsFromInsideTheBox", 0),
        "Saídas do gol": stats.get("runsOut", 0),
        "Passes certos": stats.get("accuratePasses", 0),
        "Nota média": round(stats.get("rating", 0), 2),
    }


# Mapeamento posição SofaScore → função de stats
POSICAO_STATS_MAP = {
    "F": stats_relevantes_atacante,  # Forward
    "M": stats_relevantes_meia,      # Midfielder
    "D": stats_relevantes_zagueiro,  # Defender
    "G": stats_relevantes_goleiro,   # Goalkeeper
}

# Mapeamento posição Transfermarkt → função de stats
POSICAO_TM_STATS_MAP = {
    "Centre-Forward": stats_relevantes_atacante,
    "Second Striker": stats_relevantes_atacante,
    "Left Winger": stats_relevantes_ponta,
    "Right Winger": stats_relevantes_ponta,
    "Attacking Midfield": stats_relevantes_meia,
    "Central Midfield": stats_relevantes_volante,
    "Defensive Midfield": stats_relevantes_volante,
    "Left Midfield": stats_relevantes_meia,
    "Right Midfield": stats_relevantes_meia,
    "Left-Back": stats_relevantes_lateral,
    "Right-Back": stats_relevantes_lateral,
    "Centre-Back": stats_relevantes_zagueiro,
    "Goalkeeper": stats_relevantes_goleiro,
}


def get_stats_por_posicao(posicao_tm: str, stats: dict) -> dict:
    """Retorna stats formatadas de acordo com a posição do Transfermarkt."""
    func = POSICAO_TM_STATS_MAP.get(posicao_tm, stats_relevantes_atacante)
    return func(stats)

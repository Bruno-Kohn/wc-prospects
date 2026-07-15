"""
Módulo de integração com a API do SofaScore.
Busca estatísticas de carreira de jogadores via API interna.
"""

import requests

SOFASCORE_BASE = "https://www.sofascore.com/api/v1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Cache-Control": "no-cache",
}


def _buscar_player_sofascore(query: str) -> dict | None:
    """Busca interna por query exata."""
    try:
        resp = requests.get(
            f"{SOFASCORE_BASE}/search/all",
            params={"q": query, "type": "player"},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        for r in results:
            entity = r.get("entity", {})
            team = entity.get("team", {})
            sport = team.get("sport", {})
            if sport.get("slug") == "football" and r.get("type") == "player":
                return {
                    "id": entity["id"],
                    "name": entity.get("name", ""),
                    "team": team.get("name", ""),
                    "position": entity.get("position", ""),
                    "country": entity.get("country", {}).get("name", ""),
                }
        return None
    except Exception as e:
        # Retornar erro para debug no app
        return {"error": str(e)}


def buscar_id_sofascore(nome: str) -> dict | None:
    """
    Busca um jogador pelo nome no SofaScore.
    Tenta variações: primeiro nome, cada parte do nome, nome completo.
    """
    partes = nome.split()

    # Tentar primeiro nome (mais comum para brasileiros: Endrick, Vinicius, etc)
    if partes:
        result = _buscar_player_sofascore(partes[0])
        if result:
            return result

    # Tentar cada parte do nome individualmente
    for parte in partes[1:]:
        if len(parte) > 3:  # Ignorar "de", "da", "dos"
            result = _buscar_player_sofascore(parte)
            if result:
                return result

    # Tentar nome completo
    result = _buscar_player_sofascore(nome)
    if result:
        return result

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

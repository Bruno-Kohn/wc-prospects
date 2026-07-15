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


# --- Métricas de carreira por posição (consolidado por 90 min) ---

def _p90(valor, minutos):
    """Calcula métrica por 90 minutos."""
    if not minutos or minutos == 0:
        return 0.0
    return round(valor / (minutos / 90), 2)


def _pct(parte, total):
    """Calcula porcentagem."""
    if not total or total == 0:
        return 0.0
    return round((parte / total) * 100, 1)


def metricas_carreira_goleiro(stats: dict) -> dict:
    """Métricas de carreira para goleiros."""
    minutos = stats.get("minutesPlayed", 0)
    jogos = round(minutos / 90, 1) if minutos > 0 else 0
    defesas = stats.get("saves", 0)
    clean_sheets = stats.get("cleanSheet", 0)
    gols_sofridos = stats.get("goalsConcededInsideTheBox", 0) + stats.get("goalsConcededOutsideTheBox", 0)
    total_jogos_aprox = stats.get("countRating", 0) or jogos

    return {
        "Jogos na carreira": int(total_jogos_aprox),
        "Minutos jogados": minutos,
        "Defesas/90min": _p90(defesas, minutos),
        "Clean sheets (%)": _pct(clean_sheets, total_jogos_aprox) if total_jogos_aprox else 0,
        "Pênaltis defendidos": stats.get("penaltySave", 0),
        "Defesas dentro da área/90min": _p90(stats.get("savedShotsFromInsideTheBox", 0), minutos),
        "Saídas do gol/90min": _p90(stats.get("runsOut", 0), minutos),
        "Passes certos/90min": _p90(stats.get("accuratePasses", 0), minutos),
        "Gols sofridos/90min": _p90(gols_sofridos, minutos),
        "Nota média": round(stats.get("rating", 0) / stats.get("countRating", 1), 2) if stats.get("countRating") else 0,
    }


def metricas_carreira_zagueiro(stats: dict) -> dict:
    """Métricas de carreira para zagueiros."""
    minutos = stats.get("minutesPlayed", 0)
    total_jogos = stats.get("countRating", 0) or round(minutos / 90, 1)

    return {
        "Jogos na carreira": int(total_jogos),
        "Minutos jogados": minutos,
        "Desarmes/90min": _p90(stats.get("tackles", 0), minutos),
        "Interceptações/90min": _p90(stats.get("interceptions", 0), minutos),
        "Cortes/90min": _p90(stats.get("clearances", 0), minutos),
        "Duelos aéreos ganhos/90min": _p90(stats.get("aerialDuelsWon", 0), minutos),
        "Duelos aéreos (%)": _pct(stats.get("aerialDuelsWon", 0), stats.get("aerialDuelsWon", 0) + stats.get("aerialDuelsLost", 0)),
        "Passes certos/90min": _p90(stats.get("accuratePasses", 0), minutos),
        "Gols": stats.get("goals", 0),
        "Erros para gol": stats.get("errorLeadToGoal", 0),
        "Nota média": round(stats.get("rating", 0) / stats.get("countRating", 1), 2) if stats.get("countRating") else 0,
    }


def metricas_carreira_lateral(stats: dict) -> dict:
    """Métricas de carreira para laterais."""
    minutos = stats.get("minutesPlayed", 0)
    total_jogos = stats.get("countRating", 0) or round(minutos / 90, 1)

    return {
        "Jogos na carreira": int(total_jogos),
        "Minutos jogados": minutos,
        "Assistências/90min": _p90(stats.get("assists", 0), minutos),
        "Passes decisivos/90min": _p90(stats.get("keyPasses", 0), minutos),
        "Cruzamentos certos/90min": _p90(stats.get("accurateCrosses", 0), minutos),
        "Desarmes/90min": _p90(stats.get("tackles", 0), minutos),
        "Interceptações/90min": _p90(stats.get("interceptions", 0), minutos),
        "Dribles certos/90min": _p90(stats.get("successfulDribbles", 0), minutos),
        "Gols": stats.get("goals", 0),
        "Assistências": stats.get("assists", 0),
        "Nota média": round(stats.get("rating", 0) / stats.get("countRating", 1), 2) if stats.get("countRating") else 0,
    }


def metricas_carreira_volante(stats: dict) -> dict:
    """Métricas de carreira para volantes."""
    minutos = stats.get("minutesPlayed", 0)
    total_jogos = stats.get("countRating", 0) or round(minutos / 90, 1)

    return {
        "Jogos na carreira": int(total_jogos),
        "Minutos jogados": minutos,
        "Desarmes/90min": _p90(stats.get("tackles", 0), minutos),
        "Interceptações/90min": _p90(stats.get("interceptions", 0), minutos),
        "Passes certos/90min": _p90(stats.get("accuratePasses", 0), minutos),
        "Duelos ganhos/90min": _p90(stats.get("totalDuelsWon", 0), minutos),
        "Gols": stats.get("goals", 0),
        "Assistências": stats.get("assists", 0),
        "Gols/90min": _p90(stats.get("goals", 0), minutos),
        "Cartões amarelos": stats.get("yellowCards", 0),
        "Nota média": round(stats.get("rating", 0) / stats.get("countRating", 1), 2) if stats.get("countRating") else 0,
    }


def metricas_carreira_meia(stats: dict) -> dict:
    """Métricas de carreira para meias/armadores."""
    minutos = stats.get("minutesPlayed", 0)
    total_jogos = stats.get("countRating", 0) or round(minutos / 90, 1)

    return {
        "Jogos na carreira": int(total_jogos),
        "Minutos jogados": minutos,
        "Gols": stats.get("goals", 0),
        "Assistências": stats.get("assists", 0),
        "Gols/90min": _p90(stats.get("goals", 0), minutos),
        "Assistências/90min": _p90(stats.get("assists", 0), minutos),
        "Passes decisivos/90min": _p90(stats.get("keyPasses", 0), minutos),
        "Grandes chances criadas/90min": _p90(stats.get("bigChancesCreated", 0), minutos),
        "Dribles certos/90min": _p90(stats.get("successfulDribbles", 0), minutos),
        "Finalizações no gol/90min": _p90(stats.get("shotsOnTarget", 0), minutos),
        "Nota média": round(stats.get("rating", 0) / stats.get("countRating", 1), 2) if stats.get("countRating") else 0,
    }


def metricas_carreira_ponta(stats: dict) -> dict:
    """Métricas de carreira para pontas."""
    minutos = stats.get("minutesPlayed", 0)
    total_jogos = stats.get("countRating", 0) or round(minutos / 90, 1)

    return {
        "Jogos na carreira": int(total_jogos),
        "Minutos jogados": minutos,
        "Gols": stats.get("goals", 0),
        "Assistências": stats.get("assists", 0),
        "Gols/90min": _p90(stats.get("goals", 0), minutos),
        "Assistências/90min": _p90(stats.get("assists", 0), minutos),
        "Dribles certos/90min": _p90(stats.get("successfulDribbles", 0), minutos),
        "Grandes chances criadas/90min": _p90(stats.get("bigChancesCreated", 0), minutos),
        "Finalizações no gol/90min": _p90(stats.get("shotsOnTarget", 0), minutos),
        "Passes decisivos/90min": _p90(stats.get("keyPasses", 0), minutos),
        "Nota média": round(stats.get("rating", 0) / stats.get("countRating", 1), 2) if stats.get("countRating") else 0,
    }


def metricas_carreira_atacante(stats: dict) -> dict:
    """Métricas de carreira para atacantes/centroavantes."""
    minutos = stats.get("minutesPlayed", 0)
    total_jogos = stats.get("countRating", 0) or round(minutos / 90, 1)
    gols = stats.get("goals", 0)
    total_shots = stats.get("totalShots", 0)

    return {
        "Jogos na carreira": int(total_jogos),
        "Minutos jogados": minutos,
        "Gols": gols,
        "Assistências": stats.get("assists", 0),
        "Gols/90min": _p90(gols, minutos),
        "Conversão de gols (%)": _pct(gols, total_shots) if total_shots else 0,
        "Finalizações no gol/90min": _p90(stats.get("shotsOnTarget", 0), minutos),
        "Grandes chances perdidas": stats.get("bigChancesMissed", 0),
        "Duelos aéreos ganhos/90min": _p90(stats.get("aerialDuelsWon", 0), minutos),
        "Dribles certos/90min": _p90(stats.get("successfulDribbles", 0), minutos),
        "Nota média": round(stats.get("rating", 0) / stats.get("countRating", 1), 2) if stats.get("countRating") else 0,
    }


# Mapeamento posição Transfermarkt → função de métricas de carreira
POSICAO_TM_METRICAS_MAP = {
    "Centre-Forward": metricas_carreira_atacante,
    "Second Striker": metricas_carreira_atacante,
    "Left Winger": metricas_carreira_ponta,
    "Right Winger": metricas_carreira_ponta,
    "Attacking Midfield": metricas_carreira_meia,
    "Central Midfield": metricas_carreira_volante,
    "Defensive Midfield": metricas_carreira_volante,
    "Left Midfield": metricas_carreira_meia,
    "Right Midfield": metricas_carreira_meia,
    "Left-Back": metricas_carreira_lateral,
    "Right-Back": metricas_carreira_lateral,
    "Centre-Back": metricas_carreira_zagueiro,
    "Goalkeeper": metricas_carreira_goleiro,
}


def get_metricas_carreira(posicao_tm: str, stats_acumuladas: dict) -> dict:
    """Retorna métricas de carreira consolidadas de acordo com a posição."""
    func = POSICAO_TM_METRICAS_MAP.get(posicao_tm, metricas_carreira_atacante)
    return func(stats_acumuladas)

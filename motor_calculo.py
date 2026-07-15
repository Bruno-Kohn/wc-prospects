"""
Motor de Cálculo do Índice de Relevância Real (IRR)
===================================================
Calcula a relevância de performance de jogadores de forma justa
entre diferentes ligas e posições.

Fórmula principal:
    RPP = IPB × F_liga × F_adversario × F_importancia × F_tempo

Onde:
    - IPB: Índice de Performance Bruta (calculado por posição)
    - F_liga: Coeficiente UEFA da liga
    - F_adversario: 1.2 - ((pos_adversario - 1) / 19) * 0.6
    - F_importancia: Peso do jogo (1.0 a 1.5)
    - F_tempo: minutos / 90
"""

from dataclasses import dataclass
from enum import Enum


class Posicao(Enum):
    GK = "Goleiro"
    CB = "Zagueiro"
    FB = "Lateral"
    DM = "Volante"
    AM = "Meia"
    WG = "Ponta"
    ST = "Centroavante"


@dataclass
class JogoContexto:
    """Contexto da partida para cálculo dos fatores multiplicadores."""
    coeficiente_liga: float
    peso_do_jogo: float  # 1.0 a 1.5
    posicao_adversario: int  # 1 a 20

    def __post_init__(self):
        self.peso_do_jogo = max(1.0, min(1.5, self.peso_do_jogo))
        self.posicao_adversario = max(1, min(20, self.posicao_adversario))

    @property
    def fator_adversario(self) -> float:
        """Adversário em 1º lugar = 1.2, em 20º = 0.6"""
        return 1.2 - ((self.posicao_adversario - 1) / 19) * 0.6

    @property
    def fator_importancia(self) -> float:
        return self.peso_do_jogo

    @property
    def fator_liga(self) -> float:
        return self.coeficiente_liga


@dataclass
class EstatisticasPartida:
    """Estatísticas individuais de um jogador em uma partida."""
    # Tempo
    minutos_jogados: int = 0

    # Ofensivas
    gols: int = 0
    assistencias: int = 0
    passes_certos: int = 0
    passes_tentados: int = 0
    grandes_chances_criadas: int = 0
    finalizacoes_no_gol: int = 0
    finalizacoes_fora: int = 0
    dribles_certos: int = 0
    dribles_tentados: int = 0

    # Defensivas
    desarmes: int = 0
    interceptacoes: int = 0
    cortes: int = 0
    bloqueios: int = 0
    duelos_aereos_ganhos: int = 0
    duelos_aereos_perdidos: int = 0

    # Goleiro
    defesas: int = 0
    gols_sofridos: int = 0
    clean_sheet: bool = False
    penaltis_defendidos: int = 0

    # Físico
    distancia_alta_velocidade_km: float = 0.0
    velocidade_maxima_kmh: float = 0.0

    # Disciplina / Negativas
    cartao_amarelo: int = 0
    cartao_vermelho: int = 0
    faltas_cometidas: int = 0
    faltas_sofridas: int = 0
    penalti_cometido: int = 0
    gol_contra: int = 0
    erros_para_gol: int = 0
    perda_de_posse: int = 0

    @property
    def fator_tempo(self) -> float:
        return min(self.minutos_jogados / 90, 1.0)

    @property
    def precisao_passes(self) -> float:
        if self.passes_tentados == 0:
            return 0.0
        return self.passes_certos / self.passes_tentados

    @property
    def precisao_dribles(self) -> float:
        if self.dribles_tentados == 0:
            return 0.0
        return self.dribles_certos / self.dribles_tentados


# --- Cálculo de IPB por posição ---

def _ipb_goleiro(stats: EstatisticasPartida) -> float:
    pontos = 0.0
    pontos += stats.defesas * 2.5
    pontos += stats.penaltis_defendidos * 8.0
    pontos += 5.0 if stats.clean_sheet else 0.0
    pontos += stats.cortes * 1.0
    pontos += stats.passes_certos * 0.1
    pontos -= stats.gols_sofridos * 2.0
    pontos -= stats.erros_para_gol * 5.0
    return pontos


def _ipb_zagueiro(stats: EstatisticasPartida) -> float:
    pontos = 0.0
    pontos += stats.desarmes * 2.0
    pontos += stats.interceptacoes * 1.5
    pontos += stats.cortes * 1.0
    pontos += stats.bloqueios * 1.5
    pontos += stats.duelos_aereos_ganhos * 1.0
    pontos += 4.0 if stats.clean_sheet else 0.0
    pontos += stats.gols * 6.0
    pontos += stats.passes_certos * 0.05
    pontos -= stats.erros_para_gol * 5.0
    pontos -= stats.duelos_aereos_perdidos * 0.5
    pontos -= stats.perda_de_posse * 0.3
    return pontos


def _ipb_lateral(stats: EstatisticasPartida) -> float:
    pontos = 0.0
    pontos += stats.assistencias * 5.0
    pontos += stats.grandes_chances_criadas * 3.0
    pontos += stats.desarmes * 1.5
    pontos += stats.interceptacoes * 1.0
    pontos += stats.dribles_certos * 1.5
    pontos += stats.passes_certos * 0.1
    pontos += stats.gols * 5.0
    pontos += 3.0 if stats.clean_sheet else 0.0
    pontos += stats.distancia_alta_velocidade_km * 0.5
    pontos -= stats.erros_para_gol * 4.0
    pontos -= stats.perda_de_posse * 0.3
    return pontos


def _ipb_volante(stats: EstatisticasPartida) -> float:
    pontos = 0.0
    pontos += stats.desarmes * 2.0
    pontos += stats.interceptacoes * 2.0
    pontos += stats.passes_certos * 0.15
    pontos += stats.gols * 5.0
    pontos += stats.assistencias * 4.0
    pontos += stats.duelos_aereos_ganhos * 0.8
    pontos += stats.bloqueios * 1.0
    if stats.precisao_passes >= 0.90:
        pontos += 2.0
    pontos -= stats.erros_para_gol * 4.0
    pontos -= stats.perda_de_posse * 0.4
    return pontos


def _ipb_meia(stats: EstatisticasPartida) -> float:
    pontos = 0.0
    pontos += stats.assistencias * 7.0
    pontos += stats.grandes_chances_criadas * 4.0
    pontos += stats.gols * 6.0
    pontos += stats.passes_certos * 0.15
    pontos += stats.dribles_certos * 1.5
    pontos += stats.finalizacoes_no_gol * 1.0
    if stats.precisao_passes >= 0.88:
        pontos += 1.5
    pontos -= stats.perda_de_posse * 0.4
    pontos -= stats.erros_para_gol * 3.0
    return pontos


def _ipb_ponta(stats: EstatisticasPartida) -> float:
    pontos = 0.0
    pontos += stats.gols * 7.0
    pontos += stats.assistencias * 6.0
    pontos += stats.dribles_certos * 2.0
    pontos += stats.grandes_chances_criadas * 3.5
    pontos += stats.finalizacoes_no_gol * 1.0
    if stats.velocidade_maxima_kmh >= 33.0:
        pontos += 1.5
    pontos += stats.distancia_alta_velocidade_km * 0.3
    pontos -= stats.perda_de_posse * 0.3
    pontos -= (stats.dribles_tentados - stats.dribles_certos) * 0.3
    return pontos


def _ipb_centroavante(stats: EstatisticasPartida) -> float:
    pontos = 0.0
    pontos += stats.gols * 8.0
    pontos += stats.assistencias * 5.0
    pontos += stats.finalizacoes_no_gol * 1.5
    pontos += stats.duelos_aereos_ganhos * 1.0
    pontos += stats.grandes_chances_criadas * 3.0
    pontos += stats.dribles_certos * 1.0
    pontos -= stats.perda_de_posse * 0.2
    pontos -= stats.finalizacoes_fora * 0.3
    return pontos


_IPB_FUNCOES = {
    Posicao.GK: _ipb_goleiro,
    Posicao.CB: _ipb_zagueiro,
    Posicao.FB: _ipb_lateral,
    Posicao.DM: _ipb_volante,
    Posicao.AM: _ipb_meia,
    Posicao.WG: _ipb_ponta,
    Posicao.ST: _ipb_centroavante,
}


def _penalidades_disciplinares(stats: EstatisticasPartida) -> float:
    pen = 0.0
    pen += stats.cartao_amarelo * 1.5
    pen += stats.cartao_vermelho * 5.0
    pen += stats.penalti_cometido * 3.0
    pen += stats.gol_contra * 4.0
    return pen


def calcular_ipb(posicao: Posicao, stats: EstatisticasPartida) -> float:
    """Calcula o Índice de Performance Bruta para uma posição específica."""
    func = _IPB_FUNCOES[posicao]
    ipb_bruto = func(stats)
    penalidades = _penalidades_disciplinares(stats)
    return max(0.0, ipb_bruto - penalidades)


def calcular_rpp(
    posicao: Posicao,
    stats: EstatisticasPartida,
    contexto: JogoContexto,
) -> float:
    """
    Calcula a Relevância de Performance por Posição (RPP).
    RPP = IPB × F_liga × F_adversario × F_importancia × F_tempo
    """
    ipb = calcular_ipb(posicao, stats)
    rpp = (
        ipb
        * contexto.fator_liga
        * contexto.fator_adversario
        * contexto.fator_importancia
        * stats.fator_tempo
    )
    return round(rpp, 2)


def calcular_irr(lista_rpp: list[float]) -> float:
    """
    Calcula o IRR a partir de uma lista de RPPs.
    Média ponderada com mais peso para partidas recentes.
    """
    if not lista_rpp:
        return 0.0
    n = len(lista_rpp)
    pesos = [(i + 1) for i in range(n)]
    soma_ponderada = sum(rpp * peso for rpp, peso in zip(lista_rpp, pesos))
    soma_pesos = sum(pesos)
    return round(soma_ponderada / soma_pesos, 2)


# --- Coeficientes de Liga (referência UEFA 2024/25) ---
COEFICIENTES_LIGA = {
    "Premier League": 1.00,
    "La Liga": 0.95,
    "Serie A": 0.90,
    "Bundesliga": 0.88,
    "Ligue 1": 0.85,
    "Brasileirão": 0.75,
    "Liga Portugal": 0.78,
    "Eredivisie": 0.72,
    "Champions League": 1.10,
    "Europa League": 0.95,
    "Conference League": 0.85,
    "Copa Libertadores": 0.80,
    "Copa do Mundo": 1.20,
    "Eliminatórias": 1.00,
}

# --- Pesos de Jogo ---
PESOS_JOGO = {
    "amistoso": 1.0,
    "fase_grupos": 1.1,
    "oitavas": 1.2,
    "quartas": 1.3,
    "semifinal": 1.4,
    "final": 1.5,
    "liga_regular": 1.1,
    "decisao_titulo": 1.4,
    "rebaixamento": 1.3,
}

"""
Script para coletar estatísticas do SofaScore localmente.
Roda na sua máquina e salva os dados no repositório.

Uso:
    python coletar_stats.py

O script lê a watchlist.json, busca cada jogador no SofaScore,
coleta stats das últimas temporadas e salva em stats_cache.json.
Depois faça git add/commit/push para atualizar o app.
"""

import truststore
truststore.inject_into_ssl()

import json
import time
from pathlib import Path
from sofascore_api import (
    buscar_id_sofascore,
    buscar_temporadas,
    buscar_stats_temporada,
    get_metricas_carreira,
)

WATCHLIST_PATH = Path("watchlist.json")
CACHE_PATH = Path("stats_cache.json")


def carregar_watchlist() -> dict:
    if not WATCHLIST_PATH.exists():
        print("watchlist.json não encontrado.")
        return {}
    with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def carregar_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_cache(cache: dict):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"\nCache salvo em {CACHE_PATH}")


def main():
    wl = carregar_watchlist()
    jogadores = wl.get("_jogadores", {})
    cache = carregar_cache()

    total = sum(len(v) for v in jogadores.values())
    print(f"Total de jogadores na watchlist: {total}\n")

    count = 0
    for posicao, lista in jogadores.items():
        for j in lista:
            count += 1
            nome = j.get("name", "")
            player_id = j.get("id", "")
            posicao_tm = j.get("position", "")
            clube = j.get("club", "")
            nascimento = j.get("nascimento", "")
            altura = j.get("height") or 0

            print(f"[{count}/{total}] {nome} ({posicao})...")

            # Buscar no SofaScore
            ss_player = buscar_id_sofascore(nome, clube, nascimento, altura)
            if not ss_player or "error" in ss_player:
                print(f"  ❌ Não encontrado no SofaScore")
                time.sleep(1)
                continue

            print(f"  ✓ Encontrado: {ss_player['name']} (ID: {ss_player['id']})")

            # Buscar temporadas
            temporadas = buscar_temporadas(ss_player["id"])
            if not temporadas:
                print(f"  ❌ Sem temporadas disponíveis")
                time.sleep(1)
                continue

            # Separar temporadas de clube vs seleção
            temps_clube = [t for t in temporadas if "World" not in t["tournament_name"]
                          and "Qualification" not in t["tournament_name"]
                          and "Cup 20" not in t["season_name"]  # Copa do Mundo
                          and "Championship" not in t["tournament_name"]]
            temps_selecao = [t for t in temporadas if t not in temps_clube]

            # Buscar TODAS as temporadas para consolidar
            all_temps = temps_clube + temps_selecao

            stats_jogador = {
                "sofascore_id": ss_player["id"],
                "sofascore_name": ss_player["name"],
            }

            # Acumular stats brutas de todas as temporadas
            stats_acumuladas = {}
            temps_coletadas = 0

            for temp in all_temps:
                stats = buscar_stats_temporada(
                    ss_player["id"], temp["tournament_id"], temp["season_id"]
                )
                if stats:
                    temps_coletadas += 1
                    # Somar valores numéricos
                    for key, value in stats.items():
                        if isinstance(value, (int, float)):
                            stats_acumuladas[key] = stats_acumuladas.get(key, 0) + value
                    print(f"  ✓ {temp['season_name']} — {temp['tournament_name']}")
                time.sleep(0.3)

            if stats_acumuladas:
                # Calcular métricas de carreira consolidadas
                metricas = get_metricas_carreira(posicao_tm, stats_acumuladas)
                stats_jogador["metricas"] = metricas
                stats_jogador["temporadas_coletadas"] = temps_coletadas
                print(f"  📊 {temps_coletadas} temporadas consolidadas")
            else:
                print(f"  ⚠️ Sem dados estatísticos")

            cache[player_id] = stats_jogador
            time.sleep(1)  # Rate limiting entre jogadores

    salvar_cache(cache)
    print(f"\n✅ Concluído! {len(cache)} jogadores no cache.")
    print("Agora faça: git add stats_cache.json && git commit -m 'Update stats cache' && git push")


if __name__ == "__main__":
    main()

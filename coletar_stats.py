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
    get_stats_por_posicao,
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

            print(f"[{count}/{total}] {nome} ({posicao})...")

            # Buscar no SofaScore
            ss_player = buscar_id_sofascore(nome, clube)
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

            # Coletar stats das últimas 4 temporadas
            stats_jogador = {
                "sofascore_id": ss_player["id"],
                "sofascore_name": ss_player["name"],
                "temporadas": [],
            }

            for temp in temporadas[:4]:
                stats = buscar_stats_temporada(
                    ss_player["id"], temp["tournament_id"], temp["season_id"]
                )
                if stats:
                    stats_formatadas = get_stats_por_posicao(posicao_tm, stats)
                    stats_jogador["temporadas"].append({
                        "season_name": temp["season_name"],
                        "tournament_name": temp["tournament_name"],
                        "stats": stats_formatadas,
                        "raw": stats,
                    })
                    print(f"  ✓ {temp['season_name']} — {temp['tournament_name']}")
                time.sleep(0.5)  # Rate limiting

            cache[player_id] = stats_jogador
            time.sleep(1)  # Rate limiting entre jogadores

    salvar_cache(cache)
    print(f"\n✅ Concluído! {len(cache)} jogadores no cache.")
    print("Agora faça: git add stats_cache.json && git commit -m 'Update stats cache' && git push")


if __name__ == "__main__":
    main()

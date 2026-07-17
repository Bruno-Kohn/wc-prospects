"""
Migra watchlist.json de dados Transfermarkt para dados SofaScore.
Atualiza nomes, fotos, market value, etc.
Gera notfound.json com jogadores não encontrados.
"""

import truststore
truststore.inject_into_ssl()

import json
import time
import requests
from datetime import datetime
from pathlib import Path
from sofascore_api import buscar_id_sofascore

WATCHLIST_PATH = Path("watchlist.json")
NOTFOUND_PATH = Path("notfound.json")
SOFASCORE_BASE = "https://www.sofascore.com/api/v1"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def buscar_perfil_sofascore(player_id: int) -> dict | None:
    try:
        resp = requests.get(f"{SOFASCORE_BASE}/player/{player_id}", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("player")
    except Exception:
        pass
    return None


def main():
    with open(WATCHLIST_PATH, "r", encoding="utf-8") as f:
        wl = json.load(f)

    jogadores = wl.get("_jogadores", {})
    total = sum(len(v) for v in jogadores.values())
    print(f"Total de jogadores: {total}\n")

    not_found = []
    count = 0

    for posicao, lista in jogadores.items():
        for j in lista:
            count += 1
            nome_tm = j.get("name", "")
            clube = j.get("club", "")
            nascimento = j.get("nascimento", "")
            altura = j.get("height") or 0

            print(f"[{count}/{total}] {nome_tm} ({clube})...", end=" ")

            # Buscar no SofaScore
            ss_player = buscar_id_sofascore(nome_tm, clube, nascimento, altura)
            if not ss_player or "error" in ss_player:
                print("❌ NOT FOUND")
                not_found.append({
                    "nome_transfermarkt": nome_tm,
                    "clube": clube,
                    "posicao": posicao,
                    "nascimento": nascimento,
                    "id_transfermarkt": j.get("id"),
                })
                time.sleep(0.5)
                continue

            sf_id = ss_player["id"]
            print(f"→ {ss_player['name']} (ID: {sf_id})")

            # Buscar perfil completo
            perfil = buscar_perfil_sofascore(sf_id)
            if not perfil:
                print(f"    ⚠️ Perfil não carregado, mantendo dados parciais")
                j["sofascore_id"] = sf_id
                j["name"] = ss_player["name"]
                j["imageUrl"] = f"https://api.sofascore.app/api/v1/player/{sf_id}/image"
                time.sleep(0.5)
                continue

            # Atualizar dados com SofaScore
            j["sofascore_id"] = sf_id
            j["name"] = perfil.get("name", ss_player["name"])
            j["imageUrl"] = f"https://api.sofascore.app/api/v1/player/{sf_id}/image"
            j["club"] = perfil.get("team", {}).get("name", j.get("club", ""))
            j["clubCountry"] = perfil.get("team", {}).get("country", {}).get("name", "")
            j["height"] = perfil.get("height", j.get("height"))
            j["marketValue"] = perfil.get("proposedMarketValue") or j.get("marketValue")
            j["position"] = perfil.get("position", j.get("position", ""))

            foot = perfil.get("preferredFoot", "")
            if foot:
                j["foot"] = {"Left": "left", "Right": "right", "Both": "both"}.get(foot, j.get("foot", ""))

            ts = perfil.get("dateOfBirthTimestamp")
            if ts:
                j["nascimento"] = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")

            time.sleep(0.3)

    # Salvar watchlist atualizada
    with open(WATCHLIST_PATH, "w", encoding="utf-8") as f:
        json.dump(wl, f, ensure_ascii=False, indent=2)
    print(f"\n✅ watchlist.json atualizada!")

    # Salvar not found
    if not_found:
        with open(NOTFOUND_PATH, "w", encoding="utf-8") as f:
            json.dump(not_found, f, ensure_ascii=False, indent=2)
        print(f"⚠️ {len(not_found)} jogadores não encontrados → {NOTFOUND_PATH}")
    else:
        print("🎉 Todos os jogadores encontrados!")

    print(f"\nPróximo passo: git add watchlist.json && git commit -m 'Migrate watchlist to SofaScore data' && git push")


if __name__ == "__main__":
    main()

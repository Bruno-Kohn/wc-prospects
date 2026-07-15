"""
Crawler de Estatísticas - SofaScore
====================================
Rotina assíncrona com Playwright que acessa partidas do SofaScore,
intercepta requisições de rede e extrai dados estatísticos do JSON
da API interna do site.

Uso:
    python crawler.py <url_da_partida> [--output arquivo.json]

Exemplo:
    python crawler.py "https://www.sofascore.com/football/match/..."
"""

import asyncio
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Playwright não instalado. Execute: pip install playwright && playwright install")
    raise


async def interceptar_estatisticas(url_partida: str, timeout_ms: int = 30000) -> dict:
    """
    Acessa a URL da partida e intercepta as requisições de rede
    que contenham dados estatísticos.

    Monitora respostas com status 200 cujas URLs contenham
    '/statistics' ou '/event' para extrair o JSON da API interna.
    """
    dados_coletados = {
        "url_partida": url_partida,
        "data_coleta": datetime.now().isoformat(),
        "statistics": [],
        "events": [],
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Interceptar respostas de rede
        async def handle_response(response):
            try:
                url = response.url
                if response.status == 200:
                    if "/statistics" in url:
                        body = await response.json()
                        dados_coletados["statistics"].append({
                            "url": url,
                            "data": body,
                        })
                        print(f"  [STATS] Capturado: {url[:100]}")
                    elif "/event" in url and "json" in (response.headers.get("content-type", "")):
                        body = await response.json()
                        dados_coletados["events"].append({
                            "url": url,
                            "data": body,
                        })
                        print(f"  [EVENT] Capturado: {url[:100]}")
            except Exception:
                pass

        page.on("response", handle_response)

        print(f"Acessando: {url_partida}")
        await page.goto(url_partida, wait_until="networkidle", timeout=timeout_ms)

        # Aguardar carregamento adicional de dados lazy-loaded
        await page.wait_for_timeout(5000)

        # Tentar clicar em abas de estatísticas para forçar carregamento
        try:
            stats_tab = page.locator("text=Statistics").first
            if await stats_tab.is_visible():
                await stats_tab.click()
                await page.wait_for_timeout(3000)
        except Exception:
            pass

        await browser.close()

    total = len(dados_coletados["statistics"]) + len(dados_coletados["events"])
    print(f"\nColeta finalizada: {total} requisições capturadas")
    return dados_coletados


def salvar_json(dados: dict, caminho: str):
    """Salva os dados coletados em arquivo JSON."""
    path = Path(caminho)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"Dados salvos em: {path}")


def extrair_estatisticas_jogador(dados: dict, nome_jogador: str = None) -> list[dict]:
    """
    Extrai estatísticas individuais dos dados coletados.
    Retorna lista de dicts com stats por jogador.
    """
    jogadores = []

    for stat_entry in dados.get("statistics", []):
        data = stat_entry.get("data", {})

        # Formato SofaScore: statistics > groups > statisticsItems
        if isinstance(data, dict):
            # Tentar extrair do formato de player statistics
            for group in data.get("statistics", []):
                if isinstance(group, dict):
                    for item in group.get("groups", []):
                        if isinstance(item, dict):
                            for stat_item in item.get("statisticsItems", []):
                                jogadores.append(stat_item)

    if nome_jogador:
        jogadores = [
            j for j in jogadores
            if nome_jogador.lower() in json.dumps(j).lower()
        ]

    return jogadores


async def main():
    parser = argparse.ArgumentParser(description="Crawler de estatísticas SofaScore")
    parser.add_argument("url", help="URL da partida no SofaScore")
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Caminho do arquivo JSON de saída (padrão: data/partida_<timestamp>.json)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Timeout em ms para carregamento da página (padrão: 30000)"
    )

    args = parser.parse_args()

    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"data/partida_{timestamp}.json"

    dados = await interceptar_estatisticas(args.url, timeout_ms=args.timeout)
    salvar_json(dados, args.output)


if __name__ == "__main__":
    asyncio.run(main())

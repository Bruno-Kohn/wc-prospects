import streamlit as st
import requests
import json
import base64

from utils import GITHUB_REPO, WATCHLIST_PATH, POSICOES_DEFAULT


def _github_headers():
    return {
        "Authorization": f"token {st.secrets['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }


def _carregar_watchlist_github() -> dict:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{WATCHLIST_PATH}"
    try:
        resp = requests.get(url, headers=_github_headers(), timeout=10)
        if resp.status_code == 200:
            content = base64.b64decode(resp.json()["content"]).decode()
            return json.loads(content)
        return {"_ordem_posicoes": POSICOES_DEFAULT, "_jogadores": {}}
    except Exception:
        return {"_ordem_posicoes": POSICOES_DEFAULT, "_jogadores": {}}


def _salvar_watchlist_github(data: dict):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{WATCHLIST_PATH}"
    content_b64 = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode()
    payload = {"message": "Update watchlist", "content": content_b64}
    try:
        resp = requests.get(url, headers=_github_headers(), timeout=10)
        if resp.status_code == 200:
            payload["sha"] = resp.json()["sha"]
    except Exception:
        pass
    requests.put(url, headers=_github_headers(), json=payload, timeout=10)


def get_watchlist() -> dict:
    if "watchlist" not in st.session_state:
        st.session_state["watchlist"] = _carregar_watchlist_github()
    wl = st.session_state["watchlist"]
    if "_ordem_posicoes" not in wl:
        wl["_ordem_posicoes"] = POSICOES_DEFAULT
    if "_jogadores" not in wl:
        jogadores = {}
        for k, v in wl.items():
            if k not in ("_ordem_posicoes", "_jogadores") and isinstance(v, list):
                jogadores[k] = v
        wl["_jogadores"] = jogadores
        for k in list(jogadores.keys()):
            if k in wl and k not in ("_ordem_posicoes", "_jogadores"):
                del wl[k]
    return wl


def salvar_watchlist():
    wl = st.session_state["watchlist"]
    _salvar_watchlist_github(wl)


@st.cache_data(ttl=300)
def carregar_stats_cache() -> dict:
    """Carrega stats_cache.json do repositório via GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/stats_cache.json"
    try:
        resp = requests.get(url, headers=_github_headers(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("content")
            if content:
                return json.loads(base64.b64decode(content).decode())
            download_url = data.get("download_url")
            if download_url:
                resp2 = requests.get(download_url, timeout=15)
                if resp2.status_code == 200:
                    return resp2.json()
    except Exception:
        pass
    return {}

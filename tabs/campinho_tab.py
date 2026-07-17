import streamlit as st
from components.campinho import campinho
from utils import POSICOES_DEFAULT, calcular_idades, formatar_valor
from github_api import get_watchlist, salvar_watchlist


DEFAULT_POSITIONS = [
    {"x": 50, "y": 92}, {"x": 80, "y": 72}, {"x": 60, "y": 75},
    {"x": 40, "y": 75}, {"x": 20, "y": 72}, {"x": 70, "y": 50},
    {"x": 50, "y": 50}, {"x": 30, "y": 50}, {"x": 75, "y": 25},
    {"x": 50, "y": 12}, {"x": 25, "y": 25},
]


def render(modo_edicao: bool):
    wl = get_watchlist()
    jogadores_campo = wl.get("_jogadores", {})

    todos_wl = []
    for pos in POSICOES_DEFAULT:
        for j in jogadores_campo.get(pos, []):
            todos_wl.append(j)

    campinho_salvo = wl.get("_campinho_pos", {})

    if not todos_wl:
        st.info("Adicione jogadores na Watchlist para escalá-los aqui.")
        return

    jogadores_data = [
        {"id": j["id"], "name": j["name"], "imageUrl": j.get("imageUrl", ""), "club": j.get("club", "")}
        for j in todos_wl
    ]

    slots_data = []
    if isinstance(campinho_salvo, dict) and campinho_salvo:
        for i in range(11):
            slot_key = str(i)
            if slot_key in campinho_salvo:
                s = campinho_salvo[slot_key]
                slots_data.append({"playerId": s.get("id", ""), "x": s.get("x", DEFAULT_POSITIONS[i]["x"]), "y": s.get("y", DEFAULT_POSITIONS[i]["y"])})
            else:
                slots_data.append({"playerId": "", "x": DEFAULT_POSITIONS[i]["x"], "y": DEFAULT_POSITIONS[i]["y"]})

    if not slots_data:
        slots_data = [{"playerId": "", "x": p["x"], "y": p["y"]} for p in DEFAULT_POSITIONS]

    result = campinho(jogadores=jogadores_data, slots=slots_data, key="campinho_main")

    if result:
        ids_no_campo = [s.get("playerId") for s in result if s.get("playerId")]
        jogadores_no_campo = [j for j in todos_wl if j["id"] in ids_no_campo]
        if jogadores_no_campo:
            _idades = []
            _valor = 0
            for j in jogadores_no_campo:
                nasc = j.get("nascimento")
                if nasc:
                    idade, _, _ = calcular_idades(nasc)
                    _idades.append(idade)
                _valor += j.get("marketValue") or 0
            media_str = f"Média de idade: {sum(_idades)/len(_idades):.1f} anos" if _idades else ""
            valor_str = f"Valor de mercado total: {formatar_valor(_valor)}"
            st.caption(f"{len(jogadores_no_campo)} jogadores escalados | {media_str} | {valor_str}")

    if st.button("💾 Salvar no GitHub", use_container_width=True, disabled=not modo_edicao):
        if result:
            save_data = {}
            for i, s in enumerate(result):
                save_data[str(i)] = {"id": s.get("playerId", ""), "x": s["x"], "y": s["y"]}
            wl["_campinho_pos"] = save_data
            salvar_watchlist()
            st.success("Posições salvas!")

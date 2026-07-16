import streamlit.components.v1 as components
import os

_COMPONENT_DIR = os.path.dirname(os.path.abspath(__file__))
_component_func = components.declare_component("campinho", path=_COMPONENT_DIR)


def campinho(jogadores, posicoes, key=None):
    """
    Renders an interactive football pitch with draggable players.

    Args:
        jogadores: list of dicts with {id, name, imageUrl, club}
        posicoes: dict {player_id: {x: float 0-100, y: float 0-100}}
        key: unique component key

    Returns:
        Updated posicoes dict after drag operations.
    """
    result = _component_func(
        jogadores=jogadores,
        posicoes=posicoes,
        key=key,
        default=posicoes,
    )
    return result if result else posicoes

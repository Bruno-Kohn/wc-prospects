import streamlit.components.v1 as components
import os

_COMPONENT_DIR = os.path.dirname(os.path.abspath(__file__))
_component_func = components.declare_component("campinho", path=_COMPONENT_DIR)


def campinho(jogadores, slots, key=None):
    """
    Renders an interactive football pitch with 11 draggable slots.
    Players are selected by clicking on a slot.

    Args:
        jogadores: list of dicts with {id, name, imageUrl, club} - available players
        slots: list of 11 dicts with {playerId, x, y} - current slot state
        key: unique component key

    Returns:
        Updated slots list after user interactions.
    """
    result = _component_func(
        jogadores=jogadores,
        slots=slots,
        key=key,
        default=slots,
    )
    return result if result else slots

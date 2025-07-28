"""Zone activation management for abilities."""

from enum import Enum


class ActivationZone(Enum):
    """Zones where abilities can be active."""
    HAND = "hand"
    PLAY = "play"
    DISCARD = "discard"
    DECK = "deck"
    INK_WELL = "ink_well"
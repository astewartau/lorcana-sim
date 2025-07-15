"""Game event types for the stepped engine message system."""

from enum import Enum


class GameEventType(Enum):
    """Types of game events that can be reported through the message system."""
    
    # Basic game flow
    PHASE_ADVANCED = "phase_advanced"
    TURN_ENDED = "turn_ended"
    
    # Card actions
    CARD_PLAYED = "card_played"
    CARD_DRAWN = "card_drawn"
    CARD_INKED = "card_inked"
    
    # Character actions
    CHARACTER_QUESTED = "character_quested"
    CHARACTER_CHALLENGED = "character_challenged"
    CHARACTER_BANISHED = "character_banished"
    CHARACTER_READIED = "character_readied"
    
    # Ability effects
    EFFECT_APPLIED = "effect_applied"
    EFFECT_EXPIRED = "effect_expired"
    
    # Conditional effects
    CONDITIONAL_EFFECT_APPLIED = "conditional_effect_applied"
    CONDITIONAL_EFFECT_REMOVED = "conditional_effect_removed"
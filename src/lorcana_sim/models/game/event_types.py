"""Standard event types for the game state event system."""

from enum import Enum


class EventType(Enum):
    """Standard event types that can occur in the game."""
    
    # Card Events
    CARD_DRAWN = "CARD_DRAWN"
    CARD_PLAYED = "CARD_PLAYED"
    CARD_DISCARDED = "CARD_DISCARDED"
    CARD_BANISHED = "CARD_BANISHED"
    CARD_RETURNED_TO_HAND = "CARD_RETURNED_TO_HAND"
    
    # Character Events
    CHARACTER_PLAYED = "CHARACTER_PLAYED"
    CHARACTER_CHALLENGED = "CHARACTER_CHALLENGED"
    CHARACTER_QUESTED = "CHARACTER_QUESTED"
    CHARACTER_EXERTED = "CHARACTER_EXERTED"
    CHARACTER_READIED = "CHARACTER_READIED"
    CHARACTER_DAMAGED = "CHARACTER_DAMAGED"
    CHARACTER_HEALED = "CHARACTER_HEALED"
    CHARACTER_BANISHED = "CHARACTER_BANISHED"
    
    # Game Flow Events
    TURN_BEGAN = "TURN_BEGAN"
    TURN_ENDED = "TURN_ENDED"
    PHASE_CHANGED = "PHASE_CHANGED"
    GAME_ENDED = "GAME_ENDED"
    
    # Resource Events
    INK_PLAYED = "INK_PLAYED"
    LORE_GAINED = "LORE_GAINED"
    
    # Choice Events
    CHOICE_PRESENTED = "CHOICE_PRESENTED"
    CHOICE_MADE = "CHOICE_MADE"
    
    # Ability Events
    ABILITY_TRIGGERED = "ABILITY_TRIGGERED"
    ABILITY_RESOLVED = "ABILITY_RESOLVED"
    
    # Generic Events
    GAME_STATE_CHANGED = "GAME_STATE_CHANGED"
    ERROR_OCCURRED = "ERROR_OCCURRED"


# Event data structure templates for consistency
EVENT_TEMPLATES = {
    EventType.CARD_DRAWN: {
        'required_fields': ['player', 'cards_drawn', 'count', 'source'],
        'optional_fields': ['ability_name', 'hand_size_after', 'deck_size_after'],
        'description': 'A player drew one or more cards'
    },
    
    EventType.CHARACTER_PLAYED: {
        'required_fields': ['player', 'character', 'cost_paid'],
        'optional_fields': ['ink_remaining', 'abilities_triggered'],
        'description': 'A character was played onto the board'
    },
    
    EventType.CHARACTER_CHALLENGED: {
        'required_fields': ['attacker', 'defender', 'attacker_damage', 'defender_damage'],
        'optional_fields': ['banished_characters', 'abilities_triggered'],
        'description': 'A character challenged another character'
    },
    
    EventType.CHOICE_MADE: {
        'required_fields': ['player', 'choice_id', 'selected_option'],
        'optional_fields': ['ability_name', 'choice_prompt', 'available_options'],
        'description': 'A player made a choice'
    },
    
    EventType.LORE_GAINED: {
        'required_fields': ['player', 'amount', 'source'],
        'optional_fields': ['total_lore_after', 'character_name'],
        'description': 'A player gained lore'
    }
}
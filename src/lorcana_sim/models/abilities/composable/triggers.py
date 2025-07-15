"""Event trigger system for composable abilities using existing GameEvent enum."""

from typing import Callable, Dict, Any, Optional
from ....engine.event_system import GameEvent, EventContext


def when_event(event: GameEvent, 
               source_filter: Optional[Callable[[Any, EventContext], bool]] = None,
               target_filter: Optional[Callable[[Any, EventContext], bool]] = None,
               metadata_filter: Optional[Callable[[Dict, EventContext], bool]] = None) -> Callable[[EventContext], bool]:
    """Create a trigger condition for any GameEvent.
    
    Args:
        event: The GameEvent to trigger on
        source_filter: Optional filter for event source
        target_filter: Optional filter for event target
        metadata_filter: Optional filter for event metadata
        
    Returns:
        A condition function that returns True if the event matches
    """
    
    def condition(event_context: EventContext) -> bool:
        # Check event type
        if event_context.event_type != event:
            return False
        
        # Check source filter
        if source_filter and not source_filter(event_context.source, event_context):
            return False
        
        # Check target filter  
        if target_filter and not target_filter(event_context.target, event_context):
            return False
        
        # Check metadata filter
        if metadata_filter and not metadata_filter(event_context.additional_data or {}, event_context):
            return False
        
        return True
    
    # Add event information to the condition function for introspection
    condition.event_type = event
    condition.get_relevant_events = lambda: [event]
    
    return condition


# =============================================================================
# TRIGGER HELPERS FOR ALL EXISTING ABILITIES
# =============================================================================

# Character action triggers
def when_quests(character: Any) -> Callable[[EventContext], bool]:
    """Trigger when this specific character quests."""
    return when_event(GameEvent.CHARACTER_QUESTS, 
                     source_filter=lambda src, ctx: src == character)


def when_any_quests() -> Callable[[EventContext], bool]:
    """Trigger when any character quests."""
    return when_event(GameEvent.CHARACTER_QUESTS)


def when_challenges(character: Any) -> Callable[[EventContext], bool]:
    """Trigger when this character challenges."""
    return when_event(GameEvent.CHARACTER_CHALLENGES,
                     source_filter=lambda src, ctx: src == character)


def when_any_challenges() -> Callable[[EventContext], bool]:
    """Trigger when any character challenges."""
    return when_event(GameEvent.CHARACTER_CHALLENGES)


# Character lifecycle triggers
def when_enters_play(character: Any) -> Callable[[EventContext], bool]:
    """Trigger when this specific character enters play."""
    return when_event(GameEvent.CHARACTER_ENTERS_PLAY,
                     source_filter=lambda src, ctx: src == character)


def when_any_enters_play() -> Callable[[EventContext], bool]:
    """Trigger when any character enters play."""
    return when_event(GameEvent.CHARACTER_ENTERS_PLAY)


def when_leaves_play(character: Any) -> Callable[[EventContext], bool]:
    """Trigger when this specific character leaves play."""
    return when_event(GameEvent.CHARACTER_LEAVES_PLAY,
                     source_filter=lambda src, ctx: src == character)


def when_banished(character: Any) -> Callable[[EventContext], bool]:
    """Trigger when this specific character is banished, or any character if character is None."""
    if character is None:
        # Listen for any character being banished
        return when_event(GameEvent.CHARACTER_BANISHED)
    else:
        # Listen for specific character being banished
        return when_event(GameEvent.CHARACTER_BANISHED,
                         source_filter=lambda src, ctx: src == character)


# Damage triggers
def when_takes_damage(character: Any) -> Callable[[EventContext], bool]:
    """Trigger when this character takes damage."""
    return when_event(GameEvent.CHARACTER_TAKES_DAMAGE,
                     target_filter=lambda tgt, ctx: tgt == character)


def when_deals_damage(character: Any) -> Callable[[EventContext], bool]:
    """Trigger when this character deals damage."""
    return when_event(GameEvent.CHARACTER_DEALS_DAMAGE,
                     source_filter=lambda src, ctx: src == character)


def when_any_takes_damage() -> Callable[[EventContext], bool]:
    """Trigger when any character takes damage."""
    return when_event(GameEvent.CHARACTER_TAKES_DAMAGE)


# Song/Action triggers
def when_song_sung() -> Callable[[EventContext], bool]:
    """Trigger when any song is sung."""
    return when_event(GameEvent.SONG_SUNG)


def when_action_played() -> Callable[[EventContext], bool]:
    """Trigger when any action is played."""
    return when_event(GameEvent.ACTION_PLAYED)


def when_song_played() -> Callable[[EventContext], bool]:
    """Trigger when any song is played."""
    return when_event(GameEvent.SONG_PLAYED)


# Turn structure triggers
def when_turn_begins(player: Any = None) -> Callable[[EventContext], bool]:
    """Trigger at start of turn (optionally specific player's turn)."""
    if player:
        return when_event(GameEvent.TURN_BEGINS,
                         metadata_filter=lambda meta, ctx: ctx.player == player)
    return when_event(GameEvent.TURN_BEGINS)


def when_turn_ends(player: Any = None) -> Callable[[EventContext], bool]:
    """Trigger at end of turn (optionally specific player's turn)."""
    if player:
        return when_event(GameEvent.TURN_ENDS,
                         metadata_filter=lambda meta, ctx: ctx.player == player)
    return when_event(GameEvent.TURN_ENDS)


def when_ready_step() -> Callable[[EventContext], bool]:
    """Trigger during ready step."""
    return when_event(GameEvent.READY_STEP)


# Resource triggers
def when_card_drawn(player: Any = None) -> Callable[[EventContext], bool]:
    """Trigger when a card is drawn."""
    if player:
        return when_event(GameEvent.CARD_DRAWN,
                         metadata_filter=lambda meta, ctx: ctx.player == player)
    return when_event(GameEvent.CARD_DRAWN)


def when_ink_played() -> Callable[[EventContext], bool]:
    """Trigger when ink is played."""
    return when_event(GameEvent.INK_PLAYED)


def when_lore_gained() -> Callable[[EventContext], bool]:
    """Trigger when lore is gained."""
    return when_event(GameEvent.LORE_GAINED)


# Item triggers
def when_item_played() -> Callable[[EventContext], bool]:
    """Trigger when an item is played."""
    return when_event(GameEvent.ITEM_PLAYED)


# =============================================================================
# SPECIAL TRIGGERS FOR PASSIVE ABILITIES
# =============================================================================

def when_targeted_by_ability(character: Any) -> Callable[[EventContext], bool]:
    """Trigger when character would be targeted by an ability (for Ward)."""
    # This would need a new GameEvent.TARGET_REQUESTED or similar
    # For now, we'll use metadata on existing events
    def condition(event_context: EventContext) -> bool:
        # Check if this is a targeting attempt
        if event_context.additional_data and event_context.additional_data.get('targeting_attempt'):
            return event_context.target == character
        return False
    
    # Add event information for introspection
    condition.get_relevant_events = lambda: [GameEvent.CHARACTER_TAKES_DAMAGE, GameEvent.CHARACTER_CHALLENGES]
    return condition


def when_challenge_declared_against(character: Any) -> Callable[[EventContext], bool]:
    """Trigger when a challenge is declared against a character (for redirection)."""
    return when_event(GameEvent.CHARACTER_CHALLENGES,
                     target_filter=lambda tgt, ctx: tgt == character)


def when_damage_would_be_dealt_to(character: Any) -> Callable[[EventContext], bool]:
    """Trigger before damage is dealt (for Resist)."""
    # This might need GameEvent.DAMAGE_WOULD_BE_DEALT
    # For now use CHARACTER_TAKES_DAMAGE with early priority
    return when_event(GameEvent.CHARACTER_TAKES_DAMAGE,
                     target_filter=lambda tgt, ctx: tgt == character)


def when_song_cast_attempted(singer: Any) -> Callable[[EventContext], bool]:
    """Trigger when trying to cast a song with this singer."""
    return when_event(GameEvent.SONG_SUNG,
                     source_filter=lambda src, ctx: src == singer,
                     metadata_filter=lambda meta, ctx: meta.get('attempt_phase', False))


# =============================================================================
# COMPLEX CONDITION BUILDERS
# =============================================================================

def and_conditions(*conditions: Callable[[EventContext], bool]) -> Callable[[EventContext], bool]:
    """Combine multiple conditions with AND logic."""
    def combined_condition(event_context: EventContext) -> bool:
        return all(condition(event_context) for condition in conditions)
    
    # Combine relevant events from all conditions
    def get_combined_events():
        all_events = set()
        for condition in conditions:
            if hasattr(condition, 'get_relevant_events'):
                all_events.update(condition.get_relevant_events())
        return list(all_events)
    
    combined_condition.get_relevant_events = get_combined_events
    return combined_condition


def or_conditions(*conditions: Callable[[EventContext], bool]) -> Callable[[EventContext], bool]:
    """Combine multiple conditions with OR logic."""
    def combined_condition(event_context: EventContext) -> bool:
        return any(condition(event_context) for condition in conditions)
    
    # Combine relevant events from all conditions
    def get_combined_events():
        all_events = set()
        for condition in conditions:
            if hasattr(condition, 'get_relevant_events'):
                all_events.update(condition.get_relevant_events())
        return list(all_events)
    
    combined_condition.get_relevant_events = get_combined_events
    return combined_condition


def not_condition(condition: Callable[[EventContext], bool]) -> Callable[[EventContext], bool]:
    """Negate a condition."""
    def negated_condition(event_context: EventContext) -> bool:
        return not condition(event_context)
    
    # Forward relevant events from the wrapped condition
    if hasattr(condition, 'get_relevant_events'):
        negated_condition.get_relevant_events = condition.get_relevant_events
    else:
        negated_condition.get_relevant_events = lambda: []
    
    return negated_condition


def metadata_condition(key: str, value: Any) -> Callable[[EventContext], bool]:
    """Create a condition that checks additional_data."""
    def condition(event_context: EventContext) -> bool:
        return event_context.additional_data and event_context.additional_data.get(key) == value
    
    # Metadata conditions could apply to any event, so return empty list to be conservative
    condition.get_relevant_events = lambda: []
    return condition


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def is_friendly_source(event_context: EventContext) -> bool:
    """Check if event source is friendly to the ability owner."""
    # This would need the ability owner passed in context
    ability_owner = event_context.additional_data.get('ability_owner') if event_context.additional_data else None
    if not ability_owner or not event_context.source:
        return False
    return (hasattr(ability_owner, 'controller') and 
            hasattr(event_context.source, 'controller') and
            ability_owner.controller == event_context.source.controller)


def is_enemy_source(event_context: EventContext) -> bool:
    """Check if event source is an enemy."""
    return not is_friendly_source(event_context)


def get_relevant_events_for_trigger(trigger_condition: Callable) -> list[GameEvent]:
    """Analyze a trigger condition to determine which events it cares about."""
    # This is a simplified version - in production we'd parse the condition
    # For now, return all events and optimize later
    return list(GameEvent)


# =============================================================================
# NAMED ABILITY SPECIFIC TRIGGERS
# =============================================================================

def when_banished_in_challenge(character: Any) -> Callable[[EventContext], bool]:
    """Trigger when this character is banished specifically in a challenge."""
    return when_event(GameEvent.CHARACTER_BANISHED_IN_CHALLENGE,
                     source_filter=lambda src, ctx: src == character)


def when_character_type_enters_play(character_type: str, controller: Any = None) -> Callable[[EventContext], bool]:
    """Trigger when a character of specific type enters play."""
    def condition(event_context: EventContext) -> bool:
        if event_context.event_type != GameEvent.CHARACTER_ENTERS_PLAY:
            return False
        
        character = event_context.source
        if not character:
            return False
            
        # Check character type/subtype
        if hasattr(character, 'subtypes') and character_type in character.subtypes:
            # Check controller if specified
            if controller and hasattr(character, 'controller'):
                return character.controller == controller
            return True
        
        return False
    
    condition.get_relevant_events = lambda: [GameEvent.CHARACTER_ENTERS_PLAY]
    return condition


def when_character_type_leaves_play(character_type: str, controller: Any = None) -> Callable[[EventContext], bool]:
    """Trigger when a character of specific type leaves play."""
    def condition(event_context: EventContext) -> bool:
        if event_context.event_type != GameEvent.CHARACTER_LEAVES_PLAY:
            return False
        
        character = event_context.source
        if not character:
            return False
            
        # Check character type/subtype
        if hasattr(character, 'subtypes') and character_type in character.subtypes:
            # Check controller if specified
            if controller and hasattr(character, 'controller'):
                return character.controller == controller
            return True
        
        return False
    
    condition.get_relevant_events = lambda: [GameEvent.CHARACTER_LEAVES_PLAY]
    return condition


def when_character_name_enters_play(character_name: str, controller: Any = None) -> Callable[[EventContext], bool]:
    """Trigger when a character with specific name enters play."""
    def condition(event_context: EventContext) -> bool:
        if event_context.event_type != GameEvent.CHARACTER_ENTERS_PLAY:
            return False
        
        character = event_context.source
        if not character:
            return False
            
        # Check character name
        if hasattr(character, 'name') and character_name in character.name:
            # Check controller if specified
            if controller and hasattr(character, 'controller'):
                return character.controller == controller
            return True
        
        return False
    
    condition.get_relevant_events = lambda: [GameEvent.CHARACTER_ENTERS_PLAY]
    return condition


def when_character_name_leaves_play(character_name: str, controller: Any = None) -> Callable[[EventContext], bool]:
    """Trigger when a character with specific name leaves play."""
    def condition(event_context: EventContext) -> bool:
        if event_context.event_type != GameEvent.CHARACTER_LEAVES_PLAY:
            return False
        
        character = event_context.source
        if not character:
            return False
            
        # Check character name
        if hasattr(character, 'name') and character_name in character.name:
            # Check controller if specified
            if controller and hasattr(character, 'controller'):
                return character.controller == controller
            return True
        
        return False
    
    condition.get_relevant_events = lambda: [GameEvent.CHARACTER_LEAVES_PLAY]
    return condition


def when_ability_activated(character: Any, ability_name: str) -> Callable[[EventContext], bool]:
    """Trigger when specific activated ability is used."""
    return when_event(GameEvent.ABILITY_ACTIVATED,
                     source_filter=lambda src, ctx: src == character,
                     metadata_filter=lambda meta, ctx: meta.get('ability_name') == ability_name)


def on_activation() -> Callable[[EventContext], bool]:
    """Trigger for activated abilities."""
    return when_event(GameEvent.ABILITY_ACTIVATED)


def when_turn_starts(player: Any = None) -> Callable[[EventContext], bool]:
    """Trigger at start of turn (optionally specific player's turn)."""
    if player:
        return when_event(GameEvent.TURN_BEGINS,
                         metadata_filter=lambda meta, ctx: ctx.player == player)
    return when_event(GameEvent.TURN_BEGINS)


def when_character_exerts(character: Any = None) -> Callable[[EventContext], bool]:
    """Trigger when a character is exerted."""
    if character:
        return when_event(GameEvent.CHARACTER_EXERTS,
                         source_filter=lambda src, ctx: src == character)
    return when_event(GameEvent.CHARACTER_EXERTS)


def when_character_readies(character: Any = None) -> Callable[[EventContext], bool]:
    """Trigger when a character readies."""
    if character:
        return when_event(GameEvent.CHARACTER_READIED,
                         source_filter=lambda src, ctx: src == character)
    return when_event(GameEvent.CHARACTER_READIED)


def when_moves_to_location(character: Any) -> Callable[[EventContext], bool]:
    """Trigger when a character moves to a location."""
    return when_event(GameEvent.CHARACTER_MOVES_TO_LOCATION,
                     source_filter=lambda src, ctx: src == character)


def always_active() -> Callable[[EventContext], bool]:
    """Trigger that is always active (for placeholder abilities)."""
    return lambda ctx: False  # Never actually triggers
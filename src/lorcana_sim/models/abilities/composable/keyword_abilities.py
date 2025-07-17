"""Composable implementations of all existing keyword abilities."""

from typing import Any
from .composable_ability import ComposableAbility, quick_ability
from .effects import (
    StatModification, PreventEffect, ModifyDamage, ForceRetarget, 
    GrantProperty, NoEffect, ConditionalEffect,
    ShiftEffect, ChallengerEffect, VanishEffect, RecklessEffect,
    SingTogetherEffect, CostModification, ExertCharacter, ReadyCharacter,
    BodyguardEffect, SupportStrengthEffect, ModifySongCost
)
from .target_selectors import (
    SELF, NO_TARGET, EVENT_TARGET, EVENT_SOURCE, FRIENDLY_CHARACTER, OTHER_FRIENDLY, ENEMY_CHARACTER,
    CharacterSelector, has_ability_filter, ready_filter, friendly_filter, not_self_filter
)
from .triggers import (
    when_quests, when_enters_play, when_takes_damage, when_challenges,
    when_targeted_by_ability, when_challenge_declared_against, when_damage_would_be_dealt_to,
    when_song_cast_attempted, when_event
)
from ....engine.event_system import GameEvent


# =============================================================================
# RESIST ABILITY - Reduce incoming damage
# =============================================================================

def create_resist_ability(value: int, character: Any) -> ComposableAbility:
    """Resist X - This character takes X less damage.
    
    Implementation: When this character would take damage, reduce it by X.
    """
    return quick_ability(
        name=f"Resist {value}",
        character=character,
        trigger_condition=when_damage_would_be_dealt_to(character),
        target_selector=EVENT_TARGET,
        effect=ModifyDamage(value)
    )


# =============================================================================
# WARD ABILITY - Prevent ability targeting
# =============================================================================

def create_ward_ability(character: Any) -> ComposableAbility:
    """Ward - Opponents can't choose this character except to challenge.
    
    Implementation: When this character would be targeted by an ability, prevent it.
    """
    return quick_ability(
        name="Ward",
        character=character,
        trigger_condition=when_targeted_by_ability(character),
        target_selector=NO_TARGET,
        effect=PreventEffect("targeting")
    )


# =============================================================================
# BODYGUARD ABILITY - May enter play exerted, must be challenged if able
# =============================================================================

def create_bodyguard_ability(character: Any) -> ComposableAbility:
    """Bodyguard - This character may enter play exerted. An opposing character 
    who challenges one of your characters must choose one with Bodyguard if able.
    
    Implementation: When this character enters play, mark it as having bodyguard.
    The challenge targeting logic is handled by the game engine.
    """
    return quick_ability(
        name="Bodyguard",
        character=character,
        trigger_condition=when_enters_play(character),
        target_selector=SELF,
        effect=BodyguardEffect()
    )


# =============================================================================
# EVASIVE ABILITY - Only characters with Evasive can challenge
# =============================================================================

def create_evasive_ability(character: Any) -> ComposableAbility:
    """Evasive - Only characters with Evasive can challenge this character.
    
    Implementation: When a character without Evasive tries to challenge this character, prevent it.
    """
    def evasive_condition(event_context):
        # Check if it's a challenge against this character
        if not when_challenge_declared_against(character)(event_context):
            return False
        
        # Check if challenger has Evasive
        challenger = event_context.source
        if not challenger:
            return False
        
        # Check if challenger has Evasive ability
        if hasattr(challenger, 'composable_abilities'):
            for ability in challenger.composable_abilities:
                if hasattr(ability, 'name') and 'evasive' in ability.name.lower():
                    return False  # Challenger has Evasive, allow challenge
        
        return True  # Challenger doesn't have Evasive, prevent challenge
    
    # Add event introspection
    evasive_condition.get_relevant_events = lambda: [GameEvent.CHARACTER_CHALLENGES]
    
    return quick_ability(
        name="Evasive",
        character=character,
        trigger_condition=evasive_condition,
        target_selector=NO_TARGET,
        effect=PreventEffect("challenge")
    )


# =============================================================================
# SINGER ABILITY - Can sing songs for reduced cost
# =============================================================================

def create_singer_ability(cost: int, character: Any) -> ComposableAbility:
    """Singer X - This character counts as cost X to sing songs.
    
    Implementation: When attempting to sing a song with this character,
    if the song's singer cost <= X, allow it.
    """
    def singer_condition(event_context):
        # Check if this character is being used to sing
        return (event_context.additional_data and 
                event_context.additional_data.get('singer') == character)
    
    # Add event introspection
    singer_condition.get_relevant_events = lambda: [GameEvent.SONG_SUNG]
    
    return quick_ability(
        name=f"Singer {cost}",
        character=character,
        trigger_condition=singer_condition,
        target_selector=SELF,
        effect=ModifySongCost(cost)
    )


# =============================================================================
# SUPPORT ABILITY - When this character quests, add strength to another character
# =============================================================================

def create_support_ability(character: Any) -> ComposableAbility:
    """Support - Whenever this character quests, you may add their Strength 
    to another chosen character's Strength this turn.
    
    Implementation: When this character quests, allow choosing another friendly
    character to receive the strength bonus.
    """
    
    def support_condition(event_context):
        """Trigger when this character quests."""
        return (when_event(GameEvent.CHARACTER_QUESTS)(event_context) and 
                event_context.source == character)
    
    # Add event introspection
    support_condition.get_relevant_events = lambda: [GameEvent.CHARACTER_QUESTS]
    
    # Target another friendly character (in full implementation, this would be chosen)
    return quick_ability(
        name="Support",
        character=character,
        trigger_condition=support_condition,
        target_selector=OTHER_FRIENDLY,  # Choose another friendly character
        effect=SupportStrengthEffect()
    )


# =============================================================================
# RUSH ABILITY - Can challenge the turn played
# =============================================================================

def create_rush_ability(character: Any) -> ComposableAbility:
    """Rush - This character can challenge the turn they're played.
    
    Implementation: When this character enters play, grant them the ability
    to challenge with wet ink.
    """
    return quick_ability(
        name="Rush",
        character=character,
        trigger_condition=when_enters_play(character),
        target_selector=SELF,
        effect=GrantProperty("can_challenge_with_wet_ink", True)
    )


# =============================================================================
# SHIFT ABILITIES - Play for reduced cost by discarding another character
# =============================================================================

def create_shift_ability(cost: int, character: Any) -> ComposableAbility:
    """Shift X - You may pay X to play this character on top of another character named the same.
    
    Implementation: This is primarily a play-time effect, but we mark the character
    with shift capability when it enters play.
    """
    return quick_ability(
        name=f"Shift {cost}",
        character=character,
        trigger_condition=when_enters_play(character),
        target_selector=SELF,
        effect=ShiftEffect(cost)
    )


def create_puppy_shift_ability(cost: int, character: Any) -> ComposableAbility:
    """Shift X - This character can shift onto any other character (not just same name).
    
    Implementation: Similar to regular shift but with broader targeting.
    """
    return quick_ability(
        name=f"Shift {cost} (Puppy)",
        character=character,
        trigger_condition=when_enters_play(character),
        target_selector=SELF,
        effect=ShiftEffect(cost)  # The actual puppy logic is in play mechanics
    )


def create_universal_shift_ability(cost: int, character: Any) -> ComposableAbility:
    """Shift X - This character can shift onto any character.
    
    Implementation: Universal shift allows shifting onto any character.
    """
    return quick_ability(
        name=f"Shift {cost} (Universal)",
        character=character,
        trigger_condition=when_enters_play(character),
        target_selector=SELF,
        effect=ShiftEffect(cost)  # The actual universal logic is in play mechanics
    )


# =============================================================================
# CHALLENGER ABILITY - Get +X strength while challenging
# =============================================================================

def create_challenger_ability(strength_bonus: int, character: Any) -> ComposableAbility:
    """Challenger +X - While challenging, this character gets +X Strength.
    
    Implementation: When this character challenges, grant temporary strength bonus.
    """
    return quick_ability(
        name=f"Challenger +{strength_bonus}",
        character=character,
        trigger_condition=when_challenges(character),
        target_selector=SELF,
        effect=ChallengerEffect(strength_bonus)
    )


# =============================================================================
# RECKLESS ABILITY - Can't quest, must challenge if able
# =============================================================================

def create_reckless_ability(character: Any) -> ComposableAbility:
    """Reckless - Characters with Reckless can't quest and must challenge if able.
    
    Implementation: When this character enters play, mark it as reckless.
    The actual restriction logic is handled by the game engine.
    """
    return quick_ability(
        name="Reckless",
        character=character,
        trigger_condition=when_enters_play(character),
        target_selector=SELF,
        effect=RecklessEffect()
    )


# =============================================================================
# VANISH ABILITY - Banish when opponent chooses for an action
# =============================================================================

def create_vanish_ability(character: Any) -> ComposableAbility:
    """Vanish - When an opponent chooses this character for an action, banish them.
    
    Implementation: When this character is targeted by an opponent action, banish it.
    """
    def vanish_condition(event_context):
        # Check if this character is being targeted by an opponent
        if event_context.target != character:
            return False
        
        # Check if the source is an opponent
        source = event_context.source
        if source and hasattr(source, 'controller') and hasattr(character, 'controller'):
            is_opponent = source.controller != character.controller
            return is_opponent
        
        # If no clear source, check if it's an opponent's turn
        game_state = event_context.game_state
        if game_state and hasattr(game_state, 'current_player') and hasattr(character, 'controller'):
            return game_state.current_player != character.controller
        
        return False
    
    # Add event introspection
    vanish_condition.get_relevant_events = lambda: [GameEvent.CHARACTER_TAKES_DAMAGE]
    
    return quick_ability(
        name="Vanish",
        character=character,
        trigger_condition=vanish_condition,
        target_selector=SELF,
        effect=VanishEffect()
    )


# =============================================================================
# SING TOGETHER ABILITY - Multiple characters can sing together
# =============================================================================

def create_sing_together_ability(cost: int, character: Any) -> ComposableAbility:
    """Sing Together X - Multiple characters can combine their Singer values to sing songs.
    
    Implementation: When singing a song, this character can contribute its Singer value.
    """
    def sing_together_condition(event_context):
        return (when_event(GameEvent.SONG_SUNG)(event_context) and
                event_context.additional_data and
                event_context.additional_data.get('allow_multiple_singers', False))
    
    # Add event introspection
    sing_together_condition.get_relevant_events = lambda: [GameEvent.SONG_SUNG]
    
    return quick_ability(
        name=f"Sing Together {cost}",
        character=character,
        trigger_condition=sing_together_condition,
        target_selector=SELF,
        effect=SingTogetherEffect(cost)
    )


# =============================================================================
# CONVENIENCE FUNCTIONS FOR ALL ABILITIES
# =============================================================================

def create_keyword_ability(keyword: str, character: Any, value: int = None, target_name: str = None) -> ComposableAbility:
    """Create any keyword ability by name."""
    
    keyword_factories = {
        'Resist': lambda char, val, tgt: create_resist_ability(val or 1, char),
        'Ward': lambda char, val, tgt: create_ward_ability(char),
        'Bodyguard': lambda char, val, tgt: create_bodyguard_ability(char),
        'Evasive': lambda char, val, tgt: create_evasive_ability(char),
        'Singer': lambda char, val, tgt: create_singer_ability(val or 4, char),
        'Support': lambda char, val, tgt: create_support_ability(char),
        'Rush': lambda char, val, tgt: create_rush_ability(char),
        'Shift': lambda char, val, tgt: create_shift_ability(val or 0, char),
        'Puppy Shift': lambda char, val, tgt: create_puppy_shift_ability(val or 0, char),
        'Universal Shift': lambda char, val, tgt: create_universal_shift_ability(val or 0, char),
        'Challenger': lambda char, val, tgt: create_challenger_ability(val or 1, char),
        'Reckless': lambda char, val, tgt: create_reckless_ability(char),
        'Vanish': lambda char, val, tgt: create_vanish_ability(char),
        'Sing Together': lambda char, val, tgt: create_sing_together_ability(val or 1, char),
    }
    
    if keyword not in keyword_factories:
        raise ValueError(f"Unknown keyword ability: {keyword}")
    
    return keyword_factories[keyword](character, value, target_name)


# =============================================================================
# ADVANCED COMPOSABLE ABILITIES (Examples of complex combinations)
# =============================================================================

def create_combined_ability_example(character: Any) -> ComposableAbility:
    """Example of a complex ability combining multiple triggers and effects."""
    ability = ComposableAbility("Complex Example", character)
    
    # When enters play, draw a card
    ability.add_trigger(
        when_enters_play(character),
        SELF,
        StatModification("lore", 1, "this_turn"),
        name="Enters Play Bonus"
    )
    
    # When takes damage, deal damage back to attacker
    ability.add_trigger(
        when_takes_damage(character),
        EVENT_TARGET,  # The attacker
        StatModification("damage", 1),
        name="Revenge"
    )
    
    return ability


def create_scaling_ability_example(character: Any) -> ComposableAbility:
    """Example of an ability that scales with game state."""
    def scaling_condition(event_context):
        return when_quests(character)(event_context)
    
    # Add event introspection
    scaling_condition.get_relevant_events = lambda: [GameEvent.CHARACTER_QUESTS]
    
    def scaling_effect_factory():
        def scaling_effect(target, context):
            # Give lore equal to the number of friendly characters
            game_state = context.get('game_state')
            if game_state and hasattr(character, 'controller'):
                friendly_count = len(character.controller.characters_in_play)
                lore_effect = StatModification("lore", friendly_count, "this_turn")
                return lore_effect.apply(target, context)
            return target
        
        class ScalingEffect:
            def apply(self, target, context):
                return scaling_effect(target, context)
            
            def __str__(self):
                return "lore equal to friendly character count"
        
        return ScalingEffect()
    
    return quick_ability(
        name="Scaling Ability",
        character=character,
        trigger_condition=scaling_condition,
        target_selector=SELF,
        effect=scaling_effect_factory()
    )





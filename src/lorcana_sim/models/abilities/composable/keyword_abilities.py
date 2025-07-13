"""Composable implementations of all existing keyword abilities."""

from typing import Any
from .composable_ability import ComposableAbility, quick_ability
from .effects import (
    StatModification, PreventEffect, ModifyDamage, ForceRetarget, 
    ModifySongCost, GrantProperty, NoEffect, ConditionalEffect
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
# BODYGUARD ABILITY - Force challenge redirection
# =============================================================================

def create_bodyguard_ability(character: Any) -> ComposableAbility:
    """Bodyguard - Opponents must challenge this character if able.
    
    Implementation: When an opponent challenges another friendly character,
    and this character is ready, redirect to this character.
    """
    def bodyguard_condition(event_context):
        # Check if it's a challenge against a friendly character
        if not when_event(GameEvent.CHARACTER_CHALLENGES)(event_context):
            return False
        
        # Check if target is friendly to bodyguard
        target = event_context.target
        if not target or target.controller != character.controller:
            return False
        
        # Check if target is not the bodyguard itself
        if target == character:
            return False
        
        # Check if bodyguard is ready
        if character.exerted:
            return False
        
        # Check if challenger is an opponent
        challenger = event_context.source
        if not challenger or challenger.controller == character.controller:
            return False
        
        return True
    
    return quick_ability(
        name="Bodyguard",
        character=character,
        trigger_condition=bodyguard_condition,
        target_selector=NO_TARGET,
        effect=ForceRetarget()
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
    
    return quick_ability(
        name=f"Singer {cost}",
        character=character,
        trigger_condition=singer_condition,
        target_selector=SELF,
        effect=ModifySongCost(cost)
    )


# =============================================================================
# SUPPORT ABILITY - When quests, give lore bonus to another character
# =============================================================================

def create_support_ability(value: int, character: Any) -> ComposableAbility:
    """Support X - When another friendly character quests, they get +X lore this turn.
    
    Implementation: When any friendly character (other than this one) quests,
    that character gets +X lore this turn.
    """
    
    def support_condition(event_context):
        """Trigger when any friendly character (except this one) quests."""
        # Check if it's a quest event
        if not when_event(GameEvent.CHARACTER_QUESTS)(event_context):
            return False
        
        # Check if the questing character is friendly to the support character
        questing_character = event_context.source
        if not questing_character or not hasattr(questing_character, 'controller'):
            return False
        
        if not hasattr(character, 'controller') or questing_character.controller != character.controller:
            return False
        
        # Check if the questing character is NOT the support character itself
        if questing_character == character:
            return False
        
        return True
    
    # Target the character who is questing (the event source)
    return quick_ability(
        name=f"Support {value}",
        character=character,
        trigger_condition=support_condition,
        target_selector=EVENT_SOURCE,  # Target the questing character
        effect=StatModification("lore", value, "this_turn")
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
# CONVENIENCE FUNCTIONS FOR ALL ABILITIES
# =============================================================================

def create_keyword_ability(keyword: str, character: Any, value: int = None) -> ComposableAbility:
    """Create any keyword ability by name."""
    
    keyword_factories = {
        'Resist': lambda char, val: create_resist_ability(val or 1, char),
        'Ward': lambda char, val: create_ward_ability(char),
        'Bodyguard': lambda char, val: create_bodyguard_ability(char),
        'Evasive': lambda char, val: create_evasive_ability(char),
        'Singer': lambda char, val: create_singer_ability(val or 4, char),
        'Support': lambda char, val: create_support_ability(val or 1, char),
        'Rush': lambda char, val: create_rush_ability(char),
    }
    
    if keyword not in keyword_factories:
        raise ValueError(f"Unknown keyword ability: {keyword}")
    
    return keyword_factories[keyword](character, value)


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


# =============================================================================
# COMPATIBILITY ADAPTER FOR EXISTING KEYWORD REGISTRY
# =============================================================================

class ComposableKeywordRegistry:
    """Registry that creates composable versions of keyword abilities."""
    
    @staticmethod
    def create_keyword_ability(keyword: str, value: int = None) -> Any:
        """Create a keyword ability factory function."""
        def factory(character):
            return create_keyword_ability(keyword, character, value)
        return factory
    
    @staticmethod
    def get_available_keywords() -> list[str]:
        """Get list of available keyword names."""
        return ['Resist', 'Ward', 'Bodyguard', 'Evasive', 'Singer', 'Support', 'Rush']


# =============================================================================
# BULK CONVERSION UTILITIES
# =============================================================================

def convert_all_character_abilities(character: Any) -> list[ComposableAbility]:
    """Convert all of a character's existing abilities to composable format."""
    composable_abilities = []
    
    if not hasattr(character, 'abilities'):
        return composable_abilities
    
    for ability in character.abilities:
        if hasattr(ability, 'name'):
            # Try to convert known keyword abilities
            ability_name = ability.name
            value = getattr(ability, 'value', None)
            
            try:
                composable = create_keyword_ability(ability_name, character, value)
                composable_abilities.append(composable)
            except ValueError:
                # Unknown ability, skip for now
                # In a full implementation, we'd have more conversion logic
                pass
    
    return composable_abilities


def register_composable_abilities_with_character(character: Any, event_manager: Any = None):
    """Convert a character's abilities to composable format and register them."""
    composable_abilities = convert_all_character_abilities(character)
    
    # Replace the character's abilities with composable versions
    character.composable_abilities = composable_abilities
    
    # Register with event manager if provided
    if event_manager:
        for ability in composable_abilities:
            ability.register_with_event_manager(event_manager)
    
    return composable_abilities
"""Composable ability system."""

# Core classes
from .composable_ability import ComposableAbility, ComposableListener, AbilityBuilder, ability, quick_ability
from .effects import (
    Effect, CompositeEffect, RepeatedEffect, ChoiceEffect, ConditionalEffect,
    StatModification, DrawCards, BanishCharacter, ReturnToHand, PreventEffect,
    ModifyDamage, ForceRetarget, ModifySongCost, GrantProperty, NoEffect,
    # Pre-built effects
    LORE_PLUS_1, LORE_PLUS_2, LORE_PLUS_3,
    STRENGTH_PLUS_1, STRENGTH_PLUS_2, STRENGTH_PLUS_3,
    WILLPOWER_PLUS_1, WILLPOWER_PLUS_2, WILLPOWER_PLUS_3,
    DAMAGE_1, DAMAGE_2, DAMAGE_3,
    HEAL_1, HEAL_2, HEAL_3,
    DRAW_1, DRAW_2, DRAW_3,
    BANISH, RETURN_TO_HAND, PREVENT_TARGETING, NO_EFFECT
)
from .target_selectors import (
    TargetSelector, CharacterSelector, SelfSelector, NoTargetSelector,
    EventTargetSelector, EventSourceSelector, UnionSelector, DifferenceSelector, IntersectionSelector,
    # Filter functions
    friendly_filter, enemy_filter, ready_filter, exerted_filter, damaged_filter, undamaged_filter,
    has_ability_filter, cost_filter, subtype_filter, not_self_filter, bodyguard_filter,
    and_filters, or_filters, not_filter,
    # Pre-built selectors
    SELF, EVENT_TARGET, EVENT_SOURCE, NO_TARGET,
    FRIENDLY_CHARACTER, FRIENDLY_READY, FRIENDLY_EXERTED, FRIENDLY_DAMAGED, ALL_FRIENDLY, OTHER_FRIENDLY,
    ENEMY_CHARACTER, ENEMY_EXERTED, ENEMY_DAMAGED, ALL_ENEMIES,
    DAMAGED_CHARACTER, ALL_CHARACTERS, ALL_OTHER_CHARACTERS, BODYGUARD_CHARACTER
)
from .triggers import (
    when_event, when_quests, when_any_quests, when_challenges, when_any_challenges,
    when_enters_play, when_any_enters_play, when_leaves_play, when_banished,
    when_takes_damage, when_deals_damage, when_any_takes_damage,
    when_song_sung, when_action_played, when_song_played,
    when_turn_begins, when_turn_ends, when_ready_step,
    when_card_drawn, when_ink_played, when_lore_gained, when_item_played,
    when_targeted_by_ability, when_challenge_declared_against, when_damage_would_be_dealt_to,
    when_song_cast_attempted, and_conditions, or_conditions, not_condition, metadata_condition
)

# Import named abilities to register them
from . import named_abilities

__all__ = [
    # Core classes
    'ComposableAbility', 'ComposableListener', 'AbilityBuilder', 'ability', 'quick_ability',
    
    # Effects
    'Effect', 'CompositeEffect', 'RepeatedEffect', 'ChoiceEffect', 'ConditionalEffect',
    'StatModification', 'DrawCards', 'BanishCharacter', 'ReturnToHand', 'PreventEffect',
    'ModifyDamage', 'ForceRetarget', 'ModifySongCost', 'GrantProperty', 'NoEffect',
    'LORE_PLUS_1', 'LORE_PLUS_2', 'LORE_PLUS_3',
    'STRENGTH_PLUS_1', 'STRENGTH_PLUS_2', 'STRENGTH_PLUS_3',
    'WILLPOWER_PLUS_1', 'WILLPOWER_PLUS_2', 'WILLPOWER_PLUS_3',
    'DAMAGE_1', 'DAMAGE_2', 'DAMAGE_3',
    'HEAL_1', 'HEAL_2', 'HEAL_3',
    'DRAW_1', 'DRAW_2', 'DRAW_3',
    'BANISH', 'RETURN_TO_HAND', 'PREVENT_TARGETING', 'NO_EFFECT',
    
    # Target selectors
    'TargetSelector', 'CharacterSelector', 'SelfSelector', 'NoTargetSelector',
    'EventTargetSelector', 'EventSourceSelector', 'UnionSelector', 'DifferenceSelector', 'IntersectionSelector',
    'friendly_filter', 'enemy_filter', 'ready_filter', 'exerted_filter', 'damaged_filter', 'undamaged_filter',
    'has_ability_filter', 'cost_filter', 'subtype_filter', 'not_self_filter', 'bodyguard_filter',
    'and_filters', 'or_filters', 'not_filter',
    'SELF', 'EVENT_TARGET', 'EVENT_SOURCE', 'NO_TARGET',
    'FRIENDLY_CHARACTER', 'FRIENDLY_READY', 'FRIENDLY_EXERTED', 'FRIENDLY_DAMAGED', 'ALL_FRIENDLY', 'OTHER_FRIENDLY',
    'ENEMY_CHARACTER', 'ENEMY_EXERTED', 'ENEMY_DAMAGED', 'ALL_ENEMIES',
    'DAMAGED_CHARACTER', 'ALL_CHARACTERS', 'ALL_OTHER_CHARACTERS', 'BODYGUARD_CHARACTER',
    
    # Triggers
    'when_event', 'when_quests', 'when_any_quests', 'when_challenges', 'when_any_challenges',
    'when_enters_play', 'when_any_enters_play', 'when_leaves_play', 'when_banished',
    'when_takes_damage', 'when_deals_damage', 'when_any_takes_damage',
    'when_song_sung', 'when_action_played', 'when_song_played',
    'when_turn_begins', 'when_turn_ends', 'when_ready_step',
    'when_card_drawn', 'when_ink_played', 'when_lore_gained', 'when_item_played',
    'when_targeted_by_ability', 'when_challenge_declared_against', 'when_damage_would_be_dealt_to',
    'when_song_cast_attempted', 'and_conditions', 'or_conditions', 'not_condition', 'metadata_condition'
]
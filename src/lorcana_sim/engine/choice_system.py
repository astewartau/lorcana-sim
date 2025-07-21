"""
Player choice system for abilities that require decisions ("may" effects).

This system allows the game to pause when a player needs to make a choice,
return control to the caller, and resume after receiving input.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union
from enum import Enum
from abc import ABC, abstractmethod

from ..models.abilities.composable.effects import Effect, NoEffect
from ..utils.logging_config import get_game_logger

logger = get_game_logger(__name__)

class ChoiceType(Enum):
    """Types of choices players can make."""
    YES_NO = "yes_no"                    # Simple yes/no choice
    SELECT_FROM_LIST = "select_from_list"  # Choose from a list of options
    SELECT_TARGETS = "select_targets"     # Choose game targets (characters, etc.)
    CUSTOM = "custom"                     # Custom choice with validation


@dataclass
class ChoiceOption:
    """Represents a single choice option."""
    id: str                              # Unique identifier for this option
    description: str                     # Human-readable description
    effect: Effect                       # Effect to execute if chosen
    target: Any = None                   # Target to apply effect to (overrides original trigger target)
    data: Dict[str, Any] = field(default_factory=dict)  # Additional data


@dataclass
class ChoiceContext:
    """Context information for a player choice."""
    choice_id: str                       # Unique ID for this choice instance
    player: Any                          # Player making the choice
    ability_name: str                    # Name of ability requiring choice
    prompt: str                          # Question/prompt for the player
    choice_type: ChoiceType             # Type of choice
    options: List[ChoiceOption]         # Available options
    trigger_context: Dict[str, Any]     # Original trigger context
    timeout_seconds: Optional[int] = None  # Optional timeout
    default_option: Optional[str] = None   # Default if no choice made


class PlayerChoice(Effect):
    """Effect that requires player input before execution."""
    
    def __init__(self, 
                 prompt: str,
                 yes_effect: Effect,
                 no_effect: Effect = None,
                 ability_name: str = "Unknown",
                 timeout_seconds: Optional[int] = None):
        """
        Create a player choice effect.
        
        Args:
            prompt: Question to ask the player
            yes_effect: Effect to execute if player chooses "yes"
            no_effect: Effect to execute if player chooses "no" (defaults to NoEffect)
            ability_name: Name of the ability requiring this choice
            timeout_seconds: Optional timeout for the choice
        """
        self.prompt = prompt
        self.yes_effect = yes_effect
        self.no_effect = no_effect or NoEffect()
        self.ability_name = ability_name
        self.timeout_seconds = timeout_seconds
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Apply the choice effect - this will pause the game and wait for input."""
        choice_manager = context.get('choice_manager')
        if not choice_manager:
            # Fallback: if no choice manager, default to "yes"
            return self.yes_effect.apply(target, context)
        
        # Create choice context
        choice_context = ChoiceContext(
            choice_id=choice_manager.generate_choice_id(),
            player=context.get('player') or getattr(target, 'controller', None),
            ability_name=self.ability_name,
            prompt=self.prompt,
            choice_type=ChoiceType.YES_NO,
            options=[
                ChoiceOption("yes", "Yes", self.yes_effect),
                ChoiceOption("no", "No", self.no_effect)
            ],
            trigger_context=context,
            timeout_seconds=self.timeout_seconds,
            default_option="no"  # Default to "no" for "may" effects
        )
        
        # Queue the choice and pause the game
        choice_manager.queue_choice(choice_context, target, context)
        return target  # Return target unchanged - actual effect happens after choice
    
    def __str__(self) -> str:
        return f"Player Choice: {self.prompt}"


class SelectFromListChoice(Effect):
    """Effect that lets player select from a list of options."""
    
    def __init__(self,
                 prompt: str,
                 options: List[ChoiceOption],
                 ability_name: str = "Unknown",
                 allow_none: bool = True,
                 timeout_seconds: Optional[int] = None):
        """
        Create a list selection choice.
        
        Args:
            prompt: Question to ask the player
            options: List of available choices
            ability_name: Name of the ability requiring this choice
            allow_none: Whether player can choose not to select anything
            timeout_seconds: Optional timeout
        """
        self.prompt = prompt
        self.options = options.copy()
        self.ability_name = ability_name
        self.allow_none = allow_none
        self.timeout_seconds = timeout_seconds
        
        if allow_none:
            self.options.append(ChoiceOption("none", "Choose nothing", NoEffect()))
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Apply the list choice effect."""
        choice_manager = context.get('choice_manager')
        if not choice_manager:
            # Fallback: if no choice manager, choose first option or none
            if self.allow_none:
                return target
            elif self.options:
                return self.options[0].effect.apply(target, context)
            return target
        
        choice_context = ChoiceContext(
            choice_id=choice_manager.generate_choice_id(),
            player=context.get('player') or getattr(target, 'controller', None),
            ability_name=self.ability_name,
            prompt=self.prompt,
            choice_type=ChoiceType.SELECT_FROM_LIST,
            options=self.options,
            trigger_context=context,
            timeout_seconds=self.timeout_seconds,
            default_option="none" if self.allow_none else None
        )
        
        choice_manager.queue_choice(choice_context, target, context)
        return target


class SelectCharacterChoice(Effect):
    """Effect that lets player select a character from those available."""
    
    def __init__(self,
                 prompt: str,
                 character_filter: Callable[[Any], bool],
                 effect_on_selected: Effect,
                 ability_name: str = "Unknown",
                 allow_none: bool = True,
                 from_play: bool = True,
                 from_hand: bool = False,
                 controller_characters: bool = True,
                 opponent_characters: bool = False):
        """
        Create a character selection choice.
        
        Args:
            prompt: Question to ask the player
            character_filter: Function to filter which characters are selectable
            effect_on_selected: Effect to apply to the selected character
            ability_name: Name of the ability requiring this choice
            allow_none: Whether player can choose not to select anything
            from_play: Include characters in play
            from_hand: Include characters in hand
            controller_characters: Include controller's characters
            opponent_characters: Include opponent's characters
        """
        self.prompt = prompt
        self.character_filter = character_filter
        self.effect_on_selected = effect_on_selected
        self.ability_name = ability_name
        self.allow_none = allow_none
        self.from_play = from_play
        self.from_hand = from_hand
        self.controller_characters = controller_characters
        self.opponent_characters = opponent_characters
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Apply the character selection choice."""
        choice_manager = context.get('choice_manager')
        game_state = context.get('game_state')
        ability_owner = context.get('ability_owner')
        
        if not choice_manager or not game_state:
            return target
        
        # Find available characters
        available_characters = []
        # Use the player from context if specified (for effects like GROWING POWERS where opponents choose)
        # Otherwise fall back to ability owner's controller
        controller = context.get('player') or (ability_owner.controller if ability_owner else None)
        
        for player in game_state.players:
            # Check if we should include this player's characters
            include_player = False
            if controller:
                if player == controller and self.controller_characters:
                    include_player = True
                elif player != controller and self.opponent_characters:
                    include_player = True
            
            if include_player:
                # Add characters from play
                if self.from_play:
                    for char in player.characters_in_play:
                        if self.character_filter(char):
                            available_characters.append(char)
                
                # Add characters from hand
                if self.from_hand:
                    for card in player.hand:
                        if hasattr(card, 'strength') and self.character_filter(card):
                            available_characters.append(card)
        
        # Create choice options
        options = []
        for i, char in enumerate(available_characters):
            char_name = f"{char.name} ({char.strength}/{char.willpower})"
            if hasattr(char, 'damage') and char.damage > 0:
                char_name += f" [-{char.damage}]"
            
            # Create effect that applies the chosen effect to this specific character
            class CharacterTargetEffect(Effect):
                def __init__(self, selected_char, base_effect):
                    self.selected_char = selected_char
                    self.base_effect = base_effect
                
                def apply(self, target, context):
                    return self.base_effect.apply(self.selected_char, context)
                
                def get_events(self, target, context, result):
                    """Forward events from the base effect."""
                    if hasattr(self.base_effect, 'get_events'):
                        return self.base_effect.get_events(self.selected_char, context, result)
                    return []
                
                def __str__(self):
                    return f"Apply to {self.selected_char.name}"
            
            options.append(ChoiceOption(
                f"char_{i}",
                char_name,
                CharacterTargetEffect(char, self.effect_on_selected),
                {"character": char}
            ))
        
        if not options:
            # No valid targets
            return target
        
        if self.allow_none:
            options.append(ChoiceOption("none", "Choose no character", NoEffect()))
        
        choice_context = ChoiceContext(
            choice_id=choice_manager.generate_choice_id(),
            player=context.get('player') or controller,
            ability_name=self.ability_name,
            prompt=self.prompt,
            choice_type=ChoiceType.SELECT_TARGETS,
            options=options,
            trigger_context=context,
            default_option="none" if self.allow_none else None
        )
        
        choice_manager.queue_choice(choice_context, target, context)
        return target
    
    def __str__(self) -> str:
        return f"Select character: {self.prompt}"


class SelectCardChoice(Effect):
    """Effect that lets player select a card from their hand."""
    
    def __init__(self,
                 prompt: str,
                 card_filter: Callable[[Any], bool],
                 effect_on_selected: Effect,
                 ability_name: str = "Unknown",
                 allow_none: bool = True,
                 from_hand: bool = True,
                 from_discard: bool = False):
        """
        Create a card selection choice.
        
        Args:
            prompt: Question to ask the player
            card_filter: Function to filter which cards are selectable
            effect_on_selected: Effect to apply to the selected card
            ability_name: Name of the ability requiring this choice
            allow_none: Whether player can choose not to select anything
            from_hand: Include cards from hand
            from_discard: Include cards from discard pile
        """
        self.prompt = prompt
        self.card_filter = card_filter
        self.effect_on_selected = effect_on_selected
        self.ability_name = ability_name
        self.allow_none = allow_none
        self.from_hand = from_hand
        self.from_discard = from_discard
    
    def apply(self, target: Any, context: Dict[str, Any]) -> Any:
        """Apply the card selection choice."""
        choice_manager = context.get('choice_manager')
        ability_owner = context.get('ability_owner')
        
        if not choice_manager:
            return target
        
        controller = ability_owner.controller if ability_owner else getattr(target, 'controller', None)
        if not controller:
            return target
        
        # Find available cards
        available_cards = []
        
        if self.from_hand:
            for card in controller.hand:
                if self.card_filter(card):
                    available_cards.append(card)
        
        if self.from_discard:
            for card in controller.discard_pile:
                if self.card_filter(card):
                    available_cards.append(card)
        
        # Create choice options
        options = []
        for i, card in enumerate(available_cards):
            card_name = f"{card.name}"
            if hasattr(card, 'cost'):
                card_name += f" ({card.cost} ink)"
            
            # Store the card directly as the target for this option
            options.append(ChoiceOption(
                f"card_{i}",
                card_name,
                self.effect_on_selected,  # Use original effect directly
                target=card,              # Store card as target
                data={"card": card}
            ))
        
        if not options:
            # No valid targets
            return target
        
        if self.allow_none:
            options.append(ChoiceOption("none", "Choose no card", NoEffect()))
        
        choice_context = ChoiceContext(
            choice_id=choice_manager.generate_choice_id(),
            player=controller,
            ability_name=self.ability_name,
            prompt=self.prompt,
            choice_type=ChoiceType.SELECT_FROM_LIST,
            options=options,
            trigger_context=context,
            default_option="none" if self.allow_none else None
        )
        
        choice_manager.queue_choice(choice_context, target, context)
        return target
    
    def __str__(self) -> str:
        return f"Select card: {self.prompt}"


class GameChoiceManager:
    """Manages player choices and game pausing/resuming."""
    
    def __init__(self):
        self.pending_choices: List[ChoiceContext] = []
        self.choice_counter: int = 0
        self.game_paused: bool = False
        self.current_choice: Optional[ChoiceContext] = None
        self.choice_results: Dict[str, Any] = {}
    
    def generate_choice_id(self) -> str:
        """Generate a unique choice ID."""
        self.choice_counter += 1
        return f"choice_{self.choice_counter}"
    
    def queue_choice(self, choice_context: ChoiceContext, target: Any, context: Dict[str, Any]) -> None:
        """Queue a choice and pause the game."""
        # Store the target and context for later execution
        choice_context.trigger_context['_choice_target'] = target
        choice_context.trigger_context['_choice_execution_context'] = context
        
        self.pending_choices.append(choice_context)
        self.game_paused = True
        
        # Set as current choice if it's the first one
        if not self.current_choice:
            self.current_choice = choice_context
    
    def get_current_choice(self) -> Optional[ChoiceContext]:
        """Get the current choice that needs player input."""
        return self.current_choice
    
    def has_pending_choices(self) -> bool:
        """Check if there are choices waiting for player input."""
        return len(self.pending_choices) > 0
    
    def is_game_paused(self) -> bool:
        """Check if the game is paused for player choices."""
        return self.game_paused
    
    def provide_choice(self, choice_id: str, selected_option: str) -> bool:
        """
        Provide a player's choice and execute the effect.
        
        Args:
            choice_id: ID of the choice being answered
            selected_option: ID of the selected option
            
        Returns:
            True if choice was valid and executed, False otherwise
        """
        if not self.current_choice or self.current_choice.choice_id != choice_id:
            return False
        
        # Find the selected option
        selected_effect = None
        selected_target = None
        for option in self.current_choice.options:
            if option.id == selected_option:
                selected_effect = option.effect
                selected_target = option.target  # Use option's target if specified
                logger.debug("Found selected option {selected_option}: target={selected_target}, effect={selected_effect}")
                break
        
        if selected_effect is None:
            return False
        
        # Execute the chosen effect
        # Use option.target if specified, otherwise fall back to original trigger target
        target = selected_target if selected_target is not None else self.current_choice.trigger_context.get('_choice_target')
        context = self.current_choice.trigger_context.get('_choice_execution_context', {})
        
        logger.debug("Choice execution - selected_target: {selected_target}")
        logger.debug("Choice execution - fallback _choice_target: {self.current_choice.trigger_context.get('_choice_target')}")
        logger.debug("Choice execution - final target: {target}")
        
        if target is not None:
            # Update the trigger context to replace _choice_target with the selected target
            if '_choice_target' in self.current_choice.trigger_context:
                logger.debug("Updating _choice_target from {self.current_choice.trigger_context['_choice_target']} to {selected_target}")
                self.current_choice.trigger_context['_choice_target'] = selected_target
            
            # Check if we have an ActionQueue available in the context
            action_queue = context.get('action_queue')
            if action_queue and hasattr(action_queue, 'enqueue'):
                # Use ActionQueue for atomic execution
                from .action_queue import ActionPriority
                action_queue.enqueue(
                    selected_effect,
                    target,
                    context,
                    ActionPriority.HIGH,  # Choice-selected effects should run with high priority
                    f"Choice: {self.current_choice.ability_name}"
                )
            else:
                # No action queue available - this should not happen in normal operation
                # Log error but don't execute directly to maintain architectural integrity
                print(f"WARNING: No ActionQueue available for choice resolution. Effect not executed.")
                print(f"Context keys: {list(context.keys()) if context else 'None'}")
        
        # Store the result
        self.choice_results[choice_id] = {
            'selected_option': selected_option,
            'choice_context': self.current_choice
        }
        
        # Remove this choice and move to next
        self.pending_choices.remove(self.current_choice)
        self.current_choice = self.pending_choices[0] if self.pending_choices else None
        
        # Unpause if no more choices
        if not self.pending_choices:
            self.game_paused = False
        
        return True
    
    def auto_resolve_with_defaults(self) -> int:
        """
        Auto-resolve all pending choices with their default options.
        Returns the number of choices resolved.
        """
        resolved = 0
        while self.pending_choices:
            choice = self.current_choice
            if choice and choice.default_option:
                self.provide_choice(choice.choice_id, choice.default_option)
                resolved += 1
            else:
                # No default - skip this choice
                self.pending_choices.remove(choice)
                self.current_choice = self.pending_choices[0] if self.pending_choices else None
        
        self.game_paused = False
        return resolved
    
    def clear_all_choices(self) -> None:
        """Clear all pending choices and resume the game."""
        self.pending_choices.clear()
        self.current_choice = None
        self.game_paused = False
    
    def get_choice_result(self, choice_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a completed choice."""
        return self.choice_results.get(choice_id)


# =============================================================================
# FACTORY FUNCTIONS FOR COMMON CHOICE PATTERNS
# =============================================================================

def may_effect(prompt: str, effect: Effect, ability_name: str = "Unknown") -> PlayerChoice:
    """Create a 'may' choice - player can choose to apply effect or not."""
    return PlayerChoice(prompt, effect, NoEffect(), ability_name)

def choose_one_effect(prompt: str, options: List[ChoiceOption], ability_name: str = "Unknown") -> SelectFromListChoice:
    """Create a 'choose one' effect from a list of options."""
    return SelectFromListChoice(prompt, options, ability_name, allow_none=False)

def may_choose_one_effect(prompt: str, options: List[ChoiceOption], ability_name: str = "Unknown") -> SelectFromListChoice:
    """Create a 'may choose one' effect - player can select an option or choose nothing."""
    return SelectFromListChoice(prompt, options, ability_name, allow_none=True)

def choose_character_effect(prompt: str, character_filter: Callable[[Any], bool], effect_on_selected: Effect, ability_name: str = "Unknown", **kwargs) -> SelectCharacterChoice:
    """Create a character selection choice."""
    return SelectCharacterChoice(prompt, character_filter, effect_on_selected, ability_name, **kwargs)

def may_choose_character_effect(prompt: str, character_filter: Callable[[Any], bool], effect_on_selected: Effect, ability_name: str = "Unknown", **kwargs) -> SelectCharacterChoice:
    """Create a 'may choose character' effect."""
    return SelectCharacterChoice(prompt, character_filter, effect_on_selected, ability_name, allow_none=True, **kwargs)

def choose_card_effect(prompt: str, card_filter: Callable[[Any], bool], effect_on_selected: Effect, ability_name: str = "Unknown", **kwargs) -> SelectCardChoice:
    """Create a card selection choice."""
    return SelectCardChoice(prompt, card_filter, effect_on_selected, ability_name, allow_none=False, **kwargs)

def may_choose_card_effect(prompt: str, card_filter: Callable[[Any], bool], effect_on_selected: Effect, ability_name: str = "Unknown", **kwargs) -> SelectCardChoice:
    """Create a 'may choose card' effect."""
    return SelectCardChoice(prompt, card_filter, effect_on_selected, ability_name, allow_none=True, **kwargs)
"""Character card implementation."""

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING, Dict, Any, Tuple

from .base_card import Card

if TYPE_CHECKING:
    from ...engine.damage_calculator import DamageCalculator, DamageType
    from ..game.game_state import GameState
    from ...engine.event_system import GameEventManager
    from ..abilities.composable import ComposableAbility
    from ..abilities.composable.conditional_effects import ConditionalEffect
    from ..game.player import Player


@dataclass
class CharacterCard(Card):
    """Represents a character card in Lorcana."""
    
    # Combat Stats (from JSON)
    strength: int = 0
    willpower: int = 0
    lore: int = 0
    
    # Character Classification
    subtypes: List[str] = field(default_factory=list)
    
    # Runtime State (not from JSON - game state)
    damage: int = 0
    exerted: bool = False
    is_dry: bool = True  # Ink drying status - True means ready to act
    location: Optional[str] = None
    turn_played: Optional[int] = None  # Track when character was played for ink drying
    
    # Composable Ability Integration
    composable_abilities: List['ComposableAbility'] = field(default_factory=list)
    conditional_effects: List['ConditionalEffect'] = field(default_factory=list)
    controller: Optional['Player'] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Stat Bonus Tracking (for abilities like Support)
    lore_bonuses: List[Tuple[int, str]] = field(default_factory=list)
    strength_bonuses: List[Tuple[int, str]] = field(default_factory=list)
    willpower_bonuses: List[Tuple[int, str]] = field(default_factory=list)
    challenger_bonuses: List[Tuple[int, str]] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate character card data after creation."""
        super().__post_init__()
        
        if self.strength < 0:
            raise ValueError(f"Character strength cannot be negative: {self.strength}")
        if self.willpower < 0:
            raise ValueError(f"Character willpower cannot be negative: {self.willpower}")
        if self.lore < 0:
            raise ValueError(f"Character lore cannot be negative: {self.lore}")
        if self.damage < 0:
            raise ValueError(f"Character damage cannot be negative: {self.damage}")
    
    @property
    def is_alive(self) -> bool:
        """Check if character is still alive (damage < willpower)."""
        return self.damage < self.willpower
    
    @property
    def current_strength(self) -> int:
        """Get current strength including ability modifiers."""
        base = self.strength
        # Add bonuses
        for amount, duration in self.strength_bonuses:
            base += amount
        return max(0, base)
    
    @property
    def current_willpower(self) -> int:
        """Get current willpower including ability modifiers."""
        base = self.willpower
        # Add bonuses  
        for amount, duration in self.willpower_bonuses:
            base += amount
        return max(1, base)  # Willpower must be at least 1
    
    @property
    def current_lore(self) -> int:
        """Get current lore value including ability modifiers."""
        base = self.lore
        # Add bonuses
        for amount, duration in self.lore_bonuses:
            base += amount
        return max(0, base)
    
    @property
    def current_challenger_bonus(self) -> int:
        """Get current challenger bonus."""
        return sum(amount for amount, duration in self.challenger_bonuses)
    
    def deal_damage(self, 
                   amount: int, 
                   source: Optional['CharacterCard'] = None,
                   damage_calculator: Optional['DamageCalculator'] = None,
                   damage_type: Optional['DamageType'] = None) -> int:
        """Deal damage to this character with ability modifications.
        
        Args:
            amount: Base damage amount
            source: Character dealing the damage (None for non-character sources)
            damage_calculator: Calculator to apply ability modifiers
            damage_type: Type of damage being dealt
            
        Returns:
            Actual damage dealt after ability modifications
        """
        if amount < 0:
            raise ValueError("Damage amount cannot be negative")
        
        if amount == 0:
            return 0
        
        # If no damage calculator provided, use simple damage
        if damage_calculator is None or damage_type is None:
            self.damage += amount
            return amount
        
        # Calculate final damage with ability modifications
        final_damage = damage_calculator.calculate_damage(source, self, amount, damage_type)
        
        # Apply the calculated damage
        self.damage += final_damage
        
        return final_damage
    
    def heal_damage(self, amount: int) -> None:
        """Heal damage from this character."""
        if amount < 0:
            raise ValueError("Heal amount cannot be negative")
        self.damage = max(0, self.damage - amount)
    
    def exert(self) -> None:
        """Exert this character."""
        self.exerted = True
    
    def ready(self) -> None:
        """Ready this character."""
        self.exerted = False
    
    
    def has_rush_ability(self) -> bool:
        """Check if character has Rush ability."""
        # Check composable abilities for Rush
        for ability in self.composable_abilities:
            if 'rush' in ability.name.lower():
                return True
        # Check metadata set by Rush ability
        return self.metadata.get('can_challenge_with_wet_ink', False)
    
    def has_evasive_ability(self) -> bool:
        """Check if character has Evasive ability."""
        # Check composable abilities for Evasive
        for ability in self.composable_abilities:
            if 'evasive' in ability.name.lower():
                return True
        # Check metadata set by temporary effects
        return self.metadata.get('has_evasive', False)
    
    def can_quest(self, current_turn: int) -> bool:
        """Check if this character can quest.
        
        Questing requires dry ink - Rush does not affect questing.
        """
        return not self.exerted and self.is_alive and self.is_dry
    
    def can_challenge(self, current_turn: int) -> bool:
        """Check if this character can challenge.
        
        Challenging normally requires dry ink, but Rush bypasses this restriction.
        """
        if not self.is_alive or self.exerted:
            return False
        
        # Rush bypasses ink drying requirement for challenges
        if self.has_rush_ability():
            return True
        
        # Normal characters need dry ink to challenge
        return self.is_dry
    
    def has_subtype(self, subtype: str) -> bool:
        """Check if this character has a specific subtype."""
        return subtype in self.subtypes
    
    def get_origin_type(self) -> Optional[str]:
        """Get the origin type (Storyborn, Dreamborn, Floodborn)."""
        origin_types = {"Storyborn", "Dreamborn", "Floodborn"}
        for subtype in self.subtypes:
            if subtype in origin_types:
                return subtype
        return None
    
    def __str__(self) -> str:
        """String representation including stats."""
        status = ""
        if self.exerted:
            status += " [EXERTED]"
        if self.damage > 0:
            status += f" [{self.damage} damage]"
        return f"{self.full_name} ({self.strength}/{self.willpower}){status}"
    
    # Stat Bonus Management Methods
    def add_lore_bonus(self, amount: int, duration: str) -> None:
        """Add a lore bonus to this character."""
        self.lore_bonuses.append((amount, duration))
    
    def add_strength_bonus(self, amount: int, duration: str) -> None:
        """Add a strength bonus to this character.""" 
        self.strength_bonuses.append((amount, duration))
    
    def add_willpower_bonus(self, amount: int, duration: str) -> None:
        """Add a willpower bonus to this character."""
        self.willpower_bonuses.append((amount, duration))
    
    def add_challenger_bonus(self, amount: int, duration: str) -> None:
        """Add a challenger bonus to this character."""
        self.challenger_bonuses.append((amount, duration))
    
    def add_temporary_modifier(self, **kwargs) -> None:
        """Add temporary modifiers to this character."""
        duration = kwargs.get('duration', 'turn')
        
        if 'strength' in kwargs:
            self.add_strength_bonus(kwargs['strength'], duration)
        if 'willpower' in kwargs:
            self.add_willpower_bonus(kwargs['willpower'], duration)
        if 'lore' in kwargs:
            self.add_lore_bonus(kwargs['lore'], duration)
        if 'challenger_bonus' in kwargs:
            self.add_challenger_bonus(kwargs['challenger_bonus'], duration)
        if 'evasive' in kwargs:
            self.metadata['has_evasive'] = kwargs['evasive']
        if 'rush' in kwargs:
            self.metadata['has_rush'] = kwargs['rush']
        if 'bodyguard' in kwargs:
            self.metadata['has_bodyguard'] = kwargs['bodyguard']
        if 'ward' in kwargs:
            self.metadata['has_ward'] = kwargs['ward']
    
    def clear_temporary_bonuses(self, game_state=None) -> List[Dict]:
        """Clear all 'this_turn' bonuses at end of turn and return list of expired effects."""
        expired_effects = []
        
        # Track what we're removing for messaging - aggregate same bonus types
        challenger_total = 0
        for amount, duration in self.challenger_bonuses:
            if duration in ["this_turn", "turn"]:
                challenger_total += amount
        
        if challenger_total > 0:
            expired_effects.append({
                'type': 'EFFECT_EXPIRED',
                'target': self.name,
                'effect_type': 'challenger_bonus',
                'effect_value': challenger_total,
                'reason': 'end of turn',
                'timestamp': getattr(game_state, 'turn_number', 0) * 1000 + getattr(game_state, '_event_counter', 0) if game_state else 0
            })
        
        for amount, duration in self.strength_bonuses:
            if duration in ["this_turn", "turn"]:
                expired_effects.append({
                    'type': 'EFFECT_EXPIRED',
                    'target': self.name,
                    'effect_type': 'strength_bonus',
                    'effect_value': amount,
                    'reason': 'end of turn',
                    'timestamp': getattr(game_state, 'turn_number', 0) * 1000 + getattr(game_state, '_event_counter', 0) if game_state else 0
                })
        
        for amount, duration in self.willpower_bonuses:
            if duration in ["this_turn", "turn"]:
                expired_effects.append({
                    'type': 'EFFECT_EXPIRED',
                    'target': self.name,
                    'effect_type': 'willpower_bonus',
                    'effect_value': amount,
                    'reason': 'end of turn',
                    'timestamp': getattr(game_state, 'turn_number', 0) * 1000 + getattr(game_state, '_event_counter', 0) if game_state else 0
                })
                
        for amount, duration in self.lore_bonuses:
            if duration in ["this_turn", "turn"]:
                expired_effects.append({
                    'type': 'EFFECT_EXPIRED',
                    'target': self.name,
                    'effect_type': 'lore_bonus',
                    'effect_value': amount,
                    'reason': 'end of turn',
                    'timestamp': getattr(game_state, 'turn_number', 0) * 1000 + getattr(game_state, '_event_counter', 0) if game_state else 0
                })
        
        # Actually remove the temporary bonuses
        self.lore_bonuses = [(amount, duration) for amount, duration in self.lore_bonuses if duration not in ["this_turn", "turn"]]
        self.strength_bonuses = [(amount, duration) for amount, duration in self.strength_bonuses if duration not in ["this_turn", "turn"]]
        self.willpower_bonuses = [(amount, duration) for amount, duration in self.willpower_bonuses if duration not in ["this_turn", "turn"]]
        self.challenger_bonuses = [(amount, duration) for amount, duration in self.challenger_bonuses if duration not in ["this_turn", "turn"]]
        
        return expired_effects
    
    # Composable Ability Integration Methods
    def register_composable_abilities(self, event_manager: 'GameEventManager') -> None:
        """Register all composable abilities with the event manager."""
        for ability in self.composable_abilities:
            ability.register_with_event_manager(event_manager)
    
    def unregister_composable_abilities(self, event_manager: 'GameEventManager') -> None:
        """Unregister all composable abilities from the event manager."""
        for ability in self.composable_abilities:
            ability.unregister_from_event_manager()
    
    def add_composable_ability(self, ability: 'ComposableAbility') -> None:
        """Add a composable ability to this character."""
        self.composable_abilities.append(ability)
    
    # Conditional Effect Management Methods
    def add_conditional_effect(self, effect: 'ConditionalEffect') -> None:
        """Add a conditional effect to this character."""
        self.conditional_effects.append(effect)
    
    def remove_conditional_effect(self, effect_id: str) -> Optional['ConditionalEffect']:
        """Remove a conditional effect by ID and return it if found."""
        for i, effect in enumerate(self.conditional_effects):
            if effect.effect_id == effect_id:
                return self.conditional_effects.pop(i)
        return None
    
    def get_conditional_effect(self, effect_id: str) -> Optional['ConditionalEffect']:
        """Get a conditional effect by ID."""
        for effect in self.conditional_effects:
            if effect.effect_id == effect_id:
                return effect
        return None
    
    def get_active_conditional_effects(self) -> List['ConditionalEffect']:
        """Get all currently active conditional effects."""
        return [effect for effect in self.conditional_effects if effect.is_active]
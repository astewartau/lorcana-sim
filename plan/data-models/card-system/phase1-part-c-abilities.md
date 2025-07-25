# Phase 1 Part C: Ability System Foundation

## Overview

**Critical Understanding**: The lorcana-json format provides human-readable ability descriptions (e.g., "This character can't ⟳ to sing songs") but no machine-executable logic. We must implement all ability behaviors ourselves.

**Current Status After Parts A & B**:
- ✅ Ability structure and parsing from `abilities` JSON array  
- ✅ `keywordAbilities` array parsing (599 keyword instances now parsed)
- ✅ Keyword registry system with factory pattern
- ✅ 8/14 keyword abilities implemented (Singer, Evasive, Bodyguard, Shift, Support, Ward, Rush, Resist)
- ✅ Game state integration for ability execution
- ✅ Event system for triggered abilities
- ✅ Comprehensive testing framework (254 tests)
- ❌ Remaining 6 keyword abilities (Challenger, Reckless, Sing Together, Vanish, Puppy Shift, Universal Shift)
- ❌ Named ability pattern matching system

**Dependencies**: Part B (Game State Foundation) has been completed - all ability execution systems are functional.

**Scope Analysis**:
- **14 unique keywords**: Singer, Evasive, Bodyguard, Shift, Ward, Rush, Resist, Challenger, Support, Sing Together, Reckless, Vanish, Puppy Shift, Universal Shift
- **1190+ unique named abilities**: Requires pattern-based approach
- **4 ability types**: keyword, triggered, static, activated

## Implementation Plan

### C1: Fix keywordAbilities Parsing Gap ✅ COMPLETED

**Status**: Successfully implemented - CardFactory now parses both the `abilities` JSON array and the `keywordAbilities` array.

**Files to Modify:**
- `src/lorcana_sim/models/cards/card_factory.py`

**Data Structure Analysis**:
```json
// Example from Ariel - Spectacular Singer
"keywordAbilities": ["Singer"],
"abilities": [
  {
    "fullText": "Singer 5 (This character counts as cost 5 to sing songs.)",
    "keyword": "Singer", 
    "keywordValue": "5",
    "keywordValueNumber": 5,
    "reminderText": "This character counts as cost 5 to sing songs.",
    "type": "keyword"
  }
]
```

**Implementation Strategy**:
```python
@staticmethod
def _parse_abilities(card_data: Dict[str, Any]) -> List[Ability]:
    """Parse abilities from both abilities and keywordAbilities arrays"""
    abilities = []
    
    # Parse structured abilities array (existing logic)
    for ability_data in card_data.get('abilities', []):
        # ... existing parsing logic ...
    
    # Parse keywordAbilities array (NEW)
    keywords_from_array = set(card_data.get('keywordAbilities', []))
    keywords_from_abilities = set()
    
    # Track which keywords already have structured data
    for ability in abilities:
        if hasattr(ability, 'keyword') and ability.keyword:
            keywords_from_abilities.add(ability.keyword)
    
    # Add missing keywords from keywordAbilities array
    missing_keywords = keywords_from_array - keywords_from_abilities
    for keyword_name in missing_keywords:
        abilities.append(KeywordAbility(
            name=keyword_name,
            type=AbilityType.KEYWORD,
            effect=f'{keyword_name} keyword ability',
            full_text='',
            keyword=keyword_name,
            value=None
        ))
    
    return abilities
```

### C2: Ability Enumeration and Analysis Tools ✅ COMPLETED

**Status**: Successfully implemented - Comprehensive ability analysis and enumeration tools created.

**Files to Enhance:**
- `examples/demo_enumeration.py` (already exists, needs expansion)

**Files to Create:**
- `src/lorcana_sim/utils/ability_analyzer.py`

**AbilityAnalyzer Implementation**:
```python
from typing import Dict, List, Any, Set, DefaultDict
from collections import defaultdict, Counter
import re

class AbilityAnalyzer:
    """Tool for analyzing and cataloging all abilities in the database"""
    
    def __init__(self, card_database: List[Dict[str, Any]]):
        self.cards = card_database
        self.keyword_catalog = {}
        self.named_abilities = {}
        self.ability_patterns = defaultdict(list)
        self._analyze_abilities()
    
    def _analyze_abilities(self):
        """Analyze all abilities and categorize them"""
        for card_data in self.cards:
            card_name = card_data.get('fullName', 'Unknown')
            
            # Analyze keywords
            for keyword in card_data.get('keywordAbilities', []):
                if keyword not in self.keyword_catalog:
                    self.keyword_catalog[keyword] = {
                        'count': 0,
                        'examples': [],
                        'values': set(),
                        'cards': []
                    }
                
                self.keyword_catalog[keyword]['count'] += 1
                self.keyword_catalog[keyword]['cards'].append(card_name)
                
                # Find structured data for this keyword
                for ability in card_data.get('abilities', []):
                    if (ability.get('type') == 'keyword' and 
                        ability.get('keyword') == keyword):
                        value = ability.get('keywordValueNumber')
                        if value is not None:
                            self.keyword_catalog[keyword]['values'].add(value)
                        break
            
            # Analyze named abilities
            for ability in card_data.get('abilities', []):
                ability_name = ability.get('name', '')
                if ability_name and ability.get('type') != 'keyword':
                    if ability_name not in self.named_abilities:
                        self.named_abilities[ability_name] = {
                            'count': 0,
                            'effect_text': ability.get('effect', ''),
                            'type': ability.get('type', 'unknown'),
                            'cards': [],
                            'pattern_group': None
                        }
                    
                    self.named_abilities[ability_name]['count'] += 1
                    self.named_abilities[ability_name]['cards'].append(card_name)
    
    def get_keyword_summary(self) -> Dict[str, Dict]:
        """Get summary of all keywords with usage statistics"""
        return self.keyword_catalog
    
    def get_named_abilities_by_pattern(self) -> Dict[str, List[str]]:
        """Group named abilities by common effect patterns"""
        patterns = {
            'draw_cards': r'draw \d+ card|look at.*top.*card|reveal.*card',
            'deal_damage': r'deal \d+ damage|damage.*equal',
            'modify_stats': r'gets \+\d+|\+\d+ strength|\+\d+ willpower|\+\d+ lore',
            'conditional': r'if you have|while you have|as long as',
            'quest_effects': r'when.*quest|whenever.*quest',
            'play_effects': r'when you play|when.*played|enters play',
            'challenge_effects': r'when.*challeng|whenever.*challeng',
            'sing_effects': r'sing|song',
            'search_effects': r'search your deck|look at.*deck',
            'cost_reduction': r'costs? \d+ less|pay \d+ less'
        }
        
        grouped = defaultdict(list)
        
        for ability_name, data in self.named_abilities.items():
            effect_text = data['effect_text'].lower()
            matched = False
            
            for pattern_name, pattern in patterns.items():
                if re.search(pattern, effect_text):
                    grouped[pattern_name].append(ability_name)
                    matched = True
                    break
            
            if not matched:
                grouped['uncategorized'].append(ability_name)
        
        return dict(grouped)
    
    def export_ability_catalog(self, output_file: str) -> None:
        """Export complete ability catalog for implementation reference"""
        import json
        
        catalog = {
            'keywords': self.keyword_catalog,
            'named_abilities': self.named_abilities,
            'patterns': self.get_named_abilities_by_pattern(),
            'statistics': {
                'total_keywords': len(self.keyword_catalog),
                'total_named_abilities': len(self.named_abilities),
                'total_cards': len(self.cards)
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(catalog, f, indent=2, default=str)
    
    def get_implementation_priority(self) -> Dict[str, List[str]]:
        """Suggest implementation priority based on usage frequency"""
        # Sort keywords by frequency
        keywords_by_freq = sorted(
            self.keyword_catalog.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        # Sort named abilities by frequency  
        named_by_freq = sorted(
            self.named_abilities.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        return {
            'high_priority_keywords': [k for k, data in keywords_by_freq[:5]],
            'medium_priority_keywords': [k for k, data in keywords_by_freq[5:10]],
            'low_priority_keywords': [k for k, data in keywords_by_freq[10:]],
            'high_priority_named': [k for k, data in named_by_freq[:20]],
            'pattern_groups': list(self.get_named_abilities_by_pattern().keys())
        }
```

### C3: Keyword Ability Implementations 🔄 IN PROGRESS (8/14 Complete)

**Status**: Major progress - 8 out of 14 keyword abilities fully implemented with comprehensive testing.

**Completed**: Singer, Evasive, Bodyguard, Shift, Support, Ward, Rush, Resist
**Remaining**: Challenger, Reckless, Sing Together, Vanish, Puppy Shift, Universal Shift

**Files to Create:**
- `src/lorcana_sim/abilities/keywords/__init__.py`
- `src/lorcana_sim/abilities/keywords/base_keyword.py`
- `src/lorcana_sim/abilities/keywords/singer.py`
- `src/lorcana_sim/abilities/keywords/evasive.py`
- `src/lorcana_sim/abilities/keywords/bodyguard.py`
- `src/lorcana_sim/abilities/keywords/shift.py`
- `src/lorcana_sim/abilities/keywords/ward.py`
- `src/lorcana_sim/abilities/keywords/rush.py`
- `src/lorcana_sim/abilities/keywords/resist.py`
- `src/lorcana_sim/abilities/keywords/challenger.py`
- `src/lorcana_sim/abilities/keywords/support.py`
- `src/lorcana_sim/abilities/keywords/sing_together.py`
- `src/lorcana_sim/abilities/keywords/reckless.py`
- `src/lorcana_sim/abilities/keywords/vanish.py`

**Keyword Registry System**:
```python
# src/lorcana_sim/abilities/keywords/__init__.py
from typing import Dict, Type, Optional
from ..base_ability import KeywordAbility

class KeywordRegistry:
    """Registry of all keyword ability implementations"""
    
    _implementations: Dict[str, Type[KeywordAbility]] = {}
    
    @classmethod
    def register(cls, keyword: str, implementation: Type[KeywordAbility]):
        """Register a keyword implementation"""
        cls._implementations[keyword] = implementation
    
    @classmethod
    def get_implementation(cls, keyword: str) -> Type[KeywordAbility]:
        """Get the implementation class for a keyword"""
        return cls._implementations.get(keyword, UnknownKeywordAbility)
    
    @classmethod
    def create_keyword_ability(cls, keyword: str, value: Optional[int] = None, 
                             **kwargs) -> KeywordAbility:
        """Factory method to create keyword ability instances"""
        impl_class = cls.get_implementation(keyword)
        return impl_class(
            name=keyword,
            type=AbilityType.KEYWORD,
            effect=f'{keyword} keyword ability',
            full_text=kwargs.get('full_text', ''),
            keyword=keyword,
            value=value
        )

# Auto-register implementations
from .singer import SingerAbility
from .evasive import EvasiveAbility
from .bodyguard import BodyguardAbility
# ... etc

KeywordRegistry.register('Singer', SingerAbility)
KeywordRegistry.register('Evasive', EvasiveAbility)
KeywordRegistry.register('Bodyguard', BodyguardAbility)
# ... etc
```

**Example Implementation: Singer**:
```python
# src/lorcana_sim/abilities/keywords/singer.py
from typing import Optional, TYPE_CHECKING
from ..base_ability import KeywordAbility, AbilityType

if TYPE_CHECKING:
    from ...models.game.game_state import GameState
    from ...models.cards.action_card import ActionCard

class SingerAbility(KeywordAbility):
    """Singer X - This character counts as cost X to sing songs"""
    
    def can_activate(self, game_state: 'GameState') -> bool:
        """Singer is a passive ability, doesn't activate"""
        return False
    
    def get_effective_sing_cost(self) -> int:
        """Get the cost this character counts as for singing"""
        return self.value or 0
    
    def can_sing_song(self, song: 'ActionCard') -> bool:
        """Check if this character can sing the given song"""
        if not song.is_song:
            return False
        
        required_cost = song.singer_cost_reduction
        if required_cost is None:
            return False
        
        return self.get_effective_sing_cost() >= required_cost
    
    def get_cost_reduction(self, song: 'ActionCard') -> int:
        """Get the cost reduction when singing a song"""
        if self.can_sing_song(song):
            return song.cost  # Singer allows singing for free
        return 0
    
    def execute(self, game_state: 'GameState', targets: List[Any]) -> None:
        """Singer doesn't execute, it modifies song-playing rules"""
        pass
    
    def __str__(self) -> str:
        return f"Singer {self.value}" if self.value else "Singer"
```

**Example Implementation: Evasive**:
```python  
# src/lorcana_sim/abilities/keywords/evasive.py
class EvasiveAbility(KeywordAbility):
    """Evasive - Only characters with Evasive can challenge this character"""
    
    def can_be_challenged_by(self, challenger: 'CharacterCard') -> bool:
        """Check if the given character can challenge this evasive character"""
        # Check if challenger has evasive
        for ability in challenger.abilities:
            if (hasattr(ability, 'keyword') and 
                ability.keyword == 'Evasive'):
                return True
        return False
    
    def modifies_challenge_rules(self) -> bool:
        """This ability modifies who can challenge this character"""
        return True
    
    def execute(self, game_state: 'GameState', targets: List[Any]) -> None:
        """Evasive is a passive ability that modifies challenge rules"""
        pass
```

### C4: Ability Execution Engine ✅ COMPLETED

**Status**: Successfully implemented - Full ability execution engine with event system and game state integration.

**Files to Create:**
- `src/lorcana_sim/engine/ability_engine.py`
- `src/lorcana_sim/engine/events.py`
- `src/lorcana_sim/engine/triggers.py`

**Event System**:
```python
# src/lorcana_sim/engine/events.py
from dataclasses import dataclass
from typing import Any, Optional
from ..models.cards.base_card import Card
from ..models.cards.character_card import CharacterCard
from ..models.game.player import Player

@dataclass
class GameEvent:
    """Base class for game events that can trigger abilities"""
    pass

@dataclass
class CardPlayedEvent(GameEvent):
    """Triggered when a card is played"""
    card: Card
    player: Player

@dataclass
class CharacterQuestsEvent(GameEvent):
    """Triggered when a character quests"""
    character: CharacterCard
    player: Player
    location: Optional[str] = None

@dataclass
class CharacterChallengedEvent(GameEvent):
    """Triggered when a character is challenged"""
    attacker: CharacterCard
    defender: CharacterCard
    attacker_player: Player
    defender_player: Player

@dataclass
class DamageDealtEvent(GameEvent):
    """Triggered when damage is dealt"""
    target: Any  # Could be character, player, location
    amount: int
    source: Optional[Any] = None

@dataclass
class TurnStartEvent(GameEvent):
    """Triggered at the start of a turn"""
    player: Player
    turn_number: int

@dataclass
class TurnEndEvent(GameEvent):
    """Triggered at the end of a turn"""
    player: Player
    turn_number: int
```

**Ability Engine**:
```python
# src/lorcana_sim/engine/ability_engine.py
from typing import Dict, List, Type, DefaultDict
from collections import defaultdict
from .events import GameEvent
from ..models.abilities.base_ability import Ability, TriggeredAbility

class AbilityEngine:
    """Manages ability execution and event handling"""
    
    def __init__(self, game_state):
        self.game_state = game_state
        self.event_listeners: DefaultDict[Type[GameEvent], List[TriggeredAbility]] = defaultdict(list)
        self.static_abilities: List[Ability] = []
        self.resolution_stack: List[Ability] = []
    
    def register_card(self, card: Card):
        """Register all abilities from a card"""
        for ability in card.abilities:
            if isinstance(ability, TriggeredAbility):
                # Determine which events this ability listens to
                trigger_events = self._parse_trigger_events(ability)
                for event_type in trigger_events:
                    self.event_listeners[event_type].append(ability)
            elif ability.type == AbilityType.STATIC:
                self.static_abilities.append(ability)
    
    def unregister_card(self, card: Card):
        """Remove all abilities from a card (when it leaves play)"""
        for ability in card.abilities:
            if isinstance(ability, TriggeredAbility):
                for event_listeners in self.event_listeners.values():
                    if ability in event_listeners:
                        event_listeners.remove(ability)
            elif ability in self.static_abilities:
                self.static_abilities.remove(ability)
    
    def _parse_trigger_events(self, ability: TriggeredAbility) -> List[Type[GameEvent]]:
        """Parse ability text to determine which events it triggers on"""
        trigger_text = ability.trigger_condition.lower()
        events = []
        
        if 'when you play' in trigger_text or 'when this character enters play' in trigger_text:
            events.append(CardPlayedEvent)
        if 'when' in trigger_text and 'quest' in trigger_text:
            events.append(CharacterQuestsEvent)
        if 'when' in trigger_text and 'challeng' in trigger_text:
            events.append(CharacterChallengedEvent)
        if 'when' in trigger_text and 'damage' in trigger_text:
            events.append(DamageDealtEvent)
        
        return events
    
    def trigger_event(self, event: GameEvent):
        """Process an event and trigger relevant abilities"""
        event_type = type(event)
        triggered_abilities = []
        
        # Find all abilities that trigger on this event
        for ability in self.event_listeners[event_type]:
            if self._ability_triggers_for_event(ability, event):
                triggered_abilities.append(ability)
        
        # Add to resolution stack (LIFO order)
        for ability in triggered_abilities:
            self.resolution_stack.append(ability)
        
        # Resolve the stack
        self._resolve_stack()
    
    def _ability_triggers_for_event(self, ability: TriggeredAbility, event: GameEvent) -> bool:
        """Check if an ability should trigger for the given event"""
        # Check if the ability can activate in current game state
        if not ability.can_activate(self.game_state):
            return False
        
        # TODO: Add more sophisticated trigger condition checking
        # For now, assume any registered ability triggers
        return True
    
    def _resolve_stack(self):
        """Resolve all abilities in the resolution stack"""
        while self.resolution_stack:
            ability = self.resolution_stack.pop()
            try:
                # TODO: Handle targeting, costs, etc.
                ability.execute(self.game_state, [])
            except Exception as e:
                print(f"Error executing ability {ability.name}: {e}")
    
    def get_static_modifiers(self, target: Any, modifier_type: str) -> int:
        """Get the total modification from static abilities"""
        total_modifier = 0
        for ability in self.static_abilities:
            # TODO: Check if ability affects the target
            # For now, return 0
            pass
        return total_modifier
```

### C5: Named Ability Framework ⏸️ READY FOR IMPLEMENTATION

**Status**: Ready to implement - Part B and C4 are complete, foundation exists for named ability patterns.

**Files to Create:**
- `src/lorcana_sim/abilities/named/__init__.py`
- `src/lorcana_sim/abilities/named/pattern_matcher.py`
- `src/lorcana_sim/abilities/named/effect_templates.py`
- `src/lorcana_sim/abilities/named/common_effects.py`

**Pattern Matcher**:
```python
# src/lorcana_sim/abilities/named/pattern_matcher.py
import re
from typing import Optional, List, Tuple, Type
from .effect_templates import *

class AbilityPatternMatcher:
    """Matches ability text to common patterns and creates effect implementations"""
    
    PATTERNS: List[Tuple[str, Type['EffectTemplate']]] = [
        # Draw effects
        (r'draw (\d+) cards?', DrawCardsEffect),
        (r'draw a card', lambda m, t: DrawCardsEffect(1)),
        (r'look at the top (\d+) cards?', LookAtTopCardsEffect),
        
        # Damage effects
        (r'deal (\d+) damage to (.+)', TargetedDamageEffect),
        (r'deal (\d+) damage to each (.+)', DamageAllEffect),
        
        # Lore effects
        (r'gain (\d+) lore', GainLoreEffect),
        (r'gets \+(\d+) lore', ModifyLoreEffect),
        
        # Search effects
        (r'search your deck for (.+)', SearchDeckEffect),
        
        # Cost reduction
        (r'costs? (\d+) less', CostReductionEffect),
        (r'pay (\d+) less', CostReductionEffect),
    ]
    
    def match_ability_text(self, ability_text: str) -> Optional['EffectTemplate']:
        """Try to match ability text to a known pattern"""
        for pattern_str, effect_class in self.PATTERNS:
            match = re.search(pattern_str, ability_text.lower())
            if match:
                if callable(effect_class):
                    return effect_class(match, ability_text)
                else:
                    return effect_class.from_match(match, ability_text)
        return None
    
    def get_unknown_abilities(self, abilities: List[str]) -> List[str]:
        """Return abilities that don't match any known pattern"""
        unknown = []
        for ability_text in abilities:
            if not self.match_ability_text(ability_text):
                unknown.append(ability_text)
        return unknown
```

### C6: Testing Framework ✅ COMPLETED

**Status**: Successfully implemented - Comprehensive testing framework with 254 tests covering all ability systems.

**Files Implemented:**
- `tests/test_ability_parsing.py` ✅
- `tests/test_keyword_abilities.py` ✅
- `tests/test_ability_engine.py` ✅
- `tests/keywords/` directory with individual keyword tests ✅

## Implementation Priority

### ✅ **Phase 1 (Completed)**:
1. ✅ **C1: Fix keywordAbilities parsing** - Foundation requirement
2. ✅ **C2: Enhanced enumeration** - Understand what we're building
3. ✅ **C3: Core keyword implementations** - Singer, Evasive, Bodyguard, Shift, Support, Ward, Rush, Resist (8/14 complete)

### ✅ **Phase 2 (Completed)**:
4. ✅ **Part B: Game State Foundation** - Turn tracking, move validation, game rules
5. ✅ **C4: Basic execution engine** - Events and ability triggering
6. ✅ **C6: Testing framework** - Comprehensive ability testing with 254 tests

### 🔄 **Phase 3 (Current)**:
7. **C3: Remaining keyword implementations** - Complete remaining 6 keywords (Challenger, Reckless, Sing Together, Vanish, Puppy Shift, Universal Shift)

### 🚀 **Phase 4 (Future)**:
8. **C5: Named ability patterns** - Handle common named abilities  
9. **Advanced pattern matching** - Handle complex named abilities
10. **Performance optimization** - Efficient ability checking

## Success Criteria

**Current Status - Part C Major Progress**:
- ✅ 8/14 keywords parsed and functional (57.1% complete)
- ✅ Singer reduces song costs in actual gameplay  
- ✅ Evasive prevents non-evasive challenges
- ✅ Bodyguard forces proper challenge targeting
- ✅ Shift enables alternative play costs
- ✅ Support provides quest-triggered lore bonuses
- ✅ Ward protects from targeted abilities
- ✅ Rush enables immediate challenges
- ✅ Resist reduces damage taken
- ✅ Event-driven triggered abilities work (when played, when challenged)
- ✅ Abilities actually affect game state through Part B's game engine
- ✅ Comprehensive testing framework (254 tests)
- ❌ 6 keywords remaining (Challenger, Reckless, Sing Together, Vanish, Puppy Shift, Universal Shift)
- ❌ Named ability pattern system not yet implemented

This transforms abilities from "decorative data" into "functional game mechanics" that integrate with the game state foundation from Part B.
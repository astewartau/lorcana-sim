#!/usr/bin/env python3
"""
Advanced ability parser to extract structured components from ability text.
"""

import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from pathlib import Path


@dataclass
class AbilityComponent:
    """Represents a parsed component of an ability."""
    type: str  # trigger, condition, effect, target, cost, etc.
    subtype: str  # specific type like "when_played", "damage", "chosen_character"
    value: Union[str, int, List[str]]  # the actual value/text
    modifiers: Dict[str, Any] = field(default_factory=dict)  # additional parameters


@dataclass
class ParsedAbility:
    """Represents a fully parsed ability."""
    name: str
    original_text: str
    ability_type: str  # static, triggered, activated
    components: List[AbilityComponent]
    confidence: float = 1.0  # how confident we are in the parse


class AbilityParser:
    """Parse ability text into structured components."""
    
    def __init__(self):
        self.trigger_patterns = {
            'when_played': [
                r'when you play this character',
                r'when this character (?:is played|enters play)',
            ],
            'when_quests': [
                r'when(?:ever)? this character quests',
                r'when(?:ever)? (?:this character|she|he) quests',
            ],
            'when_challenges': [
                r'when this character challenges',
                r'when (?:this character|she|he) challenges',
            ],
            'when_banished': [
                r'when this character is banished',
                r'when (?:this character|she|he) is banished',
                r'when this character (?:is )?challenged and banished',
            ],
            'when_damaged': [
                r'when this character is (?:challenged and )?damaged',
                r'when (?:this character|she|he) (?:takes|receives) damage',
            ],
            'start_of_turn': [
                r'at the start of your turn',
                r'at the beginning of your turn',
            ],
            'during_turn': [
                r'during your turn',
                r'on your turn',
            ],
            'when_card_inkwelled': [
                r'whenever a card is put into your inkwell',
                r'when you put a card into your inkwell',
            ],
        }
        
        self.condition_patterns = {
            'if_have_character': [
                r'if you have a character named ([^,\s.]+)',
                r'if you have (?:a|an) ([^,\s.]+) character',
                r'if you control (?:a|an) ([^,\s.]+) character',
            ],
            'while_have_character': [
                r'while you have (?:a|an) ([^,\s.]+) character',
                r'while you have (\d+) or more ([^,\s.]+) characters?',
                r'while you have another character',
            ],
            'if_have_cards': [
                r'if you have (\d+) or more cards in your hand',
                r'if you have no cards in your hand',
                r'if you have more cards in your hand than',
            ],
            'if_inkwell_count': [
                r'while you have (\d+) or more cards in your inkwell',
                r'if you have (\d+) or more cards in your inkwell',
            ],
            'if_damaged': [
                r'while (?:this character|she|he) has damage',
                r'if (?:this character|she|he) has no damage',
                r'while another character in play has damage',
            ],
        }
        
        self.effect_patterns = {
            'draw_cards': [
                r'draw (\d+) cards?',
                r'you may draw (?:a card|(\d+) cards?)',
            ],
            'gain_lore': [
                r'gain (\d+) lore',
                r'you gain (\d+) lore',
            ],
            'look_at_deck': [
                r'look at the top (\d+) cards? of your deck',
            ],
            'remove_damage': [
                r'remove up to (\d+) damage from ([^.]+)',
                r'remove (?:up to )?(\d+) damage',
            ],
            'deal_damage': [
                r'deal (\d+) damage to ([^.]+)',
                r'you may deal (\d+) damage',
            ],
            'stat_boost': [
                r'(?:this character |chosen character |)gets \+(\d+) (STRENGTH|WILLPOWER|LORE)',
                r'(?:this character |chosen character |)gets \+(\d+) ⛉',
            ],
            'stat_reduction': [
                r'(?:chosen character |)gets -(\d+) (STRENGTH|WILLPOWER|LORE)',
            ],
            'gain_keyword': [
                r'(?:this character |chosen character |)gains (Evasive|Rush|Bodyguard|Ward|Challenger|Support)',
                r'(?:this character |chosen character |)gains (Resist \+\d+)',
                r'(?:this character |chosen character |)gains (Challenger \+\d+)',
            ],
            'play_for_free': [
                r'play (?:a |an |)([^.]+) for free',
                r'you may play (?:a |an |)([^.]+) for free',
            ],
            'cost_reduction': [
                r'you pay (\d+) INK less to play',
                r'costs? (\d+) less to play',
            ],
            'return_to_hand': [
                r'return (?:a |an |chosen |)([^.]+) to (?:your |their player\'s )?hand',
            ],
            'banish': [
                r'banish (?:the |chosen |)([^.]+)',
                r'you may banish (?:the |chosen |)([^.]+)',
            ],
        }
        
        self.target_patterns = {
            'chosen_character': [
                r'chosen character',
                r'chosen ([^.]+) character',
            ],
            'chosen_opposing': [
                r'chosen opposing character',
                r'chosen opponent',
            ],
            'this_character': [
                r'this character',
                r'(?:she|he)',
            ],
            'your_characters': [
                r'(?:each of )?your ([^.]+) characters?',
                r'your other ([^.]+) characters?',
                r'your characters? named ([^.]+)',
            ],
            'all_characters': [
                r'all characters?',
                r'each character',
            ],
        }
        
    def parse_ability(self, name: str, effect_text: str, ability_type: str) -> ParsedAbility:
        """Parse a single ability into components."""
        components = []
        confidence = 1.0
        
        # Clean the text
        cleaned_text = self._clean_text(effect_text)
        
        # Extract triggers
        triggers = self._extract_triggers(cleaned_text)
        components.extend(triggers)
        
        # Extract conditions
        conditions = self._extract_conditions(cleaned_text)
        components.extend(conditions)
        
        # Extract effects
        effects = self._extract_effects(cleaned_text)
        components.extend(effects)
        
        # Extract targets
        targets = self._extract_targets(cleaned_text)
        components.extend(targets)
        
        # If we couldn't parse much, lower confidence
        if len(components) < 2:
            confidence = 0.5
        
        return ParsedAbility(
            name=name,
            original_text=effect_text,
            ability_type=ability_type,
            components=components,
            confidence=confidence
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Replace symbols
        replacements = {
            '⬡': 'INK',
            '◊': 'STRENGTH', 
            '⟡': 'LORE',
            '¤': 'WILLPOWER',
            '⟳': 'EXERT',
            '⛉': 'LORE',
        }
        
        for symbol, replacement in replacements.items():
            text = text.replace(symbol, replacement)
        
        # Clean whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _extract_triggers(self, text: str) -> List[AbilityComponent]:
        """Extract trigger components."""
        components = []
        
        for trigger_type, patterns in self.trigger_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    components.append(AbilityComponent(
                        type='trigger',
                        subtype=trigger_type,
                        value=match.group(0),
                        modifiers={'start_pos': match.start(), 'end_pos': match.end()}
                    ))
        
        return components
    
    def _extract_conditions(self, text: str) -> List[AbilityComponent]:
        """Extract condition components."""
        components = []
        
        for condition_type, patterns in self.condition_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = match.group(1) if match.groups() else match.group(0)
                    components.append(AbilityComponent(
                        type='condition',
                        subtype=condition_type,
                        value=value,
                        modifiers={'full_match': match.group(0)}
                    ))
        
        return components
    
    def _extract_effects(self, text: str) -> List[AbilityComponent]:
        """Extract effect components."""
        components = []
        
        for effect_type, patterns in self.effect_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if match.groups():
                        # Extract numeric values and targets
                        groups = match.groups()
                        value = groups[0] if groups[0] else match.group(0)
                        modifiers = {}
                        if len(groups) > 1 and groups[1]:
                            modifiers['target'] = groups[1]
                    else:
                        value = match.group(0)
                        modifiers = {}
                    
                    components.append(AbilityComponent(
                        type='effect',
                        subtype=effect_type,
                        value=value,
                        modifiers=modifiers
                    ))
        
        return components
    
    def _extract_targets(self, text: str) -> List[AbilityComponent]:
        """Extract target components."""
        components = []
        
        for target_type, patterns in self.target_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = match.group(1) if match.groups() else match.group(0)
                    components.append(AbilityComponent(
                        type='target',
                        subtype=target_type,
                        value=value,
                        modifiers={'full_match': match.group(0)}
                    ))
        
        return components


def analyze_parsing_results():
    """Analyze how well we can parse the abilities."""
    catalog_path = Path("data/all-cards/ability_catalog.json")
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    parser = AbilityParser()
    
    parsed_abilities = []
    confidence_scores = []
    component_counts = []
    
    for ability_name, ability_data in catalog['named_abilities'].items():
        effect_text = ability_data.get('effect_text', '')
        ability_type = ability_data.get('type', 'unknown')
        
        if effect_text:
            parsed = parser.parse_ability(ability_name, effect_text, ability_type)
            parsed_abilities.append(parsed)
            confidence_scores.append(parsed.confidence)
            component_counts.append(len(parsed.components))
    
    # Analysis
    avg_confidence = sum(confidence_scores) / len(confidence_scores)
    avg_components = sum(component_counts) / len(component_counts)
    
    high_confidence = [p for p in parsed_abilities if p.confidence >= 0.8]
    low_confidence = [p for p in parsed_abilities if p.confidence < 0.5]
    
    print(f"=== PARSING ANALYSIS ===")
    print(f"Total abilities parsed: {len(parsed_abilities)}")
    print(f"Average confidence: {avg_confidence:.2f}")
    print(f"Average components per ability: {avg_components:.1f}")
    print(f"High confidence (≥0.8): {len(high_confidence)} ({len(high_confidence)/len(parsed_abilities)*100:.1f}%)")
    print(f"Low confidence (<0.5): {len(low_confidence)} ({len(low_confidence)/len(parsed_abilities)*100:.1f}%)")
    
    print(f"\n=== EXAMPLE HIGH CONFIDENCE PARSES ===")
    for ability in high_confidence[:5]:
        print(f"\n{ability.name}:")
        print(f"  Original: {ability.original_text}")
        print(f"  Components:")
        for comp in ability.components:
            print(f"    {comp.type}.{comp.subtype}: {comp.value}")
    
    print(f"\n=== EXAMPLE LOW CONFIDENCE PARSES ===")
    for ability in low_confidence[:5]:
        print(f"\n{ability.name}:")
        print(f"  Original: {ability.original_text}")
        print(f"  Components:")
        for comp in ability.components:
            print(f"    {comp.type}.{comp.subtype}: {comp.value}")
    
    # Component type frequency
    component_types = {}
    for ability in parsed_abilities:
        for comp in ability.components:
            key = f"{comp.type}.{comp.subtype}"
            component_types[key] = component_types.get(key, 0) + 1
    
    print(f"\n=== MOST COMMON COMPONENT TYPES ===")
    sorted_types = sorted(component_types.items(), key=lambda x: x[1], reverse=True)
    for comp_type, count in sorted_types[:20]:
        print(f"{count:3d}: {comp_type}")
    
    return parsed_abilities


if __name__ == "__main__":
    analyze_parsing_results()
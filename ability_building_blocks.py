#!/usr/bin/env python3
"""
Generate a structured breakdown of ability building blocks for implementation.
"""

import json
from pathlib import Path
from ability_parser import AbilityParser
from collections import defaultdict, Counter


def generate_ability_taxonomy():
    """Generate a comprehensive taxonomy of ability components."""
    
    catalog_path = Path("data/all-cards/ability_catalog.json")
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    parser = AbilityParser()
    
    # Parse all abilities
    parsed_abilities = []
    for ability_name, ability_data in catalog['named_abilities'].items():
        effect_text = ability_data.get('effect_text', '')
        ability_type = ability_data.get('type', 'unknown')
        
        if effect_text:
            parsed = parser.parse_ability(ability_name, effect_text, ability_type)
            parsed_abilities.append(parsed)
    
    # Build taxonomy
    taxonomy = {
        'triggers': defaultdict(list),
        'conditions': defaultdict(list),
        'effects': defaultdict(list),
        'targets': defaultdict(list),
        'common_patterns': defaultdict(list)
    }
    
    # Collect all components by type
    for ability in parsed_abilities:
        for comp in ability.components:
            key = comp.subtype
            example = {
                'ability': ability.name,
                'value': comp.value,
                'modifiers': comp.modifiers,
                'original_text': ability.original_text
            }
            taxonomy[comp.type + 's'][key].append(example)
    
    # Find common ability patterns (trigger + effect combinations)
    pattern_counter = Counter()
    for ability in parsed_abilities:
        triggers = [c for c in ability.components if c.type == 'trigger']
        effects = [c for c in ability.components if c.type == 'effect']
        
        for trigger in triggers:
            for effect in effects:
                pattern = f"{trigger.subtype} -> {effect.subtype}"
                pattern_counter[pattern] += 1
                
                if pattern_counter[pattern] <= 3:  # Keep first 3 examples
                    taxonomy['common_patterns'][pattern].append({
                        'ability': ability.name,
                        'trigger_value': trigger.value,
                        'effect_value': effect.value,
                        'original_text': ability.original_text
                    })
    
    return taxonomy, pattern_counter


def print_implementation_guide(taxonomy, pattern_counter):
    """Print a guide for implementing the ability system."""
    
    print("=" * 80)
    print("LORCANA ABILITY SYSTEM IMPLEMENTATION GUIDE")
    print("=" * 80)
    
    print("\n1. TRIGGER TYPES")
    print("-" * 40)
    for trigger_type, examples in taxonomy['triggers'].items():
        print(f"\n{trigger_type.upper()} ({len(examples)} abilities)")
        print(f"  Examples: {', '.join([ex['ability'] for ex in examples[:3]])}")
        if examples:
            print(f"  Pattern: '{examples[0]['value']}'")
    
    print("\n2. EFFECT TYPES")
    print("-" * 40)
    for effect_type, examples in taxonomy['effects'].items():
        print(f"\n{effect_type.upper()} ({len(examples)} abilities)")
        print(f"  Examples: {', '.join([ex['ability'] for ex in examples[:3]])}")
        if examples:
            sample_values = [str(ex['value']) for ex in examples[:3]]
            print(f"  Values: {', '.join(sample_values)}")
    
    print("\n3. TARGET TYPES") 
    print("-" * 40)
    for target_type, examples in taxonomy['targets'].items():
        print(f"\n{target_type.upper()} ({len(examples)} abilities)")
        print(f"  Examples: {', '.join([ex['ability'] for ex in examples[:3]])}")
        unique_values = list(set([str(ex['value']) for ex in examples]))[:5]
        if unique_values:
            print(f"  Values: {', '.join(unique_values)}")
    
    print("\n4. CONDITION TYPES")
    print("-" * 40)
    for condition_type, examples in taxonomy['conditions'].items():
        print(f"\n{condition_type.upper()} ({len(examples)} abilities)")
        print(f"  Examples: {', '.join([ex['ability'] for ex in examples[:3]])}")
        if examples:
            print(f"  Pattern: '{examples[0]['value']}'")
    
    print("\n5. MOST COMMON ABILITY PATTERNS")
    print("-" * 40)
    for pattern, count in pattern_counter.most_common(15):
        print(f"{count:3d}: {pattern}")
        if pattern in taxonomy['common_patterns']:
            example = taxonomy['common_patterns'][pattern][0]
            print(f"     Example: {example['ability']}")
    
    print("\n6. IMPLEMENTATION STRATEGY")
    print("-" * 40)
    print("""
PHASE 1 - Core Framework:
- Implement trigger system (when_played, when_quests, when_banished)
- Implement basic effects (draw_cards, gain_lore, stat_boost, remove_damage)
- Implement target system (chosen_character, this_character, your_characters)

PHASE 2 - Common Patterns:
- when_played -> draw_cards (22 abilities)
- when_played -> gain_lore (18 abilities) 
- when_played -> remove_damage (16 abilities)
- when_quests -> gain_lore (15 abilities)
- when_played -> stat_boost (12 abilities)

PHASE 3 - Advanced Features:
- Conditional effects (if_have_character, while_have_character)
- Complex targeting (chosen_opposing, all_characters)
- Keyword granting (gain_keyword)
- Card manipulation (play_for_free, return_to_hand, banish)

PHASE 4 - Edge Cases:
- Multiple triggers per ability
- Complex conditions
- Duration effects
- Replacement effects
    """)


def generate_implementation_json():
    """Generate JSON structure for ability implementation."""
    
    taxonomy, pattern_counter = generate_ability_taxonomy()
    
    # Create implementation structure
    implementation = {
        "ability_framework": {
            "triggers": {},
            "effects": {},
            "targets": {},
            "conditions": {}
        },
        "common_patterns": [],
        "implementation_priority": {
            "phase_1": [],
            "phase_2": [],
            "phase_3": [],
            "phase_4": []
        }
    }
    
    # Populate framework
    for trigger_type, examples in taxonomy['triggers'].items():
        implementation["ability_framework"]["triggers"][trigger_type] = {
            "count": len(examples),
            "description": f"Triggered {trigger_type.replace('_', ' ')}",
            "examples": [ex['ability'] for ex in examples[:3]]
        }
    
    for effect_type, examples in taxonomy['effects'].items():
        implementation["ability_framework"]["effects"][effect_type] = {
            "count": len(examples),
            "description": f"Effect: {effect_type.replace('_', ' ')}",
            "examples": [ex['ability'] for ex in examples[:3]]
        }
    
    for target_type, examples in taxonomy['targets'].items():
        implementation["ability_framework"]["targets"][target_type] = {
            "count": len(examples),
            "description": f"Target: {target_type.replace('_', ' ')}",
            "examples": [ex['ability'] for ex in examples[:3]]
        }
    
    for condition_type, examples in taxonomy['conditions'].items():
        implementation["ability_framework"]["conditions"][condition_type] = {
            "count": len(examples),
            "description": f"Condition: {condition_type.replace('_', ' ')}",
            "examples": [ex['ability'] for ex in examples[:3]]
        }
    
    # Add common patterns
    for pattern, count in pattern_counter.most_common(20):
        implementation["common_patterns"].append({
            "pattern": pattern,
            "count": count,
            "examples": [ex['ability'] for ex in taxonomy['common_patterns'].get(pattern, [])[:3]]
        })
    
    # Prioritize implementation
    high_priority_triggers = ['when_played', 'when_quests', 'when_banished']
    high_priority_effects = ['draw_cards', 'gain_lore', 'stat_boost', 'remove_damage']
    
    implementation["implementation_priority"]["phase_1"] = {
        "triggers": high_priority_triggers,
        "effects": high_priority_effects,
        "targets": ['this_character', 'chosen_character', 'your_characters']
    }
    
    implementation["implementation_priority"]["phase_2"] = {
        "patterns": [p["pattern"] for p in implementation["common_patterns"][:10]]
    }
    
    # Write to file
    output_path = Path("ability_implementation_guide.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(implementation, f, indent=2, ensure_ascii=False)
    
    print(f"\nGenerated implementation guide: {output_path}")
    
    return implementation


if __name__ == "__main__":
    taxonomy, pattern_counter = generate_ability_taxonomy()
    print_implementation_guide(taxonomy, pattern_counter)
    
    print("\n" + "=" * 80)
    implementation = generate_implementation_json()
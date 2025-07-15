#!/usr/bin/env python3
"""
Analyze character targeting patterns in abilities (if you have X named Y, etc.)
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def load_ability_catalog():
    """Load the ability catalog JSON."""
    catalog_path = Path("data/all-cards/ability_catalog.json")
    with open(catalog_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_character_targeting_patterns(text):
    """Extract character targeting patterns from ability text."""
    patterns = {
        'named_character_if': [],      # "If you have a character named X"
        'named_character_while': [],   # "While you have a character named X"
        'character_type_if': [],       # "If you have a Princess character"
        'character_type_while': [],    # "While you have a Villain character"
        'character_count': [],         # "If you have 2 or more characters"
        'specific_subtypes': [],       # "If you have a Puppy character"
        'other_character': [],         # "While you have another character"
    }
    
    # Clean text first
    text = re.sub(r'\([^)]*\)', '', text)  # Remove parenthetical text
    text = ' '.join(text.split()).strip()
    
    # Pattern 1: Named character conditions
    named_patterns = [
        r'if you have a character named ([A-Za-z\s]+?)(?:\s+in play)?[,.]',
        r'while you have a character named ([A-Za-z\s]+?)(?:\s+in play)?[,.]',
        r'if you (?:control|have) a character named ([A-Za-z\s]+?)(?:\s+in play)?[,.]',
    ]
    
    for pattern in named_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            character_name = match.group(1).strip()
            if 'if you have a character named' in match.group(0).lower():
                patterns['named_character_if'].append(character_name)
            elif 'while you have a character named' in match.group(0).lower():
                patterns['named_character_while'].append(character_name)
    
    # Pattern 2: Character type conditions (Princess, Villain, etc.)
    type_patterns = [
        r'if you have (?:a|an) ([A-Za-z]+) character',
        r'while you have (?:a|an) ([A-Za-z]+) character',
        r'if you (?:control|have) (?:a|an) ([A-Za-z]+) character',
    ]
    
    for pattern in type_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            char_type = match.group(1).strip()
            # Skip generic words
            if char_type.lower() not in ['character', 'other', 'another', 'damaged']:
                if 'if you have' in match.group(0).lower():
                    patterns['character_type_if'].append(char_type)
                elif 'while you have' in match.group(0).lower():
                    patterns['character_type_while'].append(char_type)
    
    # Pattern 3: Character count conditions
    count_patterns = [
        r'if you have (\d+) or more ([A-Za-z\s]*?)characters?',
        r'while you have (\d+) or more ([A-Za-z\s]*?)characters?',
        r'if you have (\d+) or more other characters?',
        r'while you have (\d+) or more other characters?',
    ]
    
    for pattern in count_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            count = match.group(1)
            char_type = match.group(2).strip() if len(match.groups()) > 1 else "any"
            patterns['character_count'].append(f"{count}+ {char_type}characters".strip())
    
    # Pattern 4: "Another character" conditions
    other_patterns = [
        r'while you have another character(?:\s+in play)?',
        r'if you have another character(?:\s+in play)?',
        r'while you have (?:an )?other characters?(?:\s+in play)?',
    ]
    
    for pattern in other_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            patterns['other_character'].append(match.group(0))
    
    return patterns


def analyze_character_targeting():
    """Analyze all character targeting patterns in the catalog."""
    catalog = load_ability_catalog()
    
    all_patterns = defaultdict(list)
    ability_examples = defaultdict(list)
    
    for ability_name, ability_data in catalog['named_abilities'].items():
        effect_text = ability_data.get('effect_text', '')
        if not effect_text:
            continue
        
        patterns = extract_character_targeting_patterns(effect_text)
        
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                all_patterns[pattern_type].append(pattern)
                ability_examples[f"{pattern_type}:{pattern}"].append({
                    'ability': ability_name,
                    'text': effect_text
                })
    
    return all_patterns, ability_examples


def print_character_targeting_analysis(all_patterns, ability_examples):
    """Print the character targeting analysis."""
    print("=" * 80)
    print("CHARACTER TARGETING PATTERNS ANALYSIS")
    print("=" * 80)
    
    total_targeting_abilities = 0
    
    for pattern_type, pattern_list in all_patterns.items():
        if pattern_list:
            total_targeting_abilities += len(pattern_list)
            print(f"\n{pattern_type.upper().replace('_', ' ')} ({len(pattern_list)} instances):")
            
            # Count frequency of each specific pattern
            pattern_counts = Counter(pattern_list)
            
            for pattern, count in pattern_counts.most_common():
                print(f"  {count:2d}x: {pattern}")
                
                # Show example abilities
                example_key = f"{pattern_type}:{pattern}"
                if example_key in ability_examples:
                    examples = ability_examples[example_key][:2]  # Show first 2 examples
                    for example in examples:
                        print(f"      → {example['ability']}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total character targeting abilities: {total_targeting_abilities}")
    
    # Most commonly referenced character names
    print(f"\n=== MOST REFERENCED CHARACTER NAMES ===")
    all_named_chars = []
    all_named_chars.extend(all_patterns['named_character_if'])
    all_named_chars.extend(all_patterns['named_character_while'])
    
    name_counts = Counter(all_named_chars)
    for name, count in name_counts.most_common(15):
        print(f"  {count:2d}x: {name}")
    
    # Most commonly referenced character types
    print(f"\n=== MOST REFERENCED CHARACTER TYPES ===")
    all_char_types = []
    all_char_types.extend(all_patterns['character_type_if'])
    all_char_types.extend(all_patterns['character_type_while'])
    
    type_counts = Counter(all_char_types)
    for char_type, count in type_counts.most_common(15):
        print(f"  {count:2d}x: {char_type}")
    
    print(f"\n=== IMPLEMENTATION PATTERNS ===")
    print("""
CHARACTER TARGETING SYSTEM NEEDS:

1. NAMED CHARACTER LOOKUP:
   - Check if player has character with specific name
   - Most common: Gaston, Elsa, Anna, Jafar, Belle
   
2. CHARACTER TYPE LOOKUP:
   - Check if player has character with specific type/subtype
   - Most common: Princess, Villain, Captain, Puppy, Musketeer
   
3. CHARACTER COUNT CONDITIONS:
   - Check if player has X or more characters of type
   - Common patterns: "2 or more", "3 or more"
   
4. GENERIC CONDITIONS:
   - "another character" (any other character)
   - "other characters" (any others)

IMPLEMENTATION APPROACH:
- Player.has_character_named(name: str) -> bool
- Player.has_character_type(type: str) -> bool  
- Player.count_characters_type(type: str) -> int
- Player.has_other_characters() -> bool
    """)


if __name__ == "__main__":
    all_patterns, ability_examples = analyze_character_targeting()
    print_character_targeting_analysis(all_patterns, ability_examples)
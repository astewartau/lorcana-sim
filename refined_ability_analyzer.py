#!/usr/bin/env python3
"""
Refined ability analyzer that normalizes text for better pattern recognition.
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


def clean_and_normalize_text(text):
    """Clean, normalize and standardize text for better pattern matching."""
    # Remove parenthetical reminder text (anything in parentheses)
    text = re.sub(r'\([^)]*\)', '', text)
    
    # Replace unicode symbols
    text = text.replace('⬡', 'INK')
    text = text.replace('◊', 'STRENGTH')
    text = text.replace('⟡', 'LORE')
    text = text.replace('¤', 'WILLPOWER')
    text = text.replace('⟳', 'EXERT')
    text = text.replace('⭳', 'TAP')
    text = text.replace('⛉', 'LORE')
    
    # Replace numbers with X (but be careful about "cost X or less" patterns)
    # Replace standalone numbers or numbers followed by damage/cards/etc
    text = re.sub(r'\b(\d+)\s+(damage|cards?|lore|STRENGTH|WILLPOWER|INK)\b', r'X \2', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(\d+)\s+(STRENGTH|WILLPOWER|LORE|INK)\b', r'X \2', text, flags=re.IGNORECASE)
    text = re.sub(r'(draw|gain|deal|remove up to|look at the top)\s+(\d+)', r'\1 X', text, flags=re.IGNORECASE)
    text = re.sub(r'(\+|-)(\d+)', r'\1X', text)
    
    # Replace gendered pronouns with neutral ones
    # Be careful about word boundaries to avoid changing words like "they" -> "theythey"
    text = re.sub(r'\bhe\b', 'they', text, flags=re.IGNORECASE)
    text = re.sub(r'\bshe\b', 'they', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhis\b', 'their', text, flags=re.IGNORECASE)
    text = re.sub(r'\bher\b', 'their', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhim\b', 'them', text, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    text = ' '.join(text.split())
    text = text.strip()
    
    return text


def split_compound_abilities(text):
    """Split abilities connected by 'and' into separate components."""
    # Look for patterns like "When you play this character and whenever they quest"
    # or "During your turn and whenever you play a character"
    
    # Split on "and" but be smart about it - only split when it connects two full clauses
    parts = []
    
    # Common patterns that indicate compound abilities
    compound_patterns = [
        r'(when you play this character)\s+and\s+(whenever (?:they|this character))',
        r'(when (?:they|this character) (?:quest|challenge|banish))\s+and\s+(when (?:they|this character))',
        r'(during your turn)\s+and\s+(whenever)',
        r'(at the start of your turn)\s+and\s+(whenever)',
    ]
    
    found_compound = False
    for pattern in compound_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            parts.extend([match.group(1).strip(), match.group(2).strip()])
            # Get the rest of the text (everything after the compound trigger)
            rest = text[match.end():].strip()
            if rest:
                parts.append(rest)
            found_compound = True
            break
    
    if not found_compound:
        # Also split on " and " when it separates clauses with different subjects
        and_parts = re.split(r'\s+and\s+', text)
        if len(and_parts) > 1:
            # Check if each part looks like a complete clause
            complete_parts = []
            for part in and_parts:
                part = part.strip()
                # A complete clause usually starts with trigger words or has a verb
                if any(trigger in part.lower() for trigger in ['when', 'whenever', 'if', 'while', 'during', 'at the']):
                    complete_parts.append(part)
                else:
                    # This might be a continuation, combine with previous part
                    if complete_parts:
                        complete_parts[-1] += " and " + part
                    else:
                        complete_parts.append(part)
            
            if len(complete_parts) > 1:
                parts = complete_parts
            else:
                parts = [text]
        else:
            parts = [text]
    
    return [p.strip() for p in parts if p.strip()]


def extract_refined_phrases(text):
    """Extract and normalize phrases from ability text."""
    # Clean and normalize the text
    cleaned = clean_and_normalize_text(text)
    
    # Split compound abilities
    ability_parts = split_compound_abilities(cleaned)
    
    all_phrases = []
    
    for part in ability_parts:
        # Split each part into phrases on sentence boundaries
        phrases = []
        
        # Split on periods and semicolons, but not commas (commas often separate options)
        sentences = re.split(r'[.;]', part)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 3:  # Skip very short fragments
                phrases.append(sentence)
        
        all_phrases.extend(phrases)
    
    return all_phrases


def categorize_refined_phrases(phrases):
    """Categorize phrases with improved pattern matching."""
    categories = {
        'triggers': defaultdict(list),
        'effects': defaultdict(list),
        'conditions': defaultdict(list),
        'targets': defaultdict(list),
        'modifiers': defaultdict(list)
    }
    
    for phrase in phrases:
        lower_phrase = phrase.lower()
        
        # TRIGGERS - Look for timing/event keywords
        if 'when you play this character' in lower_phrase:
            categories['triggers']['when_played'].append(phrase)
        elif 'whenever this character quests' in lower_phrase or 'when this character quests' in lower_phrase:
            categories['triggers']['when_quests'].append(phrase)
        elif 'when this character challenges' in lower_phrase:
            categories['triggers']['when_challenges'].append(phrase)
        elif 'when this character is banished' in lower_phrase:
            categories['triggers']['when_banished'].append(phrase)
        elif 'when this character is challenged' in lower_phrase:
            categories['triggers']['when_challenged'].append(phrase)
        elif 'during your turn' in lower_phrase:
            categories['triggers']['during_turn'].append(phrase)
        elif 'at the start of your turn' in lower_phrase:
            categories['triggers']['start_of_turn'].append(phrase)
        elif 'whenever a card is put into your inkwell' in lower_phrase:
            categories['triggers']['when_inkwelled'].append(phrase)
        
        # CONDITIONS - Look for conditional keywords
        elif any(cond in lower_phrase for cond in ['if you have', 'while you have', 'if you control']):
            if 'character' in lower_phrase:
                categories['conditions']['character_condition'].append(phrase)
            elif 'cards in your hand' in lower_phrase or 'hand' in lower_phrase:
                categories['conditions']['hand_condition'].append(phrase)
            elif 'inkwell' in lower_phrase:
                categories['conditions']['inkwell_condition'].append(phrase)
            else:
                categories['conditions']['other_condition'].append(phrase)
        
        # EFFECTS - Look for action keywords
        elif 'draw' in lower_phrase and 'card' in lower_phrase:
            categories['effects']['draw_cards'].append(phrase)
        elif 'gain' in lower_phrase and 'lore' in lower_phrase:
            categories['effects']['gain_lore'].append(phrase)
        elif 'look at the top' in lower_phrase:
            categories['effects']['look_at_deck'].append(phrase)
        elif 'remove' in lower_phrase and 'damage' in lower_phrase:
            categories['effects']['remove_damage'].append(phrase)
        elif 'deal' in lower_phrase and 'damage' in lower_phrase:
            categories['effects']['deal_damage'].append(phrase)
        elif 'gets +' in lower_phrase or 'gains +' in lower_phrase:
            categories['effects']['stat_boost'].append(phrase)
        elif 'gets -' in lower_phrase:
            categories['effects']['stat_reduction'].append(phrase)
        elif 'gains' in lower_phrase and any(keyword in lower_phrase for keyword in ['evasive', 'rush', 'bodyguard', 'ward', 'challenger']):
            categories['effects']['gain_keyword'].append(phrase)
        elif 'return' in lower_phrase and 'hand' in lower_phrase:
            categories['effects']['return_to_hand'].append(phrase)
        elif 'banish' in lower_phrase:
            categories['effects']['banish'].append(phrase)
        elif 'play' in lower_phrase and ('for free' in lower_phrase or 'cost' in lower_phrase):
            categories['effects']['play_for_free'].append(phrase)
        elif 'ready' in lower_phrase:
            categories['effects']['ready'].append(phrase)
        elif 'exert' in lower_phrase:
            categories['effects']['exert'].append(phrase)
        
        # TARGETS - Look for targeting keywords
        elif 'chosen character' in lower_phrase:
            categories['targets']['chosen_character'].append(phrase)
        elif 'chosen opposing' in lower_phrase:
            categories['targets']['chosen_opposing'].append(phrase)
        elif 'this character' in lower_phrase:
            categories['targets']['this_character'].append(phrase)
        elif 'your characters' in lower_phrase or 'each of your' in lower_phrase:
            categories['targets']['your_characters'].append(phrase)
        elif 'all characters' in lower_phrase:
            categories['targets']['all_characters'].append(phrase)
        
        # MODIFIERS - Duration and scope
        elif 'this turn' in lower_phrase:
            categories['modifiers']['this_turn'].append(phrase)
        elif 'for the rest of this turn' in lower_phrase:
            categories['modifiers']['rest_of_turn'].append(phrase)
        elif 'until' in lower_phrase:
            categories['modifiers']['until_condition'].append(phrase)
    
    return categories


def analyze_refined_abilities():
    """Run the refined analysis on all abilities."""
    catalog = load_ability_catalog()
    
    all_phrases = []
    ability_details = []
    
    # Extract phrases from named abilities
    for ability_name, ability_data in catalog['named_abilities'].items():
        effect_text = ability_data.get('effect_text', '')
        ability_type = ability_data.get('type', 'unknown')
        
        if effect_text:
            # Store original for comparison
            original_phrases = effect_text.split(',')
            
            # Get refined phrases
            refined_phrases = extract_refined_phrases(effect_text)
            all_phrases.extend(refined_phrases)
            
            ability_details.append({
                'name': ability_name,
                'type': ability_type,
                'original': effect_text,
                'refined_phrases': refined_phrases
            })
    
    # Count phrase frequency
    phrase_counts = Counter(all_phrases)
    
    # Categorize phrases
    categorized = categorize_refined_phrases(all_phrases)
    
    return {
        'total_phrases': len(all_phrases),
        'unique_phrases': len(phrase_counts),
        'phrase_counts': phrase_counts,
        'categorized': categorized,
        'ability_details': ability_details
    }


def print_refined_analysis(results):
    """Print the refined analysis results."""
    print("=" * 80)
    print("REFINED LORCANA ABILITY ANALYSIS")
    print("=" * 80)
    
    print(f"Total phrases extracted: {results['total_phrases']}")
    print(f"Unique phrases: {results['unique_phrases']}")
    print()
    
    print("=== MOST COMMON NORMALIZED PHRASES ===")
    for phrase, count in results['phrase_counts'].most_common(30):
        print(f"{count:3d}: {phrase}")
    print()
    
    print("=== REFINED CATEGORIES ===")
    for category, subcategories in results['categorized'].items():
        if subcategories:
            print(f"\n{category.upper()}:")
            for subcat, phrases in subcategories.items():
                if phrases:
                    unique_phrases = list(set(phrases))
                    print(f"  {subcat} ({len(phrases)} total, {len(unique_phrases)} unique):")
                    for phrase in unique_phrases[:5]:  # Show first 5 unique examples
                        print(f"    - {phrase}")
    
    # Show some examples of the compound splitting
    print(f"\n=== COMPOUND ABILITY SPLITTING EXAMPLES ===")
    compound_examples = []
    for ability in results['ability_details']:
        if len(ability['refined_phrases']) > 1 and 'and' in ability['original'].lower():
            compound_examples.append(ability)
            if len(compound_examples) >= 5:
                break
    
    for example in compound_examples:
        print(f"\n{example['name']}:")
        print(f"  Original: {example['original']}")
        print(f"  Split into:")
        for i, phrase in enumerate(example['refined_phrases'], 1):
            print(f"    {i}. {phrase}")


if __name__ == "__main__":
    results = analyze_refined_abilities()
    print_refined_analysis(results)
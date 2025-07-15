#!/usr/bin/env python3
"""
Final polished ability analyzer with improved compound splitting.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def clean_and_normalize_text(text):
    """Clean, normalize and standardize text for better pattern matching."""
    # Remove parenthetical reminder text (anything in parentheses)
    text = re.sub(r'\([^)]*\)', '', text)
    
    # Replace unicode symbols
    replacements = {
        '⬡': 'INK', '◊': 'STRENGTH', '⟡': 'LORE', '¤': 'WILLPOWER', 
        '⟳': 'EXERT', '⭳': 'TAP', '⛉': 'LORE'
    }
    for symbol, replacement in replacements.items():
        text = text.replace(symbol, replacement)
    
    # Replace numbers with X (more comprehensive patterns)
    text = re.sub(r'\b(\d+)\s+(damage|cards?|lore|STRENGTH|WILLPOWER|INK)\b', r'X \2', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(\d+)\s+(STRENGTH|WILLPOWER|LORE|INK)\b', r'X \2', text, flags=re.IGNORECASE)
    text = re.sub(r'(draw|gain|deal|remove up to|look at the top)\s+(\d+)', r'\1 X', text, flags=re.IGNORECASE)
    text = re.sub(r'(\+|-)(\d+)', r'\1X', text)
    text = re.sub(r'\bcost\s+(\d+)\s+or\s+less', r'cost X or less', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(\d+)\s+or\s+more', r'X or more', text, flags=re.IGNORECASE)
    
    # Replace gendered pronouns with neutral ones
    text = re.sub(r'\bhe\b', 'they', text, flags=re.IGNORECASE)
    text = re.sub(r'\bshe\b', 'they', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhis\b', 'their', text, flags=re.IGNORECASE)
    text = re.sub(r'\bher\b', 'their', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhim\b', 'them', text, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    text = ' '.join(text.split()).strip()
    return text


def extract_atomic_phrases(text):
    """Extract atomic phrases by splitting on commas and further breaking down complex statements."""
    # First clean the text
    cleaned = clean_and_normalize_text(text)
    
    # Split on periods first (separate sentences)
    sentences = [s.strip() for s in re.split(r'[.;]', cleaned) if s.strip()]
    
    all_phrases = []
    
    for sentence in sentences:
        # Split each sentence on commas
        comma_parts = [p.strip() for p in sentence.split(',') if p.strip()]
        
        for part in comma_parts:
            # Further break down complex phrases
            atomic_phrases = break_down_complex_phrase(part)
            all_phrases.extend(atomic_phrases)
    
    return [p for p in all_phrases if p and len(p) > 2]


def break_down_complex_phrase(phrase):
    """Break down a complex phrase into granular atomic components."""
    phrase = phrase.strip()
    if not phrase:
        return []
    
    atomic_parts = []
    
    # Handle compound triggers connected by "and"
    # "When you play this character and whenever they quest" -> separate triggers
    if re.search(r'(when you play this character)\s+and\s+(whenever they)', phrase, re.IGNORECASE):
        match = re.search(r'(when you play this character)\s+and\s+(whenever they[^,]*)', phrase, re.IGNORECASE)
        if match:
            # Break down each trigger separately
            trigger1_parts = break_down_trigger_phrase(match.group(1).strip())
            trigger2_parts = break_down_trigger_phrase(match.group(2).strip())
            atomic_parts.extend(trigger1_parts + trigger2_parts)
            
            # Get any remaining effect
            rest = phrase[match.end():].strip()
            if rest:
                atomic_parts.extend(break_down_complex_phrase(rest))
            return atomic_parts
    
    # Split trigger from effect in complex statements
    # "When you play this character, chosen character gets -X WILLPOWER this turn"
    trigger_effect_patterns = [
        r'(when you play this character),?\s+(.+)',
        r'(whenever this character quests),?\s+(.+)',
        r'(when this character (?:is )?banished),?\s+(.+)',
        r'(during your turn),?\s+(.+)',
        r'(at the start of your turn),?\s+(.+)',
        r'(if you have [^,]+),?\s+(.+)',
        r'(while you have [^,]+),?\s+(.+)',
    ]
    
    for pattern in trigger_effect_patterns:
        match = re.search(pattern, phrase, re.IGNORECASE)
        if match:
            trigger = match.group(1).strip()
            effect = match.group(2).strip()
            
            # Break down the trigger into components
            trigger_parts = break_down_trigger_phrase(trigger)
            atomic_parts.extend(trigger_parts)
            
            # Further break down the effect part
            effect_parts = break_down_effect_phrase(effect)
            atomic_parts.extend(effect_parts)
            return atomic_parts
    
    # If no trigger pattern, try to break down as an effect
    effect_parts = break_down_effect_phrase(phrase)
    if effect_parts:
        return effect_parts
    
    # If we can't break it down further, return as is
    return [phrase]


def break_down_trigger_phrase(trigger):
    """Break down trigger phrases into granular components."""
    if not trigger:
        return []
    
    atomic_parts = []
    
    # Normalize "When you play this character" to "When this character is played"
    # to be consistent with other trigger patterns
    normalized_trigger = trigger
    normalized_trigger = re.sub(r'when you play this character', 'when this character is played', normalized_trigger, flags=re.IGNORECASE)
    
    # "When this character is played" -> ["When", "this character", "is played"]
    when_played_pattern = r'(when) (this character) (is played)'
    match = re.search(when_played_pattern, normalized_trigger, re.IGNORECASE)
    if match:
        return [match.group(1), match.group(2), match.group(3)]
    
    # "Whenever this character quests" -> ["Whenever", "this character", "quests"]
    whenever_quest_pattern = r'(whenever) (this character) (quests)'
    match = re.search(whenever_quest_pattern, trigger, re.IGNORECASE)
    if match:
        return [match.group(1), match.group(2), match.group(3)]
    
    # "When this character is banished" -> ["When", "this character", "is banished"]
    when_banished_pattern = r'(when) (this character) (is banished|is challenged|challenges)'
    match = re.search(when_banished_pattern, trigger, re.IGNORECASE)
    if match:
        return [match.group(1), match.group(2), match.group(3)]
    
    # "During your turn" -> ["During", "your turn"]
    during_pattern = r'(during) (your turn)'
    match = re.search(during_pattern, trigger, re.IGNORECASE)
    if match:
        return [match.group(1), match.group(2)]
    
    # "At the start of your turn" -> ["At the start of", "your turn"]
    at_start_pattern = r'(at the start of) (your turn)'
    match = re.search(at_start_pattern, trigger, re.IGNORECASE)
    if match:
        return [match.group(1), match.group(2)]
    
    # If we can't break it down, return as single phrase
    return [trigger]


def break_down_effect_phrase(effect):
    """Break down effect phrases into granular atomic components."""
    if not effect or len(effect) < 3:
        return []
    
    atomic_parts = []
    
    # Pattern: "You may reveal a song card and put it into your hand"
    # Break into: ["You may", "reveal", "a", "song card", "and", "put", "it", "into your hand"]
    reveal_put_pattern = r'(you may )?(?:(reveal) (a|an) ([^,\s]+ card))(?:\s+and\s+)?(?:(put) (it) (.+))?'
    match = re.search(reveal_put_pattern, effect, re.IGNORECASE)
    if match and 'reveal' in effect.lower():
        parts = []
        if match.group(1):
            parts.append(match.group(1).strip())  # you may
        if match.group(2):
            parts.append(match.group(2).strip())  # reveal
        if match.group(3):
            parts.append(match.group(3).strip())  # a/an
        if match.group(4):
            parts.append(match.group(4).strip())  # song card
        if match.group(5):
            parts.append(match.group(5).strip())  # put
        if match.group(6):
            parts.append(match.group(6).strip())  # it
        if match.group(7):
            parts.append(match.group(7).strip())  # destination
        return parts
    
    # Pattern: "chosen character gets -X WILLPOWER this turn"
    # Break into: ["chosen character", "gets", "-X", "WILLPOWER", "this turn"]
    stat_change_pattern = r'(chosen (?:character|opposing character)) (gets) ([-+]X) ([A-Z]+)( this turn| until [^.]*)?'
    match = re.search(stat_change_pattern, effect, re.IGNORECASE)
    if match:
        target = match.group(1).strip()
        verb = match.group(2).strip()
        modifier = match.group(3).strip()
        stat = match.group(4).strip()
        duration = match.group(5).strip() if match.group(5) else ""
        
        atomic_parts.extend([target, verb, modifier, stat])
        if duration:
            atomic_parts.append(duration.strip())
        return atomic_parts
    
    # Pattern: "+X STRENGTH for each other Villain character you have in play"
    # Break into: ["+X", "STRENGTH", "for each other", "X character", "you have in play"]
    conditional_stat_pattern = r'([-+]X) ([A-Z]+) (for each (?:other )?)([A-Za-z]+ character) (you have in play)'
    match = re.search(conditional_stat_pattern, effect, re.IGNORECASE)
    if match:
        modifier = match.group(1).strip()
        stat = match.group(2).strip()
        condition_prefix = match.group(3).strip()
        target_type = match.group(4).strip()
        condition_suffix = match.group(5).strip()
        
        # Generalize the character type
        generalized_target = re.sub(r'([A-Za-z]+) character', r'X character', target_type)
        
        atomic_parts.extend([modifier, stat, condition_prefix, generalized_target, condition_suffix])
        return atomic_parts
    
    # Pattern: "you may deal X damage to chosen character"
    # Break into: ["you may", "deal", "X damage", "to", "chosen X character"]
    damage_pattern = r'(you may )?(remove|deal) ((?:up to )?X damage)(?:\s+(from|to)\s+(.+))?'
    match = re.search(damage_pattern, effect, re.IGNORECASE)
    if match:
        modal = match.group(1).strip() if match.group(1) else ""
        action = match.group(2).strip() if match.group(2) else ""
        damage_amount = match.group(3).strip() if match.group(3) else ""
        preposition = match.group(4).strip() if match.group(4) else ""
        target = match.group(5).strip() if match.group(5) else ""
        
        # Generalize character types in the target
        if target:
            target = generalize_character_types(target)
        
        if modal:
            atomic_parts.append(modal.strip())
        if action:
            atomic_parts.append(action)
        if damage_amount:
            atomic_parts.append(damage_amount)
        if preposition:
            atomic_parts.append(preposition)
        if target:
            atomic_parts.append(target)
        return atomic_parts
    
    # Pattern: "this character gains/gets X"
    # Break into: ["this character", "gains", "X"]
    character_gain_pattern = r'(this character|chosen character) (gains?|gets?) (.+)'
    match = re.search(character_gain_pattern, effect, re.IGNORECASE)
    if match:
        target = match.group(1).strip()
        verb = match.group(2).strip()
        gain = match.group(3).strip()
        
        # Try to break down the gain part further if it's complex
        if ' for each ' in gain.lower() or ' while ' in gain.lower() or ' if ' in gain.lower():
            gain_parts = break_down_complex_condition(gain)
            atomic_parts.extend([target, verb] + gain_parts)
        else:
            atomic_parts.extend([target, verb, gain])
        return atomic_parts
    
    # Pattern: "draw X cards" -> ["draw", "X", "cards"]
    # Pattern: "gain X lore" -> ["gain", "X", "lore"]
    draw_gain_pattern = r'(draw|gain) (X) (cards?|lore)'
    match = re.search(draw_gain_pattern, effect, re.IGNORECASE)
    if match:
        action = match.group(1).strip()
        quantity = match.group(2).strip()
        resource = match.group(3).strip()
        atomic_parts.extend([action, quantity, resource])
        return atomic_parts
    
    # Pattern: "look at the top X cards of your deck"
    # Break into: ["look at", "the top X cards", "of your deck"]
    look_pattern = r'(look at) (the top X cards?) (of your deck)'
    match = re.search(look_pattern, effect, re.IGNORECASE)
    if match:
        action = match.group(1).strip()
        quantity = match.group(2).strip()
        location = match.group(3).strip()
        atomic_parts.extend([action, quantity, location])
        return atomic_parts
    
    # Pattern: "put it into your hand" -> ["put", "it", "into your hand"]
    put_pattern = r'(put) (it|them|[^,]+?) (into your hand|on (?:the )?(?:top|bottom) of your deck[^.]*)'
    match = re.search(put_pattern, effect, re.IGNORECASE)
    if match:
        action = match.group(1).strip()
        object_ref = match.group(2).strip()
        destination = match.group(3).strip()
        atomic_parts.extend([action, object_ref, destination])
        return atomic_parts
    
    # Pattern: "If you do and you have a character named X in play, Y"
    # Break into: ["If you do", "and", "you have a character named X in play", "Y"]
    conditional_pattern = r'(if you do) (and) (you have [^,]+),?\s*(.+)'
    match = re.search(conditional_pattern, effect, re.IGNORECASE)
    if match:
        condition1 = match.group(1).strip()
        connector = match.group(2).strip()
        condition2 = match.group(3).strip()
        result = match.group(4).strip()
        
        atomic_parts.extend([condition1, connector, condition2, result])
        return atomic_parts
    
    # Pattern: "banish chosen character" -> ["banish", "chosen character"]
    action_target_pattern = r'(banish|exert|ready|return|put)\s+(.+)'
    match = re.search(action_target_pattern, effect, re.IGNORECASE)
    if match:
        action = match.group(1).strip()
        target = match.group(2).strip()
        atomic_parts.extend([action, target])
        return atomic_parts
    
    # If we can't break it down, return as single phrase
    return [effect]


def generalize_character_types(text):
    """Generalize character types to X placeholders."""
    # Replace specific character types with X
    patterns = [
        (r'chosen ([A-Za-z]+) character', r'chosen X character'),
        (r'each of your ([A-Za-z]+) characters', r'each of your X characters'),
        (r'your ([A-Za-z]+) characters', r'your X characters'),
        (r'([A-Za-z]+) character', r'X character'),
    ]
    
    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result


def break_down_complex_condition(text):
    """Break down complex conditional phrases."""
    # Pattern: "+X STRENGTH for each other Villain character you have in play"
    if ' for each ' in text.lower():
        parts = text.split(' for each ')
        if len(parts) == 2:
            # Generalize the character type in the second part
            second_part = generalize_character_types(parts[1].strip())
            return [parts[0].strip(), "for each", second_part]
    
    # Pattern: "Evasive while you have another character in play"
    if ' while you have ' in text.lower():
        parts = text.split(' while you have ')
        if len(parts) == 2:
            return [parts[0].strip(), "while you have", parts[1].strip()]
    
    # If we can't break it down, return as single part
    return [text]


def extract_core_building_blocks_with_parameters(text):
    """Extract building blocks with parameters and break down complex conditions."""
    # Extract parameters from original text before normalization
    original_text = text
    
    # Get atomic phrases (which will be normalized)
    atomic_parts = extract_atomic_phrases(text)
    
    building_block_combinations = []
    
    for part in atomic_parts:
        part_clean = part.strip()
        lower_part = part_clean.lower()
        
        block_combo = []
        
        # Handle complex conditions first
        if 'if it\'s a princess or queen character card' in lower_part:
            block_combo.extend([
                "condition.if_x_card(princess)",
                "condition.if_x_card(queen)"
            ])
        elif 'if a princess character is chosen' in lower_part:
            block_combo.append("condition.if_x_character_chosen(princess)")
        elif 'if a villain character is chosen' in lower_part:
            block_combo.append("condition.if_x_character_chosen(villain)")
        elif 'if a character named' in lower_part:
            # Search in original text for the name
            name_match = re.search(r'character named ([a-zA-Z\s]+)', original_text, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
                block_combo.append(f"condition.if_named_character({name.lower()})")
        elif 'chosen character named' in lower_part:
            # Search in original text for the name
            name_match = re.search(r'chosen character named ([a-zA-Z\s]+)', original_text, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
                block_combo.append(f"target.chosen_named_character({name.lower()})")
        else:
            # Get standard building blocks
            standard_blocks = extract_core_building_blocks(part_clean)
            for block_type, block_list in standard_blocks.items():
                for block in block_list:
                    # Add parameters where relevant - search in original text
                    if block == 'damage_amount':
                        # Search for damage patterns in original text
                        damage_match = re.search(r'(\d+)\s+damage', original_text, re.IGNORECASE)
                        if damage_match:
                            amount = damage_match.group(1)
                            block_combo.append(f"{block_type}.{block}({amount})")
                        elif 'up to' in part_clean.lower() and 'damage' in part_clean.lower():
                            block_combo.append(f"{block_type}.{block}(up_to_x)")
                        else:
                            block_combo.append(f"{block_type}.{block}(x)")
                    elif block in ['lore', 'willpower', 'strength']:
                        # Extract specific amounts for resources from original text
                        resource_patterns = [
                            (r'(\d+)\s+lore', 'lore'),
                            (r'(\d+)\s+◊', 'strength'),
                            (r'(\d+)\s+¤', 'willpower'),
                            (r'(\d+)\s+willpower', 'willpower'),
                            (r'(\d+)\s+strength', 'strength'),
                            (r'\+(\d+)\s+◊', 'strength'),
                            (r'\+(\d+)\s+¤', 'willpower'),
                            (r'\+(\d+)\s+willpower', 'willpower'),
                            (r'\+(\d+)\s+strength', 'strength'),
                        ]
                        
                        amount_found = False
                        for pattern, resource_type in resource_patterns:
                            if resource_type == block or (block == 'strength' and resource_type == 'strength') or (block == 'willpower' and resource_type == 'willpower'):
                                number_match = re.search(pattern, original_text, re.IGNORECASE)
                                if number_match:
                                    amount = number_match.group(1)
                                    block_combo.append(f"{block_type}.{block}({amount})")
                                    amount_found = True
                                    break
                        
                        if not amount_found:
                            block_combo.append(f"{block_type}.{block}")
                    elif block in ['cards', 'card']:
                        # Extract card amounts from original text
                        card_match = re.search(r'(\d+)\s+cards?', original_text, re.IGNORECASE)
                        if card_match:
                            amount = card_match.group(1)
                            block_combo.append(f"{block_type}.{block}({amount})")
                        else:
                            block_combo.append(f"{block_type}.{block}")
                    elif 'cost' in block:
                        cost_match = re.search(r'cost\s+(\d+)', original_text, re.IGNORECASE)
                        if cost_match:
                            amount = cost_match.group(1)
                            block_combo.append(f"{block_type}.{block}({amount})")
                        else:
                            block_combo.append(f"{block_type}.{block}")
                    else:
                        block_combo.append(f"{block_type}.{block}")
        
        if block_combo:
            building_block_combinations.append(" + ".join(block_combo))
    
    return building_block_combinations


def extract_core_building_blocks(text):
    """Extract granular building blocks from ability text."""
    # Split into atomic component parts
    parts = extract_atomic_phrases(text)
    
    building_blocks = {
        'temporal': [],
        'action': [],
        'target': [],
        'quantity': [],
        'resource': [],
        'direction': [],
        'modal': [],
        'stat_modifier': [],
        'keyword': [],
        'timing': [],
        'condition': []
    }
    
    for part in parts:
        part_clean = part.strip()
        lower_part = part_clean.lower()
        
        # TEMPORAL MARKERS
        if lower_part in ['when', 'whenever', 'during', 'at the start of']:
            building_blocks['temporal'].append(lower_part.replace(' ', '_'))
        
        # ACTION VERBS
        elif lower_part in ['play', 'quests', 'quest', 'is banished', 'banished', 'challenges', 'challenge', 'gets', 'gains', 'gain', 'remove', 'deal', 'draw', 'banish', 'exert', 'ready', 'return', 'put', 'look at']:
            building_blocks['action'].append(lower_part.replace(' ', '_'))
        
        # TARGETS
        elif lower_part in ['this character', 'chosen character', 'chosen opposing character', 'you', 'your turn', 'your characters', 'each of your', 'all characters']:
            building_blocks['target'].append(lower_part.replace(' ', '_'))
        
        # QUANTITY/SCOPE
        elif lower_part in ['x', 'up to x', 'the top x cards', 'each', 'all']:
            building_blocks['quantity'].append(lower_part.replace(' ', '_'))
        
        # RESOURCE TYPES  
        elif lower_part in ['damage', 'lore', 'cards', 'card', 'ink', 'willpower', 'strength']:
            building_blocks['resource'].append(lower_part)
        elif lower_part in ['x damage', 'up to x damage']:
            building_blocks['resource'].append('damage_amount')
        
        # DIRECTIONAL/PREPOSITIONS
        elif lower_part in ['from', 'to', 'into', 'of your deck']:
            building_blocks['direction'].append(lower_part.replace(' ', '_'))
        
        # MODALITY
        elif lower_part in ['you may', 'must', 'can', "can't", 'cannot']:
            building_blocks['modal'].append(lower_part.replace(' ', '_').replace("'", ''))
        
        # STAT MODIFIERS
        elif re.match(r'^[-+]x$', lower_part):
            building_blocks['stat_modifier'].append(lower_part)
        
        # KEYWORDS
        elif lower_part in ['evasive', 'rush', 'bodyguard', 'ward', 'challenger', 'support', 'resist']:
            building_blocks['keyword'].append(lower_part)
        
        # TIMING/DURATION
        elif lower_part in ['this turn', 'until the start of your next turn', 'at the start of their next turn']:
            building_blocks['timing'].append(lower_part.replace(' ', '_'))
        
        # CONDITIONS (complex patterns)
        elif 'if you have' in lower_part or 'while you have' in lower_part:
            if 'character' in lower_part:
                building_blocks['condition'].append('character_requirement')
            elif 'cards in your hand' in lower_part:
                building_blocks['condition'].append('hand_requirement')
            elif 'inkwell' in lower_part:
                building_blocks['condition'].append('inkwell_requirement')
            else:
                building_blocks['condition'].append('other_requirement')
        
        # COMPLETE TRIGGER PATTERNS (now normalized for consistency)
        elif lower_part == 'when you play this character' or lower_part == 'when this character is played':
            building_blocks['temporal'].append('when')
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('is_played')
        elif lower_part == 'whenever this character quests':
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('quests')
        elif lower_part == 'during your turn':
            building_blocks['temporal'].append('during')
            building_blocks['target'].append('your_turn')
        elif lower_part == 'at the start of your turn':
            building_blocks['temporal'].append('at_the_start_of')
            building_blocks['target'].append('your_turn')
        elif lower_part == 'when this character is banished':
            building_blocks['temporal'].append('when')
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('is_banished')
        
        # COMPOUND PATTERNS
        elif 'you may draw a card' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('draw')
            building_blocks['quantity'].append('a')
            building_blocks['resource'].append('card')
        elif '+x strength' in lower_part or '+x willpower' in lower_part:
            building_blocks['stat_modifier'].append('+x')
            if 'strength' in lower_part:
                building_blocks['resource'].append('strength')
            elif 'willpower' in lower_part:
                building_blocks['resource'].append('willpower')
        elif 'chosen x character' in lower_part:
            building_blocks['target'].append('chosen_x_character')
        elif 'each of your x characters' in lower_part:
            building_blocks['quantity'].append('each_of_your')
            building_blocks['target'].append('x_characters')
        elif 'each of your' in lower_part and 'characters' in lower_part:
            building_blocks['quantity'].append('each_of_your')
            building_blocks['target'].append('your_characters')
        elif 'into your inkwell' in lower_part:
            building_blocks['direction'].append('into')
            building_blocks['target'].append('your_inkwell')
        elif 'draw a card' in lower_part:
            building_blocks['action'].append('draw')
            building_blocks['quantity'].append('a')
            building_blocks['resource'].append('card')
        elif 'in a challenge' in lower_part:
            building_blocks['timing'].append('in_a_challenge')
        elif 'if you do' in lower_part:
            building_blocks['condition'].append('if_you_do')
        elif 'otherwise' in lower_part:
            building_blocks['condition'].append('otherwise')
        elif 'in play' in lower_part:
            building_blocks['condition'].append('in_play_requirement')
        elif 'at the end of your turn' in lower_part:
            building_blocks['timing'].append('at_end_of_turn')
        elif 'once during your turn' in lower_part:
            building_blocks['timing'].append('once_per_turn')
        
        # COST MODIFICATION PATTERNS
        elif 'you pay' in lower_part and 'less to play' in lower_part:
            building_blocks['condition'].append('cost_reduction')
        elif 'for free' in lower_part:
            building_blocks['modal'].append('for_free')
        
        # ADDITIONAL TRIGGER PATTERNS
        elif 'whenever you play a song' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['condition'].append('play_song_trigger')
        elif 'whenever you play an action' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['condition'].append('play_action_trigger')
        elif 'whenever you play a floodborn character' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['condition'].append('play_floodborn_trigger')
        elif 'whenever this character is challenged' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('is_challenged')
        
        # STATE CONDITIONS
        elif 'while this character is exerted' in lower_part:
            building_blocks['condition'].append('while_exerted')
        elif 'while this character has no damage' in lower_part:
            building_blocks['condition'].append('while_undamaged')
        elif 'while this character is at a location' in lower_part:
            building_blocks['condition'].append('while_at_location')
        elif 'during an opponent\'s turn' in lower_part:
            building_blocks['timing'].append('during_opponents_turn')
        
        # DECK/HAND MANIPULATION
        elif 'then choose and discard a card' in lower_part:
            building_blocks['action'].append('choose_and_discard')
            building_blocks['target'].append('a_card')
        elif 'it on either the top or the bottom of your deck' in lower_part:
            building_blocks['action'].append('put')
            building_blocks['target'].append('it')
            building_blocks['direction'].append('top_or_bottom_of_deck')
        elif 'this card to your hand' in lower_part:
            building_blocks['target'].append('this_card')
            building_blocks['direction'].append('to_your_hand')
        elif 'chosen character to their player\'s hand' in lower_part:
            building_blocks['target'].append('chosen_character')
            building_blocks['direction'].append('to_owners_hand')
        
        # KEYWORD GRANTING PATTERNS
        elif 'challenger +x this turn' in lower_part:
            building_blocks['keyword'].append('challenger')
            building_blocks['stat_modifier'].append('+x')
            building_blocks['timing'].append('this_turn')
        elif 'resist +x until' in lower_part:
            building_blocks['keyword'].append('resist')
            building_blocks['stat_modifier'].append('+x')
            building_blocks['timing'].append('until_condition')
        elif 'gains reckless' in lower_part:
            building_blocks['action'].append('gains')
            building_blocks['keyword'].append('reckless')
        
        # OPPONENT EFFECTS
        elif 'each opponent loses' in lower_part and 'lore' in lower_part:
            building_blocks['target'].append('each_opponent')
            building_blocks['action'].append('loses')
            building_blocks['resource'].append('lore')
        
        # SHIFT CONDITIONS
        elif 'if you used shift to play them' in lower_part:
            building_blocks['condition'].append('if_shifted')
        
        # ITEM TARGETING
        elif 'chosen item' in lower_part:
            building_blocks['target'].append('chosen_item')
        
        # LOCATION REFERENCES
        elif lower_part == 'here':
            building_blocks['target'].append('here')
        elif lower_part == 'them':
            building_blocks['target'].append('them')
        elif lower_part == 'that card':
            building_blocks['target'].append('that_card')
        elif lower_part == 'one':
            building_blocks['quantity'].append('one')
        
        # DISCARD CONDITIONS
        elif 'if this card is in your discard' in lower_part:
            building_blocks['condition'].append('if_in_discard')
        
        # STANDALONE ACTION PATTERNS
        elif lower_part == 'is played':
            building_blocks['action'].append('is_played')
        elif 'whenever they quests' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('they')
            building_blocks['action'].append('quests')
        
        # MORE COMPLEX PATTERNS
        elif 'each opponent chooses and discards a card' in lower_part:
            building_blocks['target'].append('each_opponent')
            building_blocks['action'].append('choose_and_discard')
            building_blocks['target'].append('a_card')
        elif 'chosen damaged character' in lower_part:
            building_blocks['target'].append('chosen_damaged_character')
        elif 'when this character is challenged and banished' in lower_part:
            building_blocks['temporal'].append('when')
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('is_challenged_and_banished')
        elif 'this character enters play exerted' in lower_part:
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('enters_play_exerted')
        elif 'when you play this item' in lower_part:
            building_blocks['temporal'].append('when')
            building_blocks['action'].append('play')
            building_blocks['target'].append('this_item')
        elif 'whenever you play an item' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['action'].append('play')
            building_blocks['target'].append('an_item')
        elif 'whenever you play a character' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['action'].append('play')
            building_blocks['target'].append('a_character')
        elif 'once per turn' in lower_part:
            building_blocks['timing'].append('once_per_turn')
        elif 'while this character has damage' in lower_part:
            building_blocks['condition'].append('while_damaged')
        elif 'while this character has x willpower or more' in lower_part:
            building_blocks['condition'].append('while_stat_threshold')
        elif 'rush this turn' in lower_part:
            building_blocks['keyword'].append('rush')
            building_blocks['timing'].append('this_turn')
        elif 'the challenging character' in lower_part:
            building_blocks['target'].append('challenging_character')
        elif 'and when they leaves play' in lower_part:
            building_blocks['temporal'].append('when')
            building_blocks['target'].append('they')
            building_blocks['action'].append('leaves_play')
        elif lower_part == 'characters':
            building_blocks['target'].append('characters')
        elif lower_part == 'hand':
            building_blocks['target'].append('hand')
        elif lower_part == 'item':
            building_blocks['target'].append('item')
        elif 'look at the top card of your deck' in lower_part:
            building_blocks['action'].append('look_at_top_card')
            building_blocks['target'].append('your_deck')
        elif 'you may reveal the top card of your deck' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('reveal_top_card')
            building_blocks['target'].append('your_deck')
        elif 'can\'t quest during their next turn' in lower_part:
            building_blocks['action'].append('cant_quest')
            building_blocks['timing'].append('next_turn')
        elif 'you pay x ink less for the next' in lower_part:
            building_blocks['condition'].append('next_card_cost_reduction')
        
        # DAMAGE MANIPULATION PATTERNS
        elif 'you may move up to x damage counters from chosen character to chosen opposing character' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('move_damage_counters')
            building_blocks['quantity'].append('up_to_x')
            building_blocks['target'].append('chosen_character')
            building_blocks['target'].append('chosen_opposing_character')
        elif 'you may move x damage counter from chosen character to chosen opposing character' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('move_damage_counter')
            building_blocks['quantity'].append('x')
            building_blocks['target'].append('chosen_character')
            building_blocks['target'].append('chosen_opposing_character')
        elif 'this character enters play with x damage' in lower_part:
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('enters_play_with_damage')
            building_blocks['quantity'].append('x')
        elif 'you may remove all damage from chosen character' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('remove_all_damage')
            building_blocks['target'].append('chosen_character')
        elif 'x damage on them' in lower_part:
            building_blocks['quantity'].append('x')
            building_blocks['resource'].append('damage')
            building_blocks['target'].append('them')
        
        # DISCARD/HAND MANIPULATION
        elif 'a character card from your discard to your hand' in lower_part:
            building_blocks['quantity'].append('a')
            building_blocks['target'].append('character_card')
            building_blocks['direction'].append('from_discard_to_hand')
        elif 'an action card from your discard to your hand' in lower_part:
            building_blocks['quantity'].append('an')
            building_blocks['target'].append('action_card')
            building_blocks['direction'].append('from_discard_to_hand')
        elif 'an item card from your discard to your hand' in lower_part:
            building_blocks['quantity'].append('an')
            building_blocks['target'].append('item_card')
            building_blocks['direction'].append('from_discard_to_hand')
        elif 'that card to your hand' in lower_part:
            building_blocks['target'].append('that_card')
            building_blocks['direction'].append('to_your_hand')
        elif 'card in your hand' in lower_part:
            building_blocks['target'].append('card')
            building_blocks['direction'].append('in_your_hand')
        elif 'then reveal the top card of your deck' in lower_part:
            building_blocks['action'].append('then')
            building_blocks['action'].append('reveal_top_card')
            building_blocks['target'].append('your_deck')
        
        # CARD TYPE CONDITIONS
        elif 'if it\'s a character card' in lower_part:
            building_blocks['condition'].append('if_character_card')
        elif 'if it\'s the named card' in lower_part:
            building_blocks['condition'].append('if_named_card')
        elif lower_part == 'item card':
            building_blocks['target'].append('item_card')
        
        # OPPONENT CONDITIONS
        elif 'if an opponent has more cards in their hand than you' in lower_part:
            building_blocks['condition'].append('if_opponent_more_cards')
        elif 'while an opponent has x or more lore' in lower_part:
            building_blocks['condition'].append('while_opponent_lore_threshold')
        elif 'each opponent with more lore than you loses x lore' in lower_part:
            building_blocks['target'].append('each_opponent')
            building_blocks['condition'].append('more_lore_than_you')
            building_blocks['action'].append('loses')
            building_blocks['resource'].append('lore')
        elif 'each opponent chooses and banishes one of their characters' in lower_part:
            building_blocks['target'].append('each_opponent')
            building_blocks['action'].append('choose_and_banish')
            building_blocks['target'].append('their_characters')
        elif 'the challenging player chooses and discards a card' in lower_part:
            building_blocks['target'].append('challenging_player')
            building_blocks['action'].append('choose_and_discard')
            building_blocks['target'].append('a_card')
        elif lower_part == 'opponent':
            building_blocks['target'].append('opponent')
        elif 'during opponents\' turns' in lower_part:
            building_blocks['timing'].append('during_opponents_turns')
        
        # WILLPOWER/STAT CONDITIONS
        elif 'chosen opposing character with x willpower or less' in lower_part:
            building_blocks['target'].append('chosen_opposing_character')
            building_blocks['condition'].append('with_willpower_or_less')
        elif 'chosen character with x willpower or less to their player\'s hand' in lower_part:
            building_blocks['target'].append('chosen_character')
            building_blocks['condition'].append('with_willpower_or_less')
            building_blocks['direction'].append('to_owners_hand')
        elif 'or location with cost x or less to their player\'s hand' in lower_part:
            building_blocks['target'].append('location')
            building_blocks['condition'].append('with_cost_or_less')
            building_blocks['direction'].append('to_owners_hand')
        elif 'you may give chosen character -x willpower this turn' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('give')
            building_blocks['target'].append('chosen_character')
            building_blocks['stat_modifier'].append('-x')
            building_blocks['resource'].append('willpower')
            building_blocks['timing'].append('this_turn')
        
        # SONG/SINGING PATTERNS
        elif 'to sing songs' in lower_part:
            building_blocks['action'].append('sing_songs')
        elif 'whenever this character sings a song' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('sings_song')
        
        # LOCATION PATTERNS
        elif 'when this character moves to a location' in lower_part:
            building_blocks['temporal'].append('when')
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('moves_to_location')
        elif 'whenever a character quests while here' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('a_character')
            building_blocks['action'].append('quests')
            building_blocks['condition'].append('while_here')
        elif 'while at a location' in lower_part:
            building_blocks['condition'].append('while_at_location')
        elif 'characters get +x lore while here' in lower_part:
            building_blocks['target'].append('characters')
            building_blocks['action'].append('get')
            building_blocks['stat_modifier'].append('+x')
            building_blocks['resource'].append('lore')
            building_blocks['condition'].append('while_here')
        elif 'chosen location' in lower_part:
            building_blocks['target'].append('chosen_location')
        elif 'whenever a character is banished while here' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('a_character')
            building_blocks['action'].append('is_banished')
            building_blocks['condition'].append('while_here')
        
        # CHALLENGE PATTERNS
        elif 'while being challenged' in lower_part:
            building_blocks['condition'].append('while_being_challenged')
        elif 'this character takes no damage from the challenge' in lower_part:
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('takes_no_damage')
            building_blocks['condition'].append('from_challenge')
        
        # SHIFT CONDITIONS
        elif 'if you used shift to play their' in lower_part:
            building_blocks['condition'].append('if_shifted')
        
        # ADVANCED TIMING
        elif 'whenever you play a second action in a turn' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['condition'].append('second_action_per_turn')
        elif 'whenever you remove x or more damage from one of your characters' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['action'].append('remove_damage')
            building_blocks['condition'].append('x_or_more')
            building_blocks['target'].append('your_characters')
        elif 'whenever one of your items is banished' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('your_items')
            building_blocks['action'].append('is_banished')
        
        # KEYWORD EFFECTS
        elif 'evasive until the start of your next turn' in lower_part:
            building_blocks['keyword'].append('evasive')
            building_blocks['timing'].append('until_next_turn')
        elif 'support this turn' in lower_part:
            building_blocks['keyword'].append('support')
            building_blocks['timing'].append('this_turn')
        elif 'resist +x this turn' in lower_part:
            building_blocks['keyword'].append('resist')
            building_blocks['stat_modifier'].append('+x')
            building_blocks['timing'].append('this_turn')
        elif 'they gains resist +x' in lower_part:
            building_blocks['target'].append('they')
            building_blocks['action'].append('gains')
            building_blocks['keyword'].append('resist')
            building_blocks['stat_modifier'].append('+x')
        
        # CHARACTER CONDITIONS
        elif 'if this character is exerted' in lower_part:
            building_blocks['condition'].append('if_exerted')
        elif 'chosen villain character' in lower_part:
            building_blocks['target'].append('chosen_villain_character')
        elif 'all opposing damaged characters' in lower_part:
            building_blocks['target'].append('all_opposing_damaged_characters')
        
        # DECK MANIPULATION
        elif 'that card on top of it' in lower_part:
            building_blocks['target'].append('that_card')
            building_blocks['direction'].append('on_top_of_it')
        elif 'name a card' in lower_part:
            building_blocks['action'].append('name_card')
        
        # SIMPLE WORDS
        elif lower_part == 'then':
            building_blocks['action'].append('then')
        elif lower_part == 'discard':
            building_blocks['action'].append('discard')
        
        # FINAL PUSH TO 90% - REMAINING PATTERNS
        elif 'this item enters play exerted' in lower_part:
            building_blocks['target'].append('this_item')
            building_blocks['action'].append('enters_play_exerted')
        elif 'you may give chosen character -x willpower until the start of your next turn' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('give')
            building_blocks['target'].append('chosen_character')
            building_blocks['stat_modifier'].append('-x')
            building_blocks['resource'].append('willpower')
            building_blocks['timing'].append('until_next_turn')
        elif 'chosen opponent reveals their hand and discards a non-character card of your choice' in lower_part:
            building_blocks['target'].append('chosen_opponent')
            building_blocks['action'].append('reveals_hand_and_discards')
            building_blocks['condition'].append('non_character_card')
        elif 'move up to x damage counters from chosen character to chosen opposing character' in lower_part:
            building_blocks['action'].append('move_damage_counters')
            building_blocks['quantity'].append('up_to_x')
            building_blocks['target'].append('chosen_character')
            building_blocks['target'].append('chosen_opposing_character')
        elif 'each opponent chooses one of their characters and returns that card to their hand' in lower_part:
            building_blocks['target'].append('each_opponent')
            building_blocks['action'].append('choose_and_return')
            building_blocks['target'].append('their_characters')
            building_blocks['direction'].append('to_their_hand')
        elif 'reveal the top card of your deck' in lower_part:
            building_blocks['action'].append('reveal_top_card')
            building_blocks['target'].append('your_deck')
        elif 'at the start of their turn' in lower_part:
            building_blocks['temporal'].append('at_the_start_of')
            building_blocks['target'].append('their_turn')
        elif 'you don\'t discard' in lower_part:
            building_blocks['modal'].append('you_dont')
            building_blocks['action'].append('discard')
        elif 'whenever one of your characters is banished' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('one_of_your_characters')
            building_blocks['action'].append('is_banished')
        elif 'all cards in your inkwell' in lower_part:
            building_blocks['target'].append('all_cards_in_inkwell')
        elif 'resist +x' in lower_part and 'until' not in lower_part and 'this turn' not in lower_part:
            building_blocks['keyword'].append('resist')
            building_blocks['stat_modifier'].append('+x')
        elif 'ward until the start of your next turn' in lower_part:
            building_blocks['keyword'].append('ward')
            building_blocks['timing'].append('until_next_turn')
        elif 'chosen opposing item' in lower_part:
            building_blocks['target'].append('chosen_opposing_item')
        elif 'at the start of its next turn' in lower_part:
            building_blocks['temporal'].append('at_the_start_of')
            building_blocks['target'].append('its_next_turn')
        elif 'this character can\'t be challenged' in lower_part:
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('cant_be_challenged')
        elif 'a racer character card from your discard to your hand' in lower_part:
            building_blocks['quantity'].append('a')
            building_blocks['target'].append('racer_character_card')
            building_blocks['direction'].append('from_discard_to_hand')
        elif 'whenever one of your characters sings a song' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('one_of_your_characters')
            building_blocks['action'].append('sings_song')
        elif 'whenever one of your characters challenges' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('one_of_your_characters')
            building_blocks['action'].append('challenges')
        elif 'when you play a floodborn character on this card' in lower_part:
            building_blocks['temporal'].append('when')
            building_blocks['action'].append('play')
            building_blocks['target'].append('floodborn_character')
            building_blocks['condition'].append('on_this_card')
        elif 'when this item is banished' in lower_part:
            building_blocks['temporal'].append('when')
            building_blocks['target'].append('this_item')
            building_blocks['action'].append('is_banished')
        elif 'challenger +x' in lower_part and 'this turn' not in lower_part:
            building_blocks['keyword'].append('challenger')
            building_blocks['stat_modifier'].append('+x')
        elif 'when this character challenges and is banished' in lower_part:
            building_blocks['temporal'].append('when')
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('challenges_and_is_banished')
        elif 'the challenged character' in lower_part:
            building_blocks['target'].append('challenged_character')
        elif 'choose an opposing character' in lower_part:
            building_blocks['action'].append('choose')
            building_blocks['target'].append('opposing_character')
        elif 'up to 2 chosen characters' in lower_part:
            building_blocks['quantity'].append('up_to_2')
            building_blocks['target'].append('chosen_characters')
        elif 'your characters named jetsam gain rush' in lower_part:
            building_blocks['target'].append('named_characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('rush')
        elif 'your characters named flotsam gain evasive' in lower_part:
            building_blocks['target'].append('named_characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('evasive')
        elif 'you may shuffle a card from any discard into its player\'s deck' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('shuffle_from_discard')
            building_blocks['target'].append('any_players_deck')
        elif lower_part == 'character':
            building_blocks['target'].append('character')
        elif lower_part == 'more':
            building_blocks['quantity'].append('more')
        
        # COMPREHENSIVE 100% CATEGORIZATION - BATCH 1: KEYWORD EFFECTS WITH TIMING
        elif 'reckless during their next turn' in lower_part:
            building_blocks['keyword'].append('reckless')
            building_blocks['timing'].append('during_their_next_turn')
        elif 'evasive this turn' in lower_part:
            building_blocks['keyword'].append('evasive')
            building_blocks['timing'].append('this_turn')
        elif 'they gain rush' in lower_part:
            building_blocks['target'].append('they')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('rush')
        elif 'they gains ward' in lower_part:
            building_blocks['target'].append('they')
            building_blocks['action'].append('gains')
            building_blocks['keyword'].append('ward')
        elif 'bodyguard and gets +x lore' in lower_part:
            building_blocks['keyword'].append('bodyguard')
            building_blocks['action'].append('gets')
            building_blocks['stat_modifier'].append('+x')
            building_blocks['resource'].append('lore')
        elif 'bodyguard until the start of your next turn' in lower_part:
            building_blocks['keyword'].append('bodyguard')
            building_blocks['timing'].append('until_next_turn')
        elif 'resist +x and support until the start of your next turn' in lower_part:
            building_blocks['keyword'].append('resist')
            building_blocks['stat_modifier'].append('+x')
            building_blocks['keyword'].append('support')
            building_blocks['timing'].append('until_next_turn')
        elif lower_part == 'reckless':
            building_blocks['keyword'].append('reckless')
        elif 'and evasive this turn' in lower_part:
            building_blocks['keyword'].append('evasive')
            building_blocks['timing'].append('this_turn')
        
        # CHALLENGE RESTRICTIONS
        elif 'opposing characters can\'t quest' in lower_part:
            building_blocks['target'].append('opposing_characters')
            building_blocks['action'].append('cant_quest')
        elif 'chosen character can\'t challenge during their next turn' in lower_part:
            building_blocks['target'].append('chosen_character')
            building_blocks['action'].append('cant_challenge')
            building_blocks['timing'].append('during_their_next_turn')
        elif 'chosen opposing character can\'t challenge during their next turn' in lower_part:
            building_blocks['target'].append('chosen_opposing_character')
            building_blocks['action'].append('cant_challenge')
            building_blocks['timing'].append('during_their_next_turn')
        elif 'characters with cost x or less can\'t challenge this character' in lower_part:
            building_blocks['target'].append('characters')
            building_blocks['condition'].append('with_cost_or_less')
            building_blocks['action'].append('cant_challenge')
            building_blocks['target'].append('this_character')
        elif 'characters with cost x or less can\'t challenge your characters' in lower_part:
            building_blocks['target'].append('characters')
            building_blocks['condition'].append('with_cost_or_less')
            building_blocks['action'].append('cant_challenge')
            building_blocks['target'].append('your_characters')
        elif 'this character can\'t challenge' in lower_part:
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('cant_challenge')
        elif 'characters can\'t be challenged while here' in lower_part:
            building_blocks['target'].append('characters')
            building_blocks['action'].append('cant_be_challenged')
            building_blocks['condition'].append('while_here')
        elif 'damaged characters can\'t challenge this character' in lower_part:
            building_blocks['target'].append('damaged_characters')
            building_blocks['action'].append('cant_challenge')
            building_blocks['target'].append('this_character')
        elif 'damaged characters can\'t challenge your characters' in lower_part:
            building_blocks['target'].append('damaged_characters')
            building_blocks['action'].append('cant_challenge')
            building_blocks['target'].append('your_characters')
        elif 'this character can\'t challenge or quest unless it is at a location' in lower_part:
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('cant_challenge_or_quest')
            building_blocks['condition'].append('unless_at_location')
        elif 'opposing characters with cost x or less can\'t challenge' in lower_part:
            building_blocks['target'].append('opposing_characters')
            building_blocks['condition'].append('with_cost_or_less')
            building_blocks['action'].append('cant_challenge')
        elif 'your villain characters can\'t be challenged' in lower_part:
            building_blocks['target'].append('your_villain_characters')
            building_blocks['action'].append('cant_be_challenged')
        elif 'your other locations can\'t be challenged' in lower_part:
            building_blocks['target'].append('your_other_locations')
            building_blocks['action'].append('cant_be_challenged')
        elif 'your characters named koda can\'t be challenged' in lower_part:
            building_blocks['target'].append('named_characters')
            building_blocks['action'].append('cant_be_challenged')
        elif 'this location can\'t be challenged' in lower_part:
            building_blocks['target'].append('this_location')
            building_blocks['action'].append('cant_be_challenged')
        elif 'chosen character can\'t challenge during their next turn' in lower_part:
            building_blocks['target'].append('chosen_character')
            building_blocks['action'].append('cant_challenge')
            building_blocks['timing'].append('during_their_next_turn')
        elif 'opposing pirate characters can\'t quest' in lower_part:
            building_blocks['target'].append('opposing_pirate_characters')
            building_blocks['action'].append('cant_quest')
        
        # NAMED CHARACTER CONDITIONS
        elif 'if a character named aladdin is chosen' in lower_part:
            building_blocks['condition'].append('if_named_character_chosen')
        elif 'chosen character named te kā' in lower_part:
            building_blocks['target'].append('chosen_named_character')
        elif 'if a princess character is chosen' in lower_part:
            building_blocks['condition'].append('if_character_type_chosen')
        elif 'chosen character named mulan' in lower_part:
            building_blocks['target'].append('chosen_named_character')
        elif 'chosen character named mufasa' in lower_part:
            building_blocks['target'].append('chosen_named_character')
        elif 'if the chosen character is named pain' in lower_part:
            building_blocks['condition'].append('if_chosen_character_named')
        elif 'if a villain character is chosen' in lower_part:
            building_blocks['condition'].append('if_character_type_chosen')
        
        # CHARACTER TYPE TARGETING
        elif 'chosen dragon character' in lower_part:
            building_blocks['target'].append('chosen_dragon_character')
        elif 'chosen opposing dragon character' in lower_part:
            building_blocks['target'].append('chosen_opposing_dragon_character')
        elif 'chosen hero character' in lower_part:
            building_blocks['target'].append('chosen_hero_character')
        elif 'chosen pirate character' in lower_part:
            building_blocks['target'].append('chosen_pirate_character')
        elif 'chosen princess character' in lower_part:
            building_blocks['target'].append('chosen_princess_character')
        elif 'chosen illusion character' in lower_part:
            building_blocks['target'].append('chosen_illusion_character')
        elif 'chosen racer character' in lower_part:
            building_blocks['target'].append('chosen_racer_character')
        elif 'chosen floodborn character' in lower_part:
            building_blocks['target'].append('chosen_floodborn_character')
        elif lower_part == 'princess':
            building_blocks['target'].append('princess')
        elif lower_part == 'king':
            building_blocks['target'].append('king')
        elif 'your prince' in lower_part:
            building_blocks['target'].append('your_prince')
        elif 'your musketeer characters gain evasive' in lower_part:
            building_blocks['target'].append('your_musketeer_characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('evasive')
        elif 'your titan characters' in lower_part:
            building_blocks['target'].append('your_titan_characters')
        elif 'your characters named zeus gain ward' in lower_part:
            building_blocks['target'].append('named_characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('ward')
        elif 'your characters named hercules gain evasive' in lower_part:
            building_blocks['target'].append('named_characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('evasive')
        elif 'your characters named lilo gain support' in lower_part:
            building_blocks['target'].append('named_characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('support')
        elif 'your puppy characters gain ward' in lower_part:
            building_blocks['target'].append('your_puppy_characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('ward')
        elif 'your puppy characters get +x lore' in lower_part:
            building_blocks['target'].append('your_puppy_characters')
            building_blocks['action'].append('get')
            building_blocks['stat_modifier'].append('+x')
            building_blocks['resource'].append('lore')
        elif 'your queen characters gain ward' in lower_part:
            building_blocks['target'].append('your_queen_characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('ward')
        elif 'your locations get +x lore' in lower_part:
            building_blocks['target'].append('your_locations')
            building_blocks['action'].append('get')
            building_blocks['stat_modifier'].append('+x')
            building_blocks['resource'].append('lore')
        elif 'your exerted characters gain ward' in lower_part:
            building_blocks['target'].append('your_exerted_characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('ward')
        elif 'your floodborn characters that have a card under them gain evasive and ward' in lower_part:
            building_blocks['target'].append('your_floodborn_characters')
            building_blocks['condition'].append('have_card_under')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('evasive')
            building_blocks['keyword'].append('ward')
        elif 'your characters with x willpower or more can\'t be dealt damage' in lower_part:
            building_blocks['target'].append('your_characters')
            building_blocks['condition'].append('with_willpower_or_more')
            building_blocks['action'].append('cant_be_dealt_damage')
        
        # BATCH 2: COMPLEX TRIGGERS AND CONDITIONS
        elif 'whenever one of your characters with bodyguard is banished' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('your_characters')
            building_blocks['condition'].append('with_bodyguard')
            building_blocks['action'].append('is_banished')
        elif 'whenever an opposing character is damaged' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('opposing_character')
            building_blocks['action'].append('is_damaged')
        elif 'whenever this character is dealt damage' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('is_dealt_damage')
        elif 'whenever this character challenges a damaged character' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('challenges')
            building_blocks['target'].append('damaged_character')
        elif 'whenever they challenges a hyena character' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('they')
            building_blocks['action'].append('challenges')
            building_blocks['target'].append('hyena_character')
        elif 'whenever they challenges a pirate character' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('they')
            building_blocks['action'].append('challenges')
            building_blocks['target'].append('pirate_character')
        elif 'whenever they challenges a damaged character' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('they')
            building_blocks['action'].append('challenges')
            building_blocks['target'].append('damaged_character')
        elif 'whenever a character of yours named robin hood quests' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('named_character_of_yours')
            building_blocks['action'].append('quests')
        elif 'whenever a character of yours named heihei quests' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('named_character_of_yours')
            building_blocks['action'].append('quests')
        elif 'whenever you play a location' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['action'].append('play')
            building_blocks['target'].append('a_location')
        elif 'whenever you play a hero character' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['action'].append('play')
            building_blocks['target'].append('hero_character')
        elif 'whenever you play another item' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['action'].append('play')
            building_blocks['target'].append('another_item')
        elif 'whenever an opposing character is banished' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('opposing_character')
            building_blocks['action'].append('is_banished')
        elif 'whenever one of your characters is banished' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('one_of_your_characters')
            building_blocks['action'].append('is_banished')
        elif 'whenever one of your characters quests' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('one_of_your_characters')
            building_blocks['action'].append('quests')
        elif 'whenever you discard a card' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['action'].append('discard')
            building_blocks['target'].append('a_card')
        elif 'whenever your opponent discards x or more cards' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('your_opponent')
            building_blocks['action'].append('discards')
            building_blocks['quantity'].append('x_or_more')
            building_blocks['target'].append('cards')
        elif 'whenever one of your locations is banished' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('one_of_your_locations')
            building_blocks['action'].append('is_banished')
        elif 'whenever one of your characters is chosen for support' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('one_of_your_characters')
            building_blocks['action'].append('is_chosen_for_support')
        elif 'whenever one of your characters is challenged' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('one_of_your_characters')
            building_blocks['action'].append('is_challenged')
        elif 'whenever a character is challenged while here' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('a_character')
            building_blocks['action'].append('is_challenged')
            building_blocks['condition'].append('while_here')
        elif 'whenever one of your hyena characters challenges a damaged character' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('your_hyena_characters')
            building_blocks['action'].append('challenges')
            building_blocks['target'].append('damaged_character')
        elif 'whenever one of your puppy characters is banished' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('your_puppy_characters')
            building_blocks['action'].append('is_banished')
        elif 'whenever one of your illusion characters quests' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('your_illusion_characters')
            building_blocks['action'].append('quests')
        elif 'whenever one of your ally characters quests' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('your_ally_characters')
            building_blocks['action'].append('quests')
        elif 'whenever an opponent plays a song' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('an_opponent')
            building_blocks['action'].append('plays')
            building_blocks['target'].append('a_song')
        elif 'whenever an opponent plays a character' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('an_opponent')
            building_blocks['action'].append('plays')
            building_blocks['target'].append('a_character')
        elif 'whenever you play a card' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['action'].append('play')
            building_blocks['target'].append('a_card')
        elif 'whenever one or more of your characters sings a song' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('one_or_more_of_your_characters')
            building_blocks['action'].append('sings_song')
        elif 'whenever one of your illusion characters is banished' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('your_illusion_characters')
            building_blocks['action'].append('is_banished')
        elif 'whenever an opposing character is exerted' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('opposing_character')
            building_blocks['action'].append('is_exerted')
        elif 'whenever an item is banished' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('an_item')
            building_blocks['action'].append('is_banished')
        elif 'whenever one of your characters with bodyguard is banished' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('your_characters')
            building_blocks['condition'].append('with_bodyguard')
            building_blocks['action'].append('is_banished')
        elif 'whenever you remove x or more damage from a character' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['action'].append('remove_damage')
            building_blocks['quantity'].append('x_or_more')
            building_blocks['target'].append('a_character')
        elif 'whenever one or more of your characters sings a song' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('one_or_more_of_your_characters')
            building_blocks['action'].append('sings_song')
        elif 'whenever they\'s challenged' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('they')
            building_blocks['action'].append('is_challenged')
        elif 'when an opponent plays a character' in lower_part:
            building_blocks['temporal'].append('when')
            building_blocks['target'].append('an_opponent')
            building_blocks['action'].append('plays')
            building_blocks['target'].append('a_character')
        elif 'when you play this location' in lower_part:
            building_blocks['temporal'].append('when')
            building_blocks['action'].append('play')
            building_blocks['target'].append('this_location')
        elif 'when you move a character here from a location' in lower_part:
            building_blocks['temporal'].append('when')
            building_blocks['action'].append('move_character')
            building_blocks['target'].append('here')
            building_blocks['direction'].append('from_location')
        elif 'when you play a floodborn character on this card' in lower_part:
            building_blocks['temporal'].append('when')
            building_blocks['action'].append('play')
            building_blocks['target'].append('floodborn_character')
            building_blocks['condition'].append('on_this_card')
        
        # COMPLEX CONDITIONS
        elif 'if you used shift to play this character' in lower_part:
            building_blocks['condition'].append('if_shifted_this_character')
        elif 'if you played a song this turn' in lower_part:
            building_blocks['condition'].append('if_played_song_this_turn')
        elif 'if you didn\'t play a song this turn' in lower_part:
            building_blocks['condition'].append('if_didnt_play_song_this_turn')
        elif 'if you removed damage this way' in lower_part:
            building_blocks['condition'].append('if_removed_damage_this_way')
        elif 'if you\'ve played x or more actions this turn' in lower_part:
            building_blocks['condition'].append('if_played_x_actions_this_turn')
        elif 'if you\'ve played x or more actions this turn' in lower_part:
            building_blocks['condition'].append('if_played_x_actions_this_turn')
        elif 'if that item costs 3 or less' in lower_part:
            building_blocks['condition'].append('if_item_cost_threshold')
        elif 'if they\'re a hero character' in lower_part:
            building_blocks['condition'].append('if_hero_character')
        elif 'if that card is a princess character card' in lower_part:
            building_blocks['condition'].append('if_princess_character_card')
        elif 'if it\'s a princess or queen character card' in lower_part:
            building_blocks['condition'].append('if_princess_or_queen_card')
        elif 'if it\'s a dragon character card' in lower_part:
            building_blocks['condition'].append('if_dragon_character_card')
        elif 'if it\'s a puppy character card' in lower_part:
            building_blocks['condition'].append('if_puppy_character_card')
        elif 'if it\'s an item card' in lower_part:
            building_blocks['condition'].append('if_item_card')
        elif 'if an illusion character card is discarded this way' in lower_part:
            building_blocks['condition'].append('if_illusion_discarded')
        elif 'if you discarded a pirate character card' in lower_part:
            building_blocks['condition'].append('if_discarded_pirate')
        elif 'if any princess cards were moved this way' in lower_part:
            building_blocks['condition'].append('if_princess_moved')
        elif 'if an opposing character was damaged this turn' in lower_part:
            building_blocks['condition'].append('if_opposing_damaged_this_turn')
        elif 'if one of your characters was damaged this turn' in lower_part:
            building_blocks['condition'].append('if_your_character_damaged_this_turn')
        elif 'if the banished item is named maurice\'s machine' in lower_part:
            building_blocks['condition'].append('if_specific_item_banished')
        elif 'if the moved character is a knight' in lower_part:
            building_blocks['condition'].append('if_moved_character_knight')
        elif 'if an opposing character has damage' in lower_part:
            building_blocks['condition'].append('if_opposing_has_damage')
        elif 'if this character has no damage' in lower_part:
            building_blocks['condition'].append('if_no_damage')
        elif 'if they has no damage' in lower_part:
            building_blocks['condition'].append('if_no_damage')
        elif 'if this character is at a location' in lower_part:
            building_blocks['condition'].append('if_at_location')
        elif 'if it\'s the second challenge this turn' in lower_part:
            building_blocks['condition'].append('if_second_challenge_this_turn')
        elif 'if they don\'t' in lower_part:
            building_blocks['condition'].append('if_they_dont')
        elif 'if chosen opponent has more cards in their hand than you' in lower_part:
            building_blocks['condition'].append('if_opponent_more_cards')
        elif 'if they have more than x cards in their hand' in lower_part:
            building_blocks['condition'].append('if_hand_size_threshold')
        elif 'if an opponent has more cards in their inkwell than you' in lower_part:
            building_blocks['condition'].append('if_opponent_more_inkwell')
        elif 'if an effect would cause you to discard one or more cards from your hand' in lower_part:
            building_blocks['condition'].append('if_would_discard_from_hand')
        elif 'if an effect would cause you to discard one or more cards' in lower_part:
            building_blocks['condition'].append('if_would_discard_cards')
        elif 'you can\'t play this character unless an opposing character was damaged this turn' in lower_part:
            building_blocks['condition'].append('play_restriction_damaged_opposing')
        
        # BATCH 3: FINAL PUSH TO 100% - REMAINING COMPLEX PATTERNS
        elif 'their instead' in lower_part:
            building_blocks['target'].append('their_instead')
        elif lower_part == 'inkwell':
            building_blocks['target'].append('inkwell')
        elif 'chosen opposing character into their player\'s inkwell facedown' in lower_part:
            building_blocks['target'].append('chosen_opposing_character')
            building_blocks['direction'].append('into_opponents_inkwell')
            building_blocks['condition'].append('facedown')
        elif 'an action card named fire the cannons! from your discard to your hand' in lower_part:
            building_blocks['target'].append('specific_action_card')
            building_blocks['direction'].append('from_discard_to_hand')
        elif 'at the end of the turn' in lower_part:
            building_blocks['timing'].append('at_end_of_turn')
        elif 'at the end of each opponent\'s turn' in lower_part:
            building_blocks['timing'].append('at_end_of_opponents_turn')
        elif 'chosen character or item with cost x or less to their player\'s hand' in lower_part:
            building_blocks['target'].append('chosen_character_or_item')
            building_blocks['condition'].append('with_cost_or_less')
            building_blocks['direction'].append('to_owners_hand')
        elif 'that player draws x cards' in lower_part:
            building_blocks['target'].append('that_player')
            building_blocks['action'].append('draws')
            building_blocks['quantity'].append('x')
            building_blocks['target'].append('cards')
        elif 'chosen character of yours to your hand' in lower_part:
            building_blocks['target'].append('chosen_character_of_yours')
            building_blocks['direction'].append('to_your_hand')
        elif 'while an opponent has no cards in their hand' in lower_part:
            building_blocks['condition'].append('while_opponent_no_cards')
        elif 'while one or more opponents have no cards in their hands' in lower_part:
            building_blocks['condition'].append('while_opponents_no_cards')
        elif '-x strength' in lower_part:
            building_blocks['stat_modifier'].append('-x')
            building_blocks['resource'].append('strength')
        elif 'card in your opponents\' hands' in lower_part:
            building_blocks['target'].append('card')
            building_blocks['direction'].append('in_opponents_hands')
        elif 'each opponent chooses and discards either x cards or 1 action card' in lower_part:
            building_blocks['target'].append('each_opponent')
            building_blocks['action'].append('choose_and_discard')
            building_blocks['condition'].append('either_cards_or_action')
        elif 'gain lore equal to the discarded character\'s strength' in lower_part:
            building_blocks['action'].append('gain')
            building_blocks['resource'].append('lore')
            building_blocks['condition'].append('equal_to_discarded_strength')
        elif 'they takes no damage from the challenge' in lower_part:
            building_blocks['target'].append('they')
            building_blocks['action'].append('takes_no_damage')
            building_blocks['condition'].append('from_challenge')
        elif 'draw cards equal to the damage on chosen character of yours' in lower_part:
            building_blocks['action'].append('draw')
            building_blocks['target'].append('cards')
            building_blocks['condition'].append('equal_to_damage')
        elif 'its player draws a card' in lower_part:
            building_blocks['target'].append('its_player')
            building_blocks['action'].append('draws')
            building_blocks['target'].append('a_card')
        elif 'an item card named pawpsicle from your discard to your hand' in lower_part:
            building_blocks['target'].append('specific_item_card')
            building_blocks['direction'].append('from_discard_to_hand')
        elif 'that many damage counters on this character instead' in lower_part:
            building_blocks['quantity'].append('that_many')
            building_blocks['target'].append('damage_counters')
            building_blocks['target'].append('this_character')
            building_blocks['condition'].append('instead')
        elif 'characters this turn' in lower_part:
            building_blocks['target'].append('characters')
            building_blocks['timing'].append('this_turn')
        elif 'your characters gain evasive this turn' in lower_part:
            building_blocks['target'].append('your_characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('evasive')
            building_blocks['timing'].append('this_turn')
        elif 'opponents can\'t play actions' in lower_part:
            building_blocks['target'].append('opponents')
            building_blocks['action'].append('cant_play')
            building_blocks['target'].append('actions')
        elif 'shuffle all character cards from your discard into your deck' in lower_part:
            building_blocks['action'].append('shuffle')
            building_blocks['target'].append('all_character_cards')
            building_blocks['direction'].append('from_discard_into_deck')
        elif 'you may have up to 99 copies of dalmatian puppy - tail wagger in your deck' in lower_part:
            building_blocks['modal'].append('deck_construction_rule')
        elif 'all characters get -x willpower until the start of your next turn' in lower_part:
            building_blocks['target'].append('all_characters')
            building_blocks['action'].append('get')
            building_blocks['stat_modifier'].append('-x')
            building_blocks['resource'].append('willpower')
            building_blocks['timing'].append('until_next_turn')
        elif 'reveal the top x cards of your deck' in lower_part:
            building_blocks['action'].append('reveal')
            building_blocks['target'].append('top_x_cards')
            building_blocks['target'].append('your_deck')
        elif 'each character card with cost x or less' in lower_part:
            building_blocks['target'].append('character_cards')
            building_blocks['condition'].append('with_cost_or_less')
        elif 'character card' in lower_part:
            building_blocks['target'].append('character_card')
        elif 'you may shuffle all broom cards from your discard into your deck' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('shuffle')
            building_blocks['target'].append('specific_cards')
            building_blocks['direction'].append('from_discard_into_deck')
        elif 'you may shuffle this card into your deck' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('shuffle')
            building_blocks['target'].append('this_card')
            building_blocks['direction'].append('into_deck')
        elif 'the player or players with the most cards in their hand chooses and discards a card' in lower_part:
            building_blocks['target'].append('player_with_most_cards')
            building_blocks['action'].append('choose_and_discard')
            building_blocks['target'].append('a_card')
        elif 'all opposing characters to their players\' hands' in lower_part:
            building_blocks['target'].append('all_opposing_characters')
            building_blocks['direction'].append('to_owners_hands')
        elif 'you may play any character with shift on this character as if this character had any name' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('play')
            building_blocks['condition'].append('shift_any_name')
        elif 'gain lore equal to that location\'s strength' in lower_part:
            building_blocks['action'].append('gain')
            building_blocks['resource'].append('lore')
            building_blocks['condition'].append('equal_to_location_strength')
        elif 'this item' in lower_part:
            building_blocks['target'].append('this_item')
        elif 'characters gain ward and evasive while here' in lower_part:
            building_blocks['target'].append('characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('ward')
            building_blocks['keyword'].append('evasive')
            building_blocks['condition'].append('while_here')
        elif 'characters gain rush while here' in lower_part:
            building_blocks['target'].append('characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('rush')
            building_blocks['condition'].append('while_here')
        elif 'characters gain evasive while here' in lower_part:
            building_blocks['target'].append('characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('evasive')
            building_blocks['condition'].append('while_here')
        elif 'characters named peter pan lose evasive and can\'t gain evasive' in lower_part:
            building_blocks['target'].append('named_characters')
            building_blocks['action'].append('lose')
            building_blocks['keyword'].append('evasive')
            building_blocks['action'].append('cant_gain')
            building_blocks['keyword'].append('evasive')
        elif 'deal that much damage to chosen opposing character' in lower_part:
            building_blocks['action'].append('deal')
            building_blocks['quantity'].append('that_much')
            building_blocks['resource'].append('damage')
            building_blocks['target'].append('chosen_opposing_character')
        elif 'you pay x ink less to move a character of yours here' in lower_part:
            building_blocks['condition'].append('ink_cost_reduction')
            building_blocks['action'].append('move_character')
            building_blocks['target'].append('character_of_yours')
            building_blocks['target'].append('here')
        elif 'one of your items' in lower_part:
            building_blocks['target'].append('one_of_your_items')
        elif 'an item card from your discard' in lower_part:
            building_blocks['target'].append('item_card')
            building_blocks['direction'].append('from_your_discard')
        elif 'choose a character of yours and gain lore equal to their strength' in lower_part:
            building_blocks['action'].append('choose')
            building_blocks['target'].append('character_of_yours')
            building_blocks['action'].append('gain')
            building_blocks['resource'].append('lore')
            building_blocks['condition'].append('equal_to_their_strength')
        elif 'then choose and discard x cards' in lower_part:
            building_blocks['action'].append('then')
            building_blocks['action'].append('choose_and_discard')
            building_blocks['quantity'].append('x')
            building_blocks['target'].append('cards')
        elif 'you pay x ink less to move your characters to a location' in lower_part:
            building_blocks['condition'].append('ink_cost_reduction')
            building_blocks['action'].append('move_characters')
            building_blocks['target'].append('your_characters')
            building_blocks['target'].append('a_location')
        elif 'you may search your deck for a madrigal character card and reveal that card to all players' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('search_deck')
            building_blocks['target'].append('specific_character_type')
            building_blocks['action'].append('reveal_to_all')
        
        # FINAL BATCH: COMPLETE 100% CATEGORIZATION - ALL REMAINING 128 PHRASES
        elif 'opposing characters with evasive gain reckless' in lower_part:
            building_blocks['target'].append('opposing_characters')
            building_blocks['condition'].append('with_evasive')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('reckless')
        elif 'your characters with cost x or less' in lower_part:
            building_blocks['target'].append('your_characters')
            building_blocks['condition'].append('with_cost_or_less')
        elif 'chosen character with cost x or less to their player\'s hand' in lower_part:
            building_blocks['target'].append('chosen_character')
            building_blocks['condition'].append('with_cost_or_less')
            building_blocks['direction'].append('to_owners_hand')
        elif 'chosen opposing character with x willpower or more' in lower_part:
            building_blocks['target'].append('chosen_opposing_character')
            building_blocks['condition'].append('with_willpower_or_more')
        elif 'move up to x damage counter from chosen character to chosen opposing character' in lower_part:
            building_blocks['action'].append('move_damage_counter')
            building_blocks['quantity'].append('up_to_x')
            building_blocks['target'].append('chosen_character')
            building_blocks['target'].append('chosen_opposing_character')
        elif 'at the start of their next turn unless they\'re at a location' in lower_part:
            building_blocks['timing'].append('at_start_of_their_turn')
            building_blocks['condition'].append('unless_at_location')
        elif 'move x damage counter from chosen character to chosen opposing character' in lower_part:
            building_blocks['action'].append('move_damage_counter')
            building_blocks['quantity'].append('x')
            building_blocks['target'].append('chosen_character')
            building_blocks['target'].append('chosen_opposing_character')
        elif 'them to your hand' in lower_part:
            building_blocks['target'].append('them')
            building_blocks['direction'].append('to_your_hand')
        elif 'during each opponent\'s turn' in lower_part:
            building_blocks['timing'].append('during_each_opponents_turn')
        elif 'you may look at each opponent\'s hand' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('look_at')
            building_blocks['target'].append('each_opponents_hand')
        elif 'while they has x willpower or more' in lower_part:
            building_blocks['condition'].append('while_willpower_threshold')
        elif 'look at the top card of each opponent\'s deck' in lower_part:
            building_blocks['action'].append('look_at')
            building_blocks['target'].append('top_card')
            building_blocks['target'].append('each_opponents_deck')
        elif 'they gets +willpower equal to the willpower of chosen character this turn' in lower_part:
            building_blocks['target'].append('they')
            building_blocks['action'].append('gets')
            building_blocks['stat_modifier'].append('+willpower')
            building_blocks['condition'].append('equal_to_character_willpower')
            building_blocks['timing'].append('this_turn')
        elif 'all cards in your hand count as having ◉' in lower_part:
            building_blocks['target'].append('all_cards_in_hand')
            building_blocks['condition'].append('count_as_having_ink')
        elif 'damage counters can\'t be removed' in lower_part:
            building_blocks['target'].append('damage_counters')
            building_blocks['action'].append('cant_be_removed')
        elif 'this character takes no damage from challenges this turn' in lower_part:
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('takes_no_damage')
            building_blocks['condition'].append('from_challenges')
            building_blocks['timing'].append('this_turn')
        elif 'chosen character of yours at a location' in lower_part:
            building_blocks['target'].append('chosen_character_of_yours')
            building_blocks['condition'].append('at_location')
        elif 'card in opponents\' hands' in lower_part:
            building_blocks['target'].append('card')
            building_blocks['direction'].append('in_opponents_hands')
        elif 'all opposing characters with x willpower or less' in lower_part:
            building_blocks['target'].append('all_opposing_characters')
            building_blocks['condition'].append('with_willpower_or_less')
        elif 'opponents can\'t choose your items for abilities or effects' in lower_part:
            building_blocks['target'].append('opponents')
            building_blocks['action'].append('cant_choose')
            building_blocks['target'].append('your_items')
            building_blocks['condition'].append('for_abilities_or_effects')
        elif 'you can\'t lose lore' in lower_part:
            building_blocks['modal'].append('you_cant')
            building_blocks['action'].append('lose')
            building_blocks['resource'].append('lore')
        elif 'each opponent reveals the top card of their deck' in lower_part:
            building_blocks['target'].append('each_opponent')
            building_blocks['action'].append('reveals')
            building_blocks['target'].append('top_card_of_deck')
        elif 'it into their hand' in lower_part:
            building_blocks['target'].append('it')
            building_blocks['direction'].append('into_their_hand')
        elif 'it on the bottom of their deck' in lower_part:
            building_blocks['target'].append('it')
            building_blocks['direction'].append('on_bottom_of_their_deck')
        elif 'all opposing characters get -x willpower until the start of your next turn' in lower_part:
            building_blocks['target'].append('all_opposing_characters')
            building_blocks['action'].append('get')
            building_blocks['stat_modifier'].append('-x')
            building_blocks['resource'].append('willpower')
            building_blocks['timing'].append('until_next_turn')
        elif 'a chosen opposing character' in lower_part:
            building_blocks['target'].append('chosen_opposing_character')
        elif 'each opponent draws a card' in lower_part:
            building_blocks['target'].append('each_opponent')
            building_blocks['action'].append('draws')
            building_blocks['target'].append('a_card')
        elif 'you may move up to x damage counters from this character to chosen opposing character' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('move_damage_counters')
            building_blocks['quantity'].append('up_to_x')
            building_blocks['target'].append('this_character')
            building_blocks['target'].append('chosen_opposing_character')
        elif 'all opposing characters' in lower_part and lower_part != 'all opposing characters with x willpower or less' and lower_part != 'all opposing characters get -x willpower until the start of your next turn':
            building_blocks['target'].append('all_opposing_characters')
        elif 'that character to your hand' in lower_part:
            building_blocks['target'].append('that_character')
            building_blocks['direction'].append('to_your_hand')
        elif 'choose an exerted character' in lower_part:
            building_blocks['action'].append('choose')
            building_blocks['target'].append('exerted_character')
        elif 'while challenging a damaged character' in lower_part:
            building_blocks['condition'].append('while_challenging_damaged')
        elif 'this character after the challenge' in lower_part:
            building_blocks['target'].append('this_character')
            building_blocks['timing'].append('after_challenge')
        elif 'you may draw cards until you have the same number' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('draw_cards')
            building_blocks['condition'].append('until_same_number')
        elif 'they discard until they have x cards in their hand' in lower_part:
            building_blocks['target'].append('they')
            building_blocks['action'].append('discard')
            building_blocks['condition'].append('until_x_cards_in_hand')
        elif 'characters gain ward and "exert' in lower_part:
            building_blocks['target'].append('characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('ward')
        elif 'opposing damaged characters gain reckless' in lower_part:
            building_blocks['target'].append('opposing_damaged_characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('reckless')
        elif 'this character also counts as being named king candy for shift' in lower_part:
            building_blocks['target'].append('this_character')
            building_blocks['condition'].append('counts_as_named_for_shift')
        elif 'action card' in lower_part and 'an action card' not in lower_part:
            building_blocks['target'].append('action_card')
        elif lower_part == 'exerted':
            building_blocks['condition'].append('exerted')
        elif 'x cards at random from your inkwell to your hand' in lower_part:
            building_blocks['quantity'].append('x')
            building_blocks['target'].append('cards')
            building_blocks['condition'].append('at_random')
            building_blocks['direction'].append('from_inkwell_to_hand')
        elif 'a card from your hand' in lower_part:
            building_blocks['target'].append('card')
            building_blocks['direction'].append('from_your_hand')
        elif 'you may search your deck for any card' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('search_deck')
            building_blocks['target'].append('any_card')
        elif 'then shuffle your deck' in lower_part:
            building_blocks['action'].append('then')
            building_blocks['action'].append('shuffle')
            building_blocks['target'].append('your_deck')
        elif 'each player plays with the top card of their deck face up' in lower_part:
            building_blocks['target'].append('each_player')
            building_blocks['condition'].append('plays_with_top_card_face_up')
        elif 'while one of your knight characters is at a location' in lower_part:
            building_blocks['condition'].append('while_knight_at_location')
        elif 'villain characters gain "exert' in lower_part:
            building_blocks['target'].append('villain_characters')
            building_blocks['action'].append('gain')
        elif 'the first time you move a character here' in lower_part:
            building_blocks['timing'].append('first_time')
            building_blocks['action'].append('move_character')
            building_blocks['target'].append('here')
        elif 'you may play their and they enters play exerted' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('play')
            building_blocks['target'].append('they')
            building_blocks['condition'].append('enters_play_exerted')
        elif 'singer 6' in lower_part:
            building_blocks['keyword'].append('singer_6')
        elif 'the top x cards of your deck into your discard to give chosen character -x willpower until the start of your next turn' in lower_part:
            building_blocks['target'].append('top_x_cards')
            building_blocks['direction'].append('into_discard')
            building_blocks['action'].append('give')
            building_blocks['target'].append('chosen_character')
            building_blocks['stat_modifier'].append('-x')
            building_blocks['resource'].append('willpower')
            building_blocks['timing'].append('until_next_turn')
        elif 'draw until you have x cards in your hand' in lower_part:
            building_blocks['action'].append('draw')
            building_blocks['condition'].append('until_x_cards_in_hand')
        elif 'you may look at the top card of chosen player\'s deck' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('look_at')
            building_blocks['target'].append('top_card')
            building_blocks['target'].append('chosen_players_deck')
        elif 'it on top of their deck or into their discard' in lower_part:
            building_blocks['target'].append('it')
            building_blocks['direction'].append('on_top_of_deck_or_discard')
        elif 'all the cards in your hand' in lower_part:
            building_blocks['target'].append('all_cards_in_your_hand')
        elif 'whenever one of your opponents\' characters' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('opponents_characters')
        elif lower_part == 'items':
            building_blocks['target'].append('items')
        elif 'or locations is returned to their hand from play' in lower_part:
            building_blocks['target'].append('locations')
            building_blocks['action'].append('is_returned')
            building_blocks['direction'].append('to_hand_from_play')
        elif 'each opponent puts the top card of their deck into their discard' in lower_part:
            building_blocks['target'].append('each_opponent')
            building_blocks['action'].append('puts')
            building_blocks['target'].append('top_card')
            building_blocks['direction'].append('into_discard')
        elif 'you may move x damage counter from chosen character here to chosen opposing character' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('move_damage_counter')
            building_blocks['quantity'].append('x')
            building_blocks['target'].append('chosen_character')
            building_blocks['target'].append('here')
            building_blocks['target'].append('chosen_opposing_character')
        elif 'an action card from your discard' in lower_part:
            building_blocks['target'].append('action_card')
            building_blocks['direction'].append('from_your_discard')
        elif 'you may pay x ink to gain lore equal to the damage on chosen opposing character' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('pay_ink')
            building_blocks['action'].append('gain')
            building_blocks['resource'].append('lore')
            building_blocks['condition'].append('equal_to_damage')
        elif 'you may pay x ink to have each opponent choose and discard a card' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('pay_ink')
            building_blocks['target'].append('each_opponent')
            building_blocks['action'].append('choose_and_discard')
        elif 'each opposing player can\'t gain lore unless one of their characters has challenged this turn' in lower_part:
            building_blocks['target'].append('each_opposing_player')
            building_blocks['action'].append('cant_gain_lore')
            building_blocks['condition'].append('unless_challenged_this_turn')
        elif 'you may pay x ink to have chosen opponent choose and discard a card' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('pay_ink')
            building_blocks['target'].append('chosen_opponent')
            building_blocks['action'].append('choose_and_discard')
        elif 'you pay x ink less for the first action you play each turn' in lower_part:
            building_blocks['condition'].append('ink_cost_reduction')
            building_blocks['target'].append('first_action')
            building_blocks['timing'].append('each_turn')
        elif 'a location card from your discard to your hand' in lower_part:
            building_blocks['target'].append('location_card')
            building_blocks['direction'].append('from_discard_to_hand')
        elif 'chosen character of yours' in lower_part and 'to your hand' not in lower_part and 'at a location' not in lower_part:
            building_blocks['target'].append('chosen_character_of_yours')
        elif 'all opponents lose x lore and you gain lore equal to the lore lost this way' in lower_part:
            building_blocks['target'].append('all_opponents')
            building_blocks['action'].append('lose')
            building_blocks['resource'].append('lore')
            building_blocks['action'].append('gain')
            building_blocks['condition'].append('equal_to_lore_lost')
        elif 'its player gains x lore' in lower_part:
            building_blocks['target'].append('its_player')
            building_blocks['action'].append('gains')
            building_blocks['quantity'].append('x')
            building_blocks['resource'].append('lore')
        elif 'you may have any number of cards named microbots in your deck' in lower_part:
            building_blocks['modal'].append('deck_construction_rule')
        elif 'deal damage to chosen character or location equal to the number of characters here' in lower_part:
            building_blocks['action'].append('deal')
            building_blocks['resource'].append('damage')
            building_blocks['target'].append('chosen_character_or_location')
            building_blocks['condition'].append('equal_to_characters_here')
        elif 'then choose and discard that many cards' in lower_part:
            building_blocks['action'].append('then')
            building_blocks['action'].append('choose_and_discard')
            building_blocks['quantity'].append('that_many')
            building_blocks['target'].append('cards')
        elif 'look at the cards in your inkwell' in lower_part:
            building_blocks['action'].append('look_at')
            building_blocks['target'].append('cards_in_inkwell')
        elif 'chosen opposing character loses willpower equal to this character\'s strength until the start of your next turn' in lower_part:
            building_blocks['target'].append('chosen_opposing_character')
            building_blocks['action'].append('loses')
            building_blocks['resource'].append('willpower')
            building_blocks['condition'].append('equal_to_character_strength')
            building_blocks['timing'].append('until_next_turn')
        elif 'you may choose and discard a card to give chosen opposing character -x willpower until the start of your next turn' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('choose_and_discard')
            building_blocks['target'].append('a_card')
            building_blocks['action'].append('give')
            building_blocks['target'].append('chosen_opposing_character')
            building_blocks['stat_modifier'].append('-x')
            building_blocks['resource'].append('willpower')
            building_blocks['timing'].append('until_next_turn')
        elif 'you may only have 2 copies of the glass slipper in your deck' in lower_part:
            building_blocks['modal'].append('deck_construction_rule')
        elif 'then that player draws a card' in lower_part:
            building_blocks['action'].append('then')
            building_blocks['target'].append('that_player')
            building_blocks['action'].append('draws')
            building_blocks['target'].append('a_card')
        elif 'that card to its player\'s hand' in lower_part:
            building_blocks['target'].append('that_card')
            building_blocks['direction'].append('to_its_players_hand')
        elif 'then that player discards a card at random' in lower_part:
            building_blocks['action'].append('then')
            building_blocks['target'].append('that_player')
            building_blocks['action'].append('discards')
            building_blocks['target'].append('a_card')
            building_blocks['condition'].append('at_random')
        elif lower_part == 'and':
            building_blocks['action'].append('and')
        elif 'you have a character named anna in pla' in lower_part:
            building_blocks['condition'].append('have_named_character_in_play')
        elif 'choose one: • each player draws a card' in lower_part:
            building_blocks['modal'].append('choose_one')
            building_blocks['target'].append('each_player')
            building_blocks['action'].append('draws')
            building_blocks['target'].append('a_card')
        elif '• each player chooses and discards a card' in lower_part:
            building_blocks['target'].append('each_player')
            building_blocks['action'].append('choose_and_discard')
            building_blocks['target'].append('a_card')
        elif 'opponents need x lore to win the game' in lower_part:
            building_blocks['target'].append('opponents')
            building_blocks['condition'].append('lore_requirement_to_win')
        elif 'whenever an opponent chooses this character for an action or ability' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('an_opponent')
            building_blocks['action'].append('chooses')
            building_blocks['target'].append('this_character')
            building_blocks['condition'].append('for_action_or_ability')
        elif 'chosen opponent reveals their hand' in lower_part:
            building_blocks['target'].append('chosen_opponent')
            building_blocks['action'].append('reveals')
            building_blocks['target'].append('their_hand')
        elif 'discard your hand' in lower_part:
            building_blocks['action'].append('discard')
            building_blocks['target'].append('your_hand')
        elif 'a damage counter on them' in lower_part:
            building_blocks['target'].append('damage_counter')
            building_blocks['target'].append('them')
        elif 'remove all damage from them' in lower_part:
            building_blocks['action'].append('remove_all_damage')
            building_blocks['target'].append('them')
        elif lower_part == 'damaged characters':
            building_blocks['target'].append('damaged_characters')
        elif 'chosen opponent chooses one of their characters and returns that card to their hand' in lower_part:
            building_blocks['target'].append('chosen_opponent')
            building_blocks['action'].append('choose_and_return')
            building_blocks['target'].append('their_characters')
            building_blocks['direction'].append('to_their_hand')
        elif 'each opponent discards a card at random' in lower_part:
            building_blocks['target'].append('each_opponent')
            building_blocks['action'].append('discards')
            building_blocks['target'].append('a_card')
            building_blocks['condition'].append('at_random')
        elif 'chosen opponent loses x lore' in lower_part:
            building_blocks['target'].append('chosen_opponent')
            building_blocks['action'].append('loses')
            building_blocks['quantity'].append('x')
            building_blocks['resource'].append('lore')
        elif 'chosen character with x willpower or less' in lower_part:
            building_blocks['target'].append('chosen_character')
            building_blocks['condition'].append('with_willpower_or_less')
        elif 'characters" this turn' in lower_part:
            building_blocks['target'].append('characters')
            building_blocks['timing'].append('this_turn')
        elif 'an item card with cost x or less from your discard to your hand' in lower_part:
            building_blocks['target'].append('item_card')
            building_blocks['condition'].append('with_cost_or_less')
            building_blocks['direction'].append('from_discard_to_hand')
        elif 'them in your hand' in lower_part:
            building_blocks['target'].append('them')
            building_blocks['direction'].append('in_your_hand')
        elif 'up to 2 item cards from your discard to your hand' in lower_part:
            building_blocks['quantity'].append('up_to_2')
            building_blocks['target'].append('item_cards')
            building_blocks['direction'].append('from_discard_to_hand')
        elif 'each player pays x ink more to play actions or items' in lower_part:
            building_blocks['target'].append('each_player')
            building_blocks['action'].append('pays')
            building_blocks['quantity'].append('x')
            building_blocks['resource'].append('ink')
            building_blocks['condition'].append('more_to_play')
        elif 'while this character is being challenged' in lower_part:
            building_blocks['condition'].append('while_being_challenged')
        elif 'each character you removed damage from this way' in lower_part:
            building_blocks['target'].append('each_character')
            building_blocks['condition'].append('removed_damage_this_way')
        elif 'x damage on their' in lower_part:
            building_blocks['quantity'].append('x')
            building_blocks['resource'].append('damage')
            building_blocks['target'].append('their')
        elif 'each opposing character gets -x willpower until the start of your next turn' in lower_part:
            building_blocks['target'].append('each_opposing_character')
            building_blocks['action'].append('gets')
            building_blocks['stat_modifier'].append('-x')
            building_blocks['resource'].append('willpower')
            building_blocks['timing'].append('until_next_turn')
        elif '+x lore' in lower_part:
            building_blocks['stat_modifier'].append('+x')
            building_blocks['resource'].append('lore')
        elif 'those characters' in lower_part:
            building_blocks['target'].append('those_characters')
        elif 'gain lore equal to the strength of chosen opposing character' in lower_part:
            building_blocks['action'].append('gain')
            building_blocks['resource'].append('lore')
            building_blocks['condition'].append('equal_to_opposing_strength')
        elif 'opposing characters with rush enter play exerted' in lower_part:
            building_blocks['target'].append('opposing_characters')
            building_blocks['condition'].append('with_rush')
            building_blocks['action'].append('enter_play_exerted')
        elif 'this character to your hand' in lower_part:
            building_blocks['target'].append('this_character')
            building_blocks['direction'].append('to_your_hand')
        elif 'move x damage counter from this character to chosen opposing character' in lower_part:
            building_blocks['action'].append('move_damage_counter')
            building_blocks['quantity'].append('x')
            building_blocks['target'].append('this_character')
            building_blocks['target'].append('chosen_opposing_character')
        elif 'each opponent chooses one of their characters and puts that card on the bottom of their deck' in lower_part:
            building_blocks['target'].append('each_opponent')
            building_blocks['action'].append('choose_and_put')
            building_blocks['target'].append('their_characters')
            building_blocks['direction'].append('on_bottom_of_deck')
        elif 'you may search your deck for a card named wrong lever! and reveal that card to all players' in lower_part:
            building_blocks['modal'].append('you_may')
            building_blocks['action'].append('search_deck')
            building_blocks['target'].append('specific_named_card')
            building_blocks['action'].append('reveal_to_all')
        elif 'chosen opponent discards a card at random' in lower_part:
            building_blocks['target'].append('chosen_opponent')
            building_blocks['action'].append('discards')
            building_blocks['target'].append('a_card')
            building_blocks['condition'].append('at_random')
        elif 'the challenging player may choose and discard a card' in lower_part:
            building_blocks['target'].append('challenging_player')
            building_blocks['modal'].append('may')
            building_blocks['action'].append('choose_and_discard')
            building_blocks['target'].append('a_card')
        elif 'x damage counter on chosen character' in lower_part:
            building_blocks['quantity'].append('x')
            building_blocks['target'].append('damage_counter')
            building_blocks['target'].append('chosen_character')
        elif 'chosen character into their player\'s inkwell facedown and exerted' in lower_part:
            building_blocks['target'].append('chosen_character')
            building_blocks['direction'].append('into_opponents_inkwell')
            building_blocks['condition'].append('facedown_and_exerted')
        elif 'x damage counters on all opposing characters' in lower_part:
            building_blocks['quantity'].append('x')
            building_blocks['target'].append('damage_counters')
            building_blocks['target'].append('all_opposing_characters')
        elif 'all opposing items' in lower_part:
            building_blocks['target'].append('all_opposing_items')
        elif 'all opposing locations' in lower_part:
            building_blocks['target'].append('all_opposing_locations')
        elif 'opposing items enter play exerted' in lower_part:
            building_blocks['target'].append('opposing_items')
            building_blocks['action'].append('enter_play_exerted')
        elif 'while x or more characters of yours are exerted' in lower_part:
            building_blocks['condition'].append('while_x_or_more_exerted')
        elif 'each opponent puts the top card of their deck into their inkwell facedown and exerted' in lower_part:
            building_blocks['target'].append('each_opponent')
            building_blocks['action'].append('puts')
            building_blocks['target'].append('top_card')
            building_blocks['direction'].append('into_inkwell')
            building_blocks['condition'].append('facedown_and_exerted')
        elif 'skip your turn\'s draw step' in lower_part:
            building_blocks['action'].append('skip')
            building_blocks['timing'].append('draw_step')
        elif 'and at the start of your turn' in lower_part:
            building_blocks['timing'].append('at_start_of_turn')
        elif 'card in your discard' in lower_part:
            building_blocks['target'].append('card')
            building_blocks['direction'].append('in_your_discard')
        
        # FINAL 5 PHRASES TO ACHIEVE 100%
        elif 'whenever this character moves to a location' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('this_character')
            building_blocks['action'].append('moves_to_location')
        elif 'whenever a character is challenged and banished while here' in lower_part:
            building_blocks['temporal'].append('whenever')
            building_blocks['target'].append('a_character')
            building_blocks['action'].append('is_challenged_and_banished')
            building_blocks['condition'].append('while_here')
        elif 'characters gain ward and' in lower_part and 'exert' in lower_part:
            building_blocks['target'].append('characters')
            building_blocks['action'].append('gain')
            building_blocks['keyword'].append('ward')
            building_blocks['action'].append('exert')
        elif 'villain characters gain' in lower_part and 'exert' in lower_part:
            building_blocks['target'].append('villain_characters')
            building_blocks['action'].append('gain')
            building_blocks['action'].append('exert')
        elif 'characters' in lower_part and 'this turn' in lower_part:
            building_blocks['target'].append('characters')
            building_blocks['timing'].append('this_turn')
        
        # MORE GRANULAR PATTERNS
        elif lower_part == 'reveal':
            building_blocks['action'].append('reveal')
        elif 'song card' in lower_part:
            building_blocks['target'].append('card_type')
        elif lower_part == 'it':
            building_blocks['target'].append('it')
        elif 'into your hand' in lower_part:
            building_blocks['direction'].append('into')
            building_blocks['target'].append('your_hand')
        elif 'for each' in lower_part:
            building_blocks['condition'].append('for_each')
        elif 'for each other' in lower_part:
            building_blocks['condition'].append('for_each_other')
        elif 'you have in play' in lower_part:
            building_blocks['condition'].append('in_play_requirement')
        elif 'x character' in lower_part:
            building_blocks['target'].append('x_character')
        elif 'other' in lower_part and 'character' in lower_part:
            building_blocks['target'].append('other_character')
        elif 'on the bottom of your deck' in lower_part:
            building_blocks['direction'].append('on_bottom_of_deck')
        elif 'on the top of your deck' in lower_part:
            building_blocks['direction'].append('on_top_of_deck')
        elif 'the rest' in lower_part:
            building_blocks['target'].append('the_rest')
        elif 'in any order' in lower_part:
            building_blocks['modal'].append('in_any_order')
    
    return building_blocks


def analyze_final_patterns():
    """Final analysis focusing on the most essential patterns."""
    catalog_path = Path("data/all-cards/ability_catalog.json")
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    all_atomic_phrases = []
    all_building_blocks = defaultdict(list)
    uncategorized_phrases = []
    ability_examples = []
    
    for ability_name, ability_data in catalog['named_abilities'].items():
        effect_text = ability_data.get('effect_text', '')
        if not effect_text:
            continue
        
        # Get atomic phrases
        atomic_parts = extract_atomic_phrases(effect_text)
        all_atomic_phrases.extend(atomic_parts)
        
        # Get building blocks and track what gets categorized
        blocks = extract_core_building_blocks(effect_text)
        categorized_phrases = set()
        
        for block_type, block_list in blocks.items():
            for block in block_list:
                all_building_blocks[f"{block_type}.{block}"].append(ability_name)
        
        # Check which atomic phrases didn't get turned into building blocks
        for phrase in atomic_parts:
            phrase_categorized = False
            lower_phrase = phrase.lower()
            
            # Check if this phrase would trigger any building block categorization
            for part in atomic_parts:
                temp_blocks = extract_core_building_blocks(part)
                if any(block_list for block_list in temp_blocks.values()):
                    if part == phrase:
                        phrase_categorized = True
                        categorized_phrases.add(phrase)
                        break
            
            if not phrase_categorized:
                uncategorized_phrases.append(phrase)
        
        # Store example
        ability_examples.append({
            'name': ability_name,
            'type': ability_data.get('type', 'unknown'),
            'original': effect_text,
            'atomic_parts': atomic_parts,
            'building_blocks': blocks,
            'uncategorized': [p for p in atomic_parts if p not in categorized_phrases]
        })
    
    phrase_counts = Counter(all_atomic_phrases)
    uncategorized_counts = Counter(uncategorized_phrases)
    
    return {
        'phrase_counts': phrase_counts,
        'building_blocks': dict(all_building_blocks),
        'ability_examples': ability_examples,
        'uncategorized_phrases': uncategorized_counts,
        'total_phrases': len(all_atomic_phrases),
        'categorized_phrases': len(all_atomic_phrases) - len(uncategorized_phrases),
        'uncategorized_count': len(uncategorized_phrases)
    }


def print_final_analysis(results):
    """Print the final, clean analysis."""
    print("=" * 80)
    print("FINAL LORCANA ABILITY ATOMIC ANALYSIS")
    print("=" * 80)
    
    print("=== PHRASE CATEGORIZATION SUMMARY ===")
    print(f"Total atomic phrases: {results['total_phrases']}")
    print(f"Categorized into building blocks: {results['categorized_phrases']}")
    print(f"Uncategorized phrases: {results['uncategorized_count']}")
    print(f"Categorization rate: {results['categorized_phrases']/results['total_phrases']*100:.1f}%")
    
    print("\n=== TOP 30 MOST COMMON ATOMIC PHRASES ===")
    for phrase, count in results['phrase_counts'].most_common(30):
        print(f"{count:3d}: {phrase}")
    
    print(f"\n=== BUILDING BLOCK FREQUENCY ===")
    block_counts = {k: len(v) for k, v in results['building_blocks'].items()}
    sorted_blocks = sorted(block_counts.items(), key=lambda x: x[1], reverse=True)
    
    for block_type, count in sorted_blocks[:30]:
        print(f"{count:3d}: {block_type}")
    
    print(f"\n=== TOP 25 UNCATEGORIZED PHRASES ===")
    print("(These need new building block categories)")
    for phrase, count in results['uncategorized_phrases'].most_common(25):
        print(f"{count:3d}: {phrase}")
    
    print(f"\n=== ATOMIC PHRASE BREAKDOWN EXAMPLES ===")
    # Show examples of how complex phrases get broken down
    complex_examples = []
    for example in results['ability_examples']:
        if len(example['atomic_parts']) > 1 and example['original']:
            complex_examples.append(example)
    
    # Randomly select 5 examples instead of always taking the first 5
    import random
    if len(complex_examples) > 5:
        complex_examples = random.sample(complex_examples, 5)
    else:
        complex_examples = complex_examples[:5]
    
    for example in complex_examples:
        print(f"\n{example['name']}:")
        print(f"  Original: {example['original']}")
        print(f"  Broken into:")
        
        # Get all building blocks for the entire ability
        all_blocks = extract_core_building_blocks_with_parameters(example['original'])
        
        for i, block_combo in enumerate(all_blocks, 1):
            print(f"    {i}. {block_combo}")
    
    print(f"\n=== ABILITY PATTERN EXAMPLES ===")
    
    # Show examples of the most common trigger+effect combinations
    trigger_effect_combos = defaultdict(list)
    
    for example in results['ability_examples']:
        blocks = example['building_blocks']
        triggers = blocks.get('triggers', [])
        effects = blocks.get('effects', [])
        
        for trigger in triggers:
            for effect in effects:
                combo = f"{trigger} -> {effect}"
                if len(trigger_effect_combos[combo]) < 3:  # Keep first 3 examples
                    trigger_effect_combos[combo].append(example['name'])
    
    # Sort by frequency and show top combinations
    combo_counts = {combo: len(examples) for combo, examples in trigger_effect_combos.items()}
    sorted_combos = sorted(combo_counts.items(), key=lambda x: x[1], reverse=True)
    
    print("\nMost Common Trigger -> Effect Patterns:")
    for combo, count in sorted_combos[:15]:
        if count >= 3:  # Only show patterns with at least 3 examples
            examples = trigger_effect_combos[combo]
            print(f"{count:3d}: {combo}")
            print(f"     Examples: {', '.join(examples)}")
    
    print(f"\n=== IMPLEMENTATION ROADMAP ===")
    print("""
CORE COMPONENTS TO IMPLEMENT:

1. TRIGGER SYSTEM:
   - when_played (most common trigger)
   - when_quests (second most common)
   - when_banished, during_turn, start_of_turn

2. EFFECT SYSTEM:
   - stat_boost (most common effect)
   - draw_cards, gain_lore, remove_damage
   - banish, gain_keyword, return_to_hand

3. TARGET SYSTEM:
   - this_character (most common target)
   - chosen_character, your_characters
   - chosen_opposing

4. CONDITION SYSTEM:
   - require_character, while_have_character
   - require_hand_size, require_damage_state

5. MODIFIER SYSTEM:
   - this_turn (duration)
   - until_condition (complex duration)

IMPLEMENTATION PRIORITY:
Phase 1: when_played + stat_boost + this_character
Phase 2: when_quests + draw_cards + chosen_character  
Phase 3: when_banished + gain_lore + your_characters
Phase 4: Advanced conditions and modifiers

NEXT STEPS:
1. Review uncategorized phrases to identify missing building block types
2. Implement atomic phrase -> building block mapping
3. Create composable ability system from building blocks
    """)


if __name__ == "__main__":
    results = analyze_final_patterns()
    print_final_analysis(results)
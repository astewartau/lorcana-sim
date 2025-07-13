#!/usr/bin/env python3
"""
Comprehensive script to extract and analyze all abilities from the Lorcana card database.

This script reads the lorcana-json database and extracts:
- All unique abilities (keywords, named abilities, triggered, static, activated)
- Groups them by type and pattern
- Counts how many cards have each ability
- Extracts full ability text descriptions
- Creates a checklist format output file
"""

import json
import re
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class AbilityAnalyzer:
    """Analyzes abilities from Lorcana cards."""
    
    def __init__(self, data_path: str):
        """Initialize the analyzer with the path to the allCards.json file."""
        self.data_path = Path(data_path)
        self.cards = []
        self.abilities_by_type = defaultdict(list)
        self.ability_counts = defaultdict(int)
        self.ability_full_texts = defaultdict(set)
        self.cards_with_ability = defaultdict(list)
        self.keyword_definitions = {}
        
    def load_data(self):
        """Load the card data from JSON file."""
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.cards = data['cards']
            
    def extract_abilities(self):
        """Extract all abilities from the cards."""
        # Common keyword patterns in effect text
        keyword_patterns = {
            'Bodyguard': r'\bBodyguard\b',
            'Challenger': r'\bChallenger\b',
            'Evasive': r'\bEvasive\b',
            'Reckless': r'\bReckless\b',
            'Resist': r'\bResist\b',
            'Rush': r'\bRush\b',
            'Shift': r'\bShift\b',
            'Singer': r'\bSinger\b',
            'Support': r'\bSupport\b',
            'Ward': r'\bWard\b',
        }
        
        for card in self.cards:
            if 'abilities' not in card or not card['abilities']:
                continue
                
            card_name = card.get('fullName', 'Unknown Card')
            
            for ability in card['abilities']:
                ability_type = ability.get('type', 'unknown')
                ability_name = ability.get('name', '')
                ability_effect = ability.get('effect', '')
                ability_full_text = ability.get('fullText', '')
                
                # For keyword type, use the 'keyword' field if available
                if ability_type == 'keyword':
                    keyword_name = ability.get('keyword', '')
                    if keyword_name:
                        ability_name = keyword_name
                        # Use reminderText as effect if available
                        reminder_text = ability.get('reminderText', '')
                        if reminder_text and not ability_effect:
                            ability_effect = reminder_text
                    elif not ability_name:
                        # Fallback to pattern matching
                        for keyword, pattern in keyword_patterns.items():
                            if re.search(pattern, ability_effect, re.IGNORECASE):
                                ability_name = keyword
                                break
                
                # Create a unique identifier for the ability
                if ability_name:
                    ability_key = f"{ability_type}:{ability_name}"
                else:
                    # For unnamed abilities, use a cleaned version of the effect
                    cleaned_effect = re.sub(r'[^\w\s]', '', ability_effect[:50])
                    ability_key = f"{ability_type}:unnamed_{cleaned_effect}"
                
                # Store the ability information
                self.abilities_by_type[ability_type].append({
                    'name': ability_name,
                    'effect': ability_effect,
                    'full_text': ability_full_text,
                    'card': card_name,
                    'key': ability_key
                })
                
                # Count occurrences
                self.ability_counts[ability_key] += 1
                
                # Store unique full texts
                if ability_full_text:
                    self.ability_full_texts[ability_key].add(ability_full_text)
                
                # Track which cards have this ability
                self.cards_with_ability[ability_key].append(card_name)
                
                # Extract keyword definitions
                if ability_type == 'keyword' and ability_name and ability_effect:
                    self.keyword_definitions[ability_name] = ability_effect
    
    def group_abilities_by_pattern(self) -> Dict[str, List[Dict]]:
        """Group abilities by common patterns or effects."""
        pattern_groups = defaultdict(list)
        
        # Common patterns to look for
        patterns = {
            'damage_dealing': r'deal.*damage|damage.*to',
            'card_draw': r'draw.*card|look at.*top.*card',
            'cost_reduction': r'pay.*less|reduce.*cost|costs.*less',
            'lore_generation': r'gain.*lore|quest for.*lore',
            'character_boost': r'get.*\+|gains.*\+|\+.*strength|\+.*willpower',
            'protection': r'can\'t be.*challenged|damage.*prevented|resist',
            'removal': r'banish|return.*hand|put.*bottom',
            'exert_effects': r'when.*exerted|whenever.*exerts',
            'play_effects': r'when you play|when.*played',
            'challenge_effects': r'when.*challenges|whenever.*challenged',
            'quest_effects': r'when.*quests|whenever.*quest',
            'ink_effects': r'ink.*well|add.*ink',
            'song_effects': r'sing.*song|songs cost',
            'item_effects': r'item.*you control|items get',
            'location_effects': r'location.*you control|at.*location',
            'character_type_effects': r'princess|hero|villain|captain|knight|fairy|dragon',
            'ready_effects': r'ready|doesn\'t.*exert|untap',
            'move_effects': r'move.*to.*location|move.*character',
            'discard_effects': r'discard|opponent.*discards',
            'reveal_effects': r'reveal|look at.*hand',
            'shift_effects': r'shift|you can pay',
            'evasive_effects': r'can only be challenged|evasive',
            'bodyguard_effects': r'bodyguard|must.*challenge',
            'singer_effects': r'singer|count.*ink.*sing',
            'resist_effects': r'resist|damage.*reduced',
            'reckless_effects': r'reckless|can\'t.*quest',
            'ward_effects': r'ward|opponent.*pays',
            'support_effects': r'support|add.*strength.*another'
        }
        
        # Analyze each ability
        for ability_type, abilities in self.abilities_by_type.items():
            for ability in abilities:
                effect_text = ability['effect'].lower()
                full_text = ability['full_text'].lower()
                name = ability['name'].lower()
                
                # Check against each pattern
                matched = False
                for pattern_name, pattern_regex in patterns.items():
                    if (re.search(pattern_regex, effect_text) or 
                        re.search(pattern_regex, full_text) or
                        re.search(pattern_regex, name)):
                        pattern_groups[pattern_name].append(ability)
                        matched = True
                
                # If no pattern matched, put in 'other'
                if not matched:
                    pattern_groups['other'].append(ability)
        
        return pattern_groups
    
    def generate_markdown_report(self) -> str:
        """Generate a comprehensive markdown report of all abilities."""
        report = []
        
        # Header
        report.append("# Lorcana Abilities Comprehensive Analysis")
        report.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total cards analyzed: {len(self.cards)}")
        report.append(f"Total unique abilities found: {len(self.ability_counts)}\n")
        
        # Table of Contents
        report.append("## Table of Contents")
        report.append("1. [Summary Statistics](#summary-statistics)")
        report.append("2. [Keywords](#keywords)")
        report.append("3. [Static Abilities](#static-abilities)")
        report.append("4. [Triggered Abilities](#triggered-abilities)")
        report.append("5. [Activated Abilities](#activated-abilities)")
        report.append("6. [Abilities by Pattern](#abilities-by-pattern)")
        report.append("7. [Implementation Checklist](#implementation-checklist)\n")
        
        # Summary Statistics
        report.append("## Summary Statistics")
        report.append("\n### Abilities by Type")
        type_counts = Counter()
        for ability_type, abilities in self.abilities_by_type.items():
            type_counts[ability_type] = len(abilities)
        
        for ability_type, count in type_counts.most_common():
            report.append(f"- **{ability_type.title()}**: {count} instances")
        
        report.append("\n### Most Common Abilities")
        for ability_key, count in sorted(self.ability_counts.items(), 
                                       key=lambda x: x[1], reverse=True)[:20]:
            ability_type, ability_name = ability_key.split(':', 1)
            if ability_name.startswith('unnamed_'):
                display_name = f"Unnamed {ability_type}"
            else:
                display_name = ability_name
            report.append(f"- **{display_name}** ({ability_type}): {count} cards")
        
        # Keywords Section
        report.append("\n## Keywords")
        report.append("\nKeywords are abilities that appear on multiple cards with consistent effects.\n")
        
        keyword_abilities = [a for a in self.abilities_by_type.get('keyword', [])]
        unique_keywords = {}
        
        for ability in keyword_abilities:
            name = ability['name']
            if name and name not in unique_keywords:
                unique_keywords[name] = {
                    'effect': ability['effect'],
                    'count': self.ability_counts[f"keyword:{name}"],
                    'examples': self.cards_with_ability[f"keyword:{name}"][:3]
                }
        
        # If we found keywords, display them
        if unique_keywords:
            for keyword, info in sorted(unique_keywords.items()):
                report.append(f"### {keyword}")
                report.append(f"- **Description**: {info['effect']}")
                report.append(f"- **Card Count**: {info['count']}")
                report.append(f"- **Example Cards**: {', '.join(info['examples'])}")
                report.append("")
        else:
            # Show unnamed keyword abilities
            report.append("*Note: Keywords in this set are implemented as unnamed abilities with the keyword type.*\n")
            
            # Group unnamed keywords by effect pattern
            keyword_effects = defaultdict(list)
            for ability in keyword_abilities:
                if not ability['name']:
                    effect = ability['effect']
                    keyword_effects[effect].append(ability['card'])
            
            # Show most common keyword effects
            sorted_effects = sorted(keyword_effects.items(), 
                                  key=lambda x: len(x[1]), reverse=True)[:20]
            
            for effect, cards in sorted_effects:
                report.append(f"### {effect}")
                report.append(f"- **Card Count**: {len(cards)}")
                report.append(f"- **Example Cards**: {', '.join(cards[:3])}")
                report.append("")
        
        # Static Abilities
        report.append("\n## Static Abilities")
        report.append("\nStatic abilities provide continuous effects while the card is in play.\n")
        
        static_abilities = self.abilities_by_type.get('static', [])
        unique_static = {}
        
        for ability in static_abilities:
            key = ability['key']
            if key not in unique_static:
                unique_static[key] = {
                    'name': ability['name'],
                    'effect': ability['effect'],
                    'full_text': ability['full_text'],
                    'count': self.ability_counts[key],
                    'examples': self.cards_with_ability[key][:3]
                }
        
        # Sort by count
        for key, info in sorted(unique_static.items(), 
                               key=lambda x: x[1]['count'], reverse=True)[:30]:
            report.append(f"### {info['name'] or 'Unnamed Static Ability'}")
            report.append(f"- **Full Text**: {info['full_text']}")
            report.append(f"- **Card Count**: {info['count']}")
            report.append(f"- **Example Cards**: {', '.join(info['examples'])}")
            report.append("")
        
        # Triggered Abilities
        report.append("\n## Triggered Abilities")
        report.append("\nTriggered abilities activate when specific game events occur.\n")
        
        triggered_abilities = self.abilities_by_type.get('triggered', [])
        unique_triggered = {}
        
        for ability in triggered_abilities:
            key = ability['key']
            if key not in unique_triggered:
                unique_triggered[key] = {
                    'name': ability['name'],
                    'effect': ability['effect'],
                    'full_text': ability['full_text'],
                    'count': self.ability_counts[key],
                    'examples': self.cards_with_ability[key][:3]
                }
        
        # Sort by count
        for key, info in sorted(unique_triggered.items(), 
                               key=lambda x: x[1]['count'], reverse=True)[:30]:
            report.append(f"### {info['name'] or 'Unnamed Triggered Ability'}")
            report.append(f"- **Full Text**: {info['full_text']}")
            report.append(f"- **Card Count**: {info['count']}")
            report.append(f"- **Example Cards**: {', '.join(info['examples'])}")
            report.append("")
        
        # Activated Abilities
        report.append("\n## Activated Abilities")
        report.append("\nActivated abilities can be used by paying their costs.\n")
        
        activated_abilities = self.abilities_by_type.get('activated', [])
        unique_activated = {}
        
        for ability in activated_abilities:
            key = ability['key']
            if key not in unique_activated:
                unique_activated[key] = {
                    'name': ability['name'],
                    'effect': ability['effect'],
                    'full_text': ability['full_text'],
                    'count': self.ability_counts[key],
                    'examples': self.cards_with_ability[key][:3]
                }
        
        # Sort by count
        for key, info in sorted(unique_activated.items(), 
                               key=lambda x: x[1]['count'], reverse=True)[:30]:
            report.append(f"### {info['name'] or 'Unnamed Activated Ability'}")
            report.append(f"- **Full Text**: {info['full_text']}")
            report.append(f"- **Card Count**: {info['count']}")
            report.append(f"- **Example Cards**: {', '.join(info['examples'])}")
            report.append("")
        
        # Abilities by Pattern
        report.append("\n## Abilities by Pattern")
        report.append("\nAbilities grouped by their game effects and patterns.\n")
        
        pattern_groups = self.group_abilities_by_pattern()
        
        # Sort patterns by number of abilities
        sorted_patterns = sorted(pattern_groups.items(), 
                               key=lambda x: len(x[1]), reverse=True)
        
        for pattern_name, abilities in sorted_patterns[:20]:
            if not abilities:
                continue
                
            report.append(f"### {pattern_name.replace('_', ' ').title()}")
            report.append(f"Total abilities in this category: {len(abilities)}\n")
            
            # Group by unique effects
            unique_in_pattern = {}
            for ability in abilities:
                key = ability['key']
                if key not in unique_in_pattern:
                    unique_in_pattern[key] = {
                        'name': ability['name'],
                        'type': key.split(':')[0],
                        'effect': ability['effect'],
                        'count': self.ability_counts[key]
                    }
            
            # Show top 10 most common in this pattern
            for key, info in sorted(unique_in_pattern.items(), 
                                   key=lambda x: x[1]['count'], reverse=True)[:10]:
                name = info['name'] or 'Unnamed'
                report.append(f"- **{name}** ({info['type']}): {info['effect'][:100]}... ({info['count']} cards)")
            
            report.append("")
        
        # Implementation Checklist
        report.append("\n## Implementation Checklist")
        report.append("\nTrack implementation progress for each ability type.\n")
        
        # Keywords
        report.append("### Keywords")
        if unique_keywords:
            for keyword in sorted(unique_keywords.keys()):
                report.append(f"- [ ] **{keyword}** ({unique_keywords[keyword]['count']} cards)")
        else:
            # Count keyword abilities by their 'keyword' field, not effect text
            keyword_counts = defaultdict(int)
            for ability in keyword_abilities:
                # Only count abilities that have actual keyword field
                if ability.get('keyword'):
                    keyword_name = ability['keyword'].capitalize()
                    keyword_counts[keyword_name] += 1
                # Skip non-keyword abilities
            
            for keyword, count in sorted(keyword_counts.items()):
                report.append(f"- [ ] **{keyword}** (~{count} cards)")
        
        # Most common abilities needing implementation
        report.append("\n### High-Priority Abilities (10+ cards)")
        high_priority = [(k, v) for k, v in self.ability_counts.items() if v >= 10]
        for ability_key, count in sorted(high_priority, key=lambda x: x[1], reverse=True):
            ability_type, ability_name = ability_key.split(':', 1)
            if ability_name.startswith('unnamed_'):
                # Get a better description for unnamed abilities
                for ability in self.abilities_by_type[ability_type]:
                    if ability['key'] == ability_key:
                        display_name = f"{ability['effect'][:50]}..."
                        break
            else:
                display_name = ability_name
            report.append(f"- [ ] **{display_name}** ({ability_type}, {count} cards)")
        
        # All unique ability texts
        report.append("\n## All Unique Ability Texts")
        report.append("\nComplete list of every unique ability text found:\n")
        
        all_texts = set()
        for abilities in self.abilities_by_type.values():
            for ability in abilities:
                if ability['full_text']:
                    all_texts.add(ability['full_text'])
        
        for i, text in enumerate(sorted(all_texts), 1):
            report.append(f"{i}. {text}")
        
        return '\n'.join(report)
    
    def save_report(self, output_path: str):
        """Save the report to a markdown file."""
        report = self.generate_markdown_report()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Report saved to: {output_file}")
        
        # Also print summary statistics
        print(f"\nSummary:")
        print(f"- Total cards analyzed: {len(self.cards)}")
        print(f"- Total unique abilities: {len(self.ability_counts)}")
        print(f"- Ability types found: {list(self.abilities_by_type.keys())}")
        print(f"- Most common ability: {max(self.ability_counts.items(), key=lambda x: x[1]) if self.ability_counts else 'None'}")


def main():
    """Main function to run the ability enumeration."""
    # Path to the allCards.json file
    data_path = "/home/ashley/repos/lorcana/lorcana-sim/data/all-cards/allCards.json"
    
    # Output path for the report
    output_path = "/home/ashley/repos/lorcana/lorcana-sim/abilities_comprehensive_report.md"
    
    # Create analyzer and run analysis
    analyzer = AbilityAnalyzer(data_path)
    
    print("Loading card data...")
    analyzer.load_data()
    
    print("Extracting abilities...")
    analyzer.extract_abilities()
    
    print("Generating report...")
    analyzer.save_report(output_path)
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
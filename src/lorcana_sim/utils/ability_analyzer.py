"""Ability analysis and enumeration tools for understanding the ability landscape."""

from typing import Dict, List, Any, Set, DefaultDict
from collections import defaultdict, Counter
import re
import json

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
                            'full_text': ability.get('fullText', ''),
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
            'cost_reduction': r'costs? \d+ less|pay \d+ less',
            'banish_effects': r'banish|return.*hand',
            'healing_effects': r'heal|remove.*damage',
            'exert_effects': r'exert|ready',
            'location_effects': r'location|move.*character',
            'discard_effects': r'discard|choose.*discard'
        }
        
        grouped = defaultdict(list)
        
        for ability_name, data in self.named_abilities.items():
            effect_text = (data['effect_text'] + ' ' + data['full_text']).lower()
            matched = False
            
            for pattern_name, pattern in patterns.items():
                if re.search(pattern, effect_text):
                    grouped[pattern_name].append(ability_name)
                    matched = True
                    break
            
            if not matched:
                grouped['uncategorized'].append(ability_name)
        
        return dict(grouped)
    
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
        
        pattern_groups = self.get_named_abilities_by_pattern()
        pattern_priority = sorted(
            pattern_groups.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        return {
            'high_priority_keywords': [k for k, data in keywords_by_freq[:5]],
            'medium_priority_keywords': [k for k, data in keywords_by_freq[5:10]],
            'low_priority_keywords': [k for k, data in keywords_by_freq[10:]],
            'high_priority_named': [k for k, data in named_by_freq[:20]],
            'top_pattern_groups': [pattern for pattern, abilities in pattern_priority[:10]]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about abilities"""
        total_ability_instances = sum(data['count'] for data in self.named_abilities.values())
        total_keyword_instances = sum(data['count'] for data in self.keyword_catalog.values())
        
        pattern_groups = self.get_named_abilities_by_pattern()
        largest_pattern = max(pattern_groups.items(), key=lambda x: len(x[1])) if pattern_groups else ('none', [])
        
        return {
            'total_cards': len(self.cards),
            'unique_keywords': len(self.keyword_catalog),
            'total_keyword_instances': total_keyword_instances,
            'unique_named_abilities': len(self.named_abilities),
            'total_named_ability_instances': total_ability_instances,
            'pattern_groups_found': len(pattern_groups),
            'largest_pattern_group': largest_pattern[0],
            'largest_pattern_size': len(largest_pattern[1]),
            'uncategorized_abilities': len(pattern_groups.get('uncategorized', []))
        }
    
    def export_ability_catalog(self, output_file: str) -> None:
        """Export complete ability catalog for implementation reference"""
        catalog = {
            'keywords': {
                keyword: {
                    'count': data['count'],
                    'values': list(data['values']),
                    'example_cards': data['cards'][:5]  # First 5 examples
                }
                for keyword, data in self.keyword_catalog.items()
            },
            'named_abilities': {
                name: {
                    'count': data['count'],
                    'type': data['type'],
                    'effect_text': data['effect_text'],
                    'full_text': data['full_text'],
                    'example_cards': data['cards'][:3]  # First 3 examples
                }
                for name, data in self.named_abilities.items()
            },
            'patterns': self.get_named_abilities_by_pattern(),
            'implementation_priority': self.get_implementation_priority(),
            'statistics': self.get_statistics()
        }
        
        with open(output_file, 'w') as f:
            json.dump(catalog, f, indent=2, default=str)
    
    def print_summary(self):
        """Print a comprehensive summary of the ability analysis"""
        stats = self.get_statistics()
        priority = self.get_implementation_priority()
        patterns = self.get_named_abilities_by_pattern()
        
        print("=" * 60)
        print(" ABILITY ANALYSIS SUMMARY")
        print("=" * 60)
        
        print(f"\nDatabase Overview:")
        print(f"  Total cards: {stats['total_cards']}")
        print(f"  Unique keywords: {stats['unique_keywords']}")
        print(f"  Total keyword instances: {stats['total_keyword_instances']}")
        print(f"  Unique named abilities: {stats['unique_named_abilities']}")
        print(f"  Total named ability instances: {stats['total_named_ability_instances']}")
        
        print(f"\nKeyword Implementation Priority:")
        print(f"  High priority: {', '.join(priority['high_priority_keywords'])}")
        print(f"  Medium priority: {', '.join(priority['medium_priority_keywords'])}")
        print(f"  Low priority: {', '.join(priority['low_priority_keywords'])}")
        
        print(f"\nTop Named Abilities by Frequency:")
        for ability in priority['high_priority_named'][:10]:
            count = self.named_abilities[ability]['count']
            print(f"  {ability}: {count} instances")
        
        print(f"\nTop Pattern Groups:")
        for pattern in priority['top_pattern_groups'][:8]:
            count = len(patterns[pattern])
            print(f"  {pattern}: {count} abilities")
        
        print(f"\nImplementation Complexity:")
        print(f"  Keywords (manageable): {stats['unique_keywords']}")
        print(f"  Named abilities (needs patterns): {stats['unique_named_abilities']}")
        print(f"  Largest pattern group: {stats['largest_pattern_group']} ({stats['largest_pattern_size']} abilities)")
        print(f"  Uncategorized abilities: {stats['uncategorized_abilities']}")
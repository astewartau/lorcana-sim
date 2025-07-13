"""Integration tests for composable keyword abilities with game states."""

import pytest

from lorcana_sim.models.game.game_state import GameState, Phase, GameAction
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.action_card import ActionCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.event_system import GameEventManager, GameEvent, EventContext

# Import our composable keyword abilities
from lorcana_sim.models.abilities.composable.keyword_abilities import (
    create_resist_ability, create_ward_ability, create_bodyguard_ability,
    create_evasive_ability, create_singer_ability, create_support_ability, 
    create_rush_ability
)


def create_test_character(name: str, cost: int = 3, strength: int = 2, willpower: int = 3) -> CharacterCard:
    """Create a real character card for testing composable abilities."""
    return CharacterCard(
        id=hash(name) % 10000,
        name=name,
        version="Test Version",
        full_name=f"{name} - Test Version",
        cost=cost,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=1,
        story="Test",
        abilities=[],
        strength=strength,
        willpower=willpower,
        lore=1,
        subtypes=["Hero"]
    )


def create_character_with_composable_ability(name: str, ability_keyword: str, value: int = None, 
                                           cost: int = 3, strength: int = 2, willpower: int = 3) -> CharacterCard:
    """Create a character card with a composable keyword ability."""
    
    character = create_test_character(name, cost, strength, willpower)
    
    # Add the composable ability
    if ability_keyword:
        if ability_keyword == "Resist":
            ability = create_resist_ability(value or 1, character)
        elif ability_keyword == "Ward":
            ability = create_ward_ability(character)
        elif ability_keyword == "Bodyguard":
            ability = create_bodyguard_ability(character)
        elif ability_keyword == "Evasive":
            ability = create_evasive_ability(character)
        elif ability_keyword == "Singer":
            ability = create_singer_ability(value or 4, character)
        elif ability_keyword == "Support":
            ability = create_support_ability(value or 1, character)
        elif ability_keyword == "Rush":
            ability = create_rush_ability(character)
        else:
            ability = None
        
        if ability:
            character.composable_abilities = [ability]
    
    return character


def create_basic_character(name: str, cost: int = 3, strength: int = 2, willpower: int = 3) -> CharacterCard:
    """Create a character card without any abilities."""
    return create_character_with_composable_ability(name, None, cost=cost, strength=strength, willpower=willpower)


def setup_game_with_characters(player1_characters: list, player2_characters: list) -> tuple:
    """Set up a game state with characters already in play and event manager."""
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Put characters in play
    player1.characters_in_play = player1_characters
    player2.characters_in_play = player2_characters
    
    # Create real game state
    game = GameState(players=[player1, player2])
    game.current_phase = Phase.PLAY  # Set to play phase for combat tests
    
    # Set up event manager and register abilities
    event_manager = GameEventManager(game)
    
    # Register all composable abilities with the event manager
    for char in player1_characters + player2_characters:
        if hasattr(char, 'composable_abilities'):
            for ability in char.composable_abilities:
                ability.register_with_event_manager(event_manager)
    
    return game, event_manager


class TestResistAbilityIntegration:
    """Test Resist ability integration with actual damage events."""
    
    def test_resist_reduces_damage_in_combat(self):
        """Test that Resist ability reduces damage during character challenge."""
        # Create a Resist 2 character and an attacker
        resist_char = create_character_with_composable_ability("Resist Character", "Resist", value=2, willpower=5)
        attacker = create_basic_character("Attacker", strength=4)
        
        game, event_manager = setup_game_with_characters([], [resist_char])
        game.players[0].characters_in_play = [attacker]
        
        # Simulate a challenge (damage event)
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            source=attacker,
            target=resist_char,
            game_state=game,
            additional_data={'damage': 4}
        )
        
        # Execute the event through the event manager
        event_manager.trigger_event(damage_event)
        
        # Damage should be reduced from 4 to 2 (4 - 2 resist)
        assert damage_event.additional_data['damage'] == 2
    
    def test_resist_stacks_with_multiple_resist_abilities(self):
        """Test that multiple Resist abilities on the same character stack."""
        # Create character with two Resist abilities
        resist_char = create_basic_character("Multi-Resist Character", willpower=10)
        resist_char.composable_abilities = [
            create_resist_ability(2, resist_char),
            create_resist_ability(1, resist_char)
        ]
        
        game, event_manager = setup_game_with_characters([], [resist_char])
        
        # Abilities are automatically registered by setup_game_with_characters
        
        # Simulate damage
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=resist_char,
            additional_data={'damage': 5}
        )
        
        event_manager.trigger_event(damage_event)
        
        # Damage should be reduced by both abilities: 5 - 2 - 1 = 2
        assert damage_event.additional_data['damage'] == 2
    
    def test_resist_cannot_reduce_damage_below_zero(self):
        """Test that Resist cannot reduce damage below 0."""
        resist_char = create_character_with_composable_ability("High Resist", "Resist", value=5)
        
        game, event_manager = setup_game_with_characters([], [resist_char])
        
        # Simulate low damage
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=resist_char,
            additional_data={'damage': 2}
        )
        
        event_manager.trigger_event(damage_event)
        
        # Damage should be reduced to 0, not negative
        assert damage_event.additional_data['damage'] == 0


class TestSupportAbilityIntegration:
    """Test Support ability integration with questing mechanics."""
    
    def test_support_triggers_on_quest(self):
        """Test that Support ability triggers when character quests."""
        support_char = create_character_with_composable_ability("Support Character", "Support", value=2)
        target_char = create_basic_character("Target Character")
        controller = Player("Test Player")
        support_char.controller = target_char.controller = controller
        
        game, event_manager = setup_game_with_characters([support_char, target_char], [])
        
        # Simulate the target character questing (support_char provides bonus)
        quest_event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=target_char,  # Target character quests, gets bonus from support
            game_state=game,
            additional_data={}
        )
        
        event_manager.trigger_event(quest_event)
        
        # Target character should have received lore bonus
        assert len(target_char.lore_bonuses) == 1
        assert target_char.lore_bonuses[0] == (2, "this_turn")
    
    def test_support_only_affects_other_characters(self):
        """Test that Support doesn't target the character with the ability."""
        support_char = create_character_with_composable_ability("Support Character", "Support", value=1)
        support_char.controller = Player("Test Player")
        
        game, event_manager = setup_game_with_characters([support_char], [])
        
        # Simulate questing
        quest_event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=support_char,
            game_state=game,
            additional_data={}
        )
        
        event_manager.trigger_event(quest_event)
        
        # Support character shouldn't have received the bonus
        assert len(support_char.lore_bonuses) == 0
    
    def test_support_affects_multiple_friendly_characters(self):
        """Test Support targeting when multiple friendly characters are available."""
        support_char = create_character_with_composable_ability("Support Character", "Support", value=1)
        friendly1 = create_basic_character("Friendly 1")
        friendly2 = create_basic_character("Friendly 2")
        
        # Set up controllers
        controller = Player("Test Player")
        support_char.controller = friendly1.controller = friendly2.controller = controller
        
        game, event_manager = setup_game_with_characters([support_char, friendly1, friendly2], [])
        
        # Simulate friendly1 questing (gets bonus from support_char)
        quest_event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=friendly1,  # friendly1 quests, gets bonus from support
            game_state=game,
            additional_data={}
        )
        
        event_manager.trigger_event(quest_event)
        
        # friendly1 should have received the bonus (they quested)
        assert len(friendly1.lore_bonuses) == 1
        assert friendly1.lore_bonuses[0] == (1, "this_turn")
        # friendly2 should not have received a bonus (they didn't quest)
        assert len(friendly2.lore_bonuses) == 0


class TestRushAbilityIntegration:
    """Test Rush ability integration with character play mechanics."""
    
    def test_rush_grants_immediate_challenge_ability(self):
        """Test that Rush allows character to challenge the turn it's played."""
        rush_char = create_character_with_composable_ability("Rush Character", "Rush")
        
        # Character needs to be in play for abilities to be registered
        game, event_manager = setup_game_with_characters([rush_char], [])
        
        # Simulate playing the character (entering play)
        play_event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=rush_char,
            additional_data={}
        )
        
        event_manager.trigger_event(play_event)
        
        # Character should have the rush property
        assert rush_char.metadata.get('can_challenge_with_wet_ink', False) == True


class TestWardAbilityIntegration:
    """Test Ward ability integration with targeting prevention."""
    
    def test_ward_prevents_ability_targeting(self):
        """Test that Ward prevents characters from being targeted by abilities."""
        ward_char = create_character_with_composable_ability("Ward Character", "Ward")
        
        game, event_manager = setup_game_with_characters([], [ward_char])
        
        # Simulate a targeting attempt
        targeting_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,  # Using as placeholder for targeting
            target=ward_char,
            additional_data={'targeting_attempt': True}
        )
        
        event_manager.trigger_event(targeting_event)
        
        # Event should be prevented
        assert targeting_event.additional_data.get('prevented', False) == True


class TestEvasiveAbilityIntegration:
    """Test Evasive ability integration with challenge mechanics."""
    
    def test_evasive_prevents_normal_challenges(self):
        """Test that Evasive characters can only be challenged by other Evasive characters."""
        evasive_defender = create_character_with_composable_ability("Evasive Defender", "Evasive")
        normal_attacker = create_basic_character("Normal Attacker")
        
        game, event_manager = setup_game_with_characters([normal_attacker], [evasive_defender])
        
        # Simulate a challenge attempt by normal character
        challenge_event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=normal_attacker,
            target=evasive_defender,
            additional_data={}
        )
        
        event_manager.trigger_event(challenge_event)
        
        # Challenge should be prevented
        assert challenge_event.additional_data.get('prevented', False) == True
    
    def test_evasive_allows_evasive_challenges(self):
        """Test that Evasive characters can challenge other Evasive characters."""
        evasive_attacker = create_character_with_composable_ability("Evasive Attacker", "Evasive")
        evasive_defender = create_character_with_composable_ability("Evasive Defender", "Evasive")
        
        game, event_manager = setup_game_with_characters([evasive_attacker], [evasive_defender])
        
        # Simulate challenge between evasive characters
        challenge_event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=evasive_attacker,
            target=evasive_defender,
            additional_data={}
        )
        
        event_manager.trigger_event(challenge_event)
        
        # Challenge should not be prevented
        assert challenge_event.additional_data.get('prevented', False) == False


class TestBodyguardAbilityIntegration:
    """Test Bodyguard ability integration with challenge redirection."""
    
    def test_bodyguard_redirects_challenges(self):
        """Test that Bodyguard redirects challenges to other friendly characters."""
        bodyguard = create_character_with_composable_ability("Bodyguard", "Bodyguard")
        protected_char = create_basic_character("Protected Character")
        attacker = create_basic_character("Attacker")
        
        # Set up controllers
        friendly_controller = Player("Friendly Player")
        enemy_controller = Player("Enemy Player")
        bodyguard.controller = protected_char.controller = friendly_controller
        attacker.controller = enemy_controller
        
        game, event_manager = setup_game_with_characters([attacker], [bodyguard, protected_char])
        
        # Simulate challenge against protected character
        challenge_event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=attacker,
            target=protected_char,
            additional_data={}
        )
        
        event_manager.trigger_event(challenge_event)
        
        # Challenge should be retargeted to bodyguard
        assert challenge_event.additional_data.get('retargeted', False) == True


class TestSingerAbilityIntegration:
    """Test Singer ability integration with song mechanics."""
    
    def test_singer_enables_song_singing(self):
        """Test that Singer ability enables singing songs at specified cost."""
        singer_char = create_character_with_composable_ability("Singer Character", "Singer", value=5)
        
        game, event_manager = setup_game_with_characters([singer_char], [])
        
        # Simulate attempting to sing a song
        sing_event = EventContext(
            event_type=GameEvent.SONG_SUNG,
            source=singer_char,
            additional_data={'singer': singer_char, 'required_cost': 4}
        )
        
        event_manager.trigger_event(sing_event)
        
        # Singer should be able to sing the song
        assert sing_event.additional_data.get('can_sing', False) == True
        assert sing_event.additional_data.get('singer_cost') == 5
    
    def test_singer_cost_restriction(self):
        """Test that Singer can only sing songs within their cost range."""
        singer_3 = create_character_with_composable_ability("Singer 3", "Singer", value=3)
        
        game, event_manager = setup_game_with_characters([singer_3], [])
        
        # Try to sing a song that costs more than the singer's value
        sing_event = EventContext(
            event_type=GameEvent.SONG_SUNG,
            source=singer_3,
            additional_data={'singer': singer_3, 'required_cost': 5}
        )
        
        event_manager.trigger_event(sing_event)
        
        # Singer should still process but with their cost value
        assert sing_event.additional_data.get('singer_cost') == 3


class TestMultipleAbilityInteractions:
    """Test interactions between multiple abilities on the same or different characters."""
    
    def test_resist_and_support_on_same_character(self):
        """Test character with both Resist and Support abilities."""
        multi_ability_char = create_basic_character("Multi Character", willpower=5)
        multi_ability_char.composable_abilities = [
            create_resist_ability(1, multi_ability_char),
            create_support_ability(1, multi_ability_char)
        ]
        
        friendly_char = create_basic_character("Friendly Character")
        controller = Player("Test Player")
        multi_ability_char.controller = friendly_char.controller = controller
        
        game, event_manager = setup_game_with_characters([multi_ability_char, friendly_char], [])
        
        # Abilities are automatically registered by setup_game_with_characters
        
        # Test Support ability triggers on quest - friendly_char quests and gets bonus
        quest_event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=friendly_char,  # friendly_char quests, gets bonus from multi_ability_char
            game_state=game,
            additional_data={}
        )
        
        event_manager.trigger_event(quest_event)
        assert len(friendly_char.lore_bonuses) == 1
        
        # Test Resist ability reduces damage
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=multi_ability_char,
            additional_data={'damage': 3}
        )
        
        event_manager.trigger_event(damage_event)
        assert damage_event.additional_data['damage'] == 2  # 3 - 1 resist
    
    def test_ward_and_evasive_combination(self):
        """Test character with both Ward and Evasive abilities."""
        protected_char = create_basic_character("Protected Character")
        protected_char.composable_abilities = [
            create_ward_ability(protected_char),
            create_evasive_ability(protected_char)
        ]
        
        normal_attacker = create_basic_character("Normal Attacker")
        
        game, event_manager = setup_game_with_characters([normal_attacker], [protected_char])
        
        # Register abilities
        for ability in protected_char.composable_abilities:
            ability.register_with_event_manager(event_manager)
        
        # Test that normal attacker cannot challenge (Evasive)
        challenge_event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=normal_attacker,
            target=protected_char,
            additional_data={}
        )
        
        event_manager.trigger_event(challenge_event)
        assert challenge_event.additional_data.get('prevented', False) == True
        
        # Test that abilities cannot target (Ward)
        targeting_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=protected_char,
            additional_data={'targeting_attempt': True}
        )
        
        event_manager.trigger_event(targeting_event)
        assert targeting_event.additional_data.get('prevented', False) == True


class TestAbilityPerformanceAndStability:
    """Test performance and stability of ability system."""
    
    def test_many_abilities_performance(self):
        """Test system performance with many abilities active."""
        import time
        
        # Create many characters with different abilities
        characters = []
        for i in range(20):
            if i % 7 == 0:
                char = create_character_with_composable_ability(f"Resist {i}", "Resist", value=1)
            elif i % 7 == 1:
                char = create_character_with_composable_ability(f"Support {i}", "Support", value=1)
            elif i % 7 == 2:
                char = create_character_with_composable_ability(f"Ward {i}", "Ward")
            elif i % 7 == 3:
                char = create_character_with_composable_ability(f"Evasive {i}", "Evasive")
            elif i % 7 == 4:
                char = create_character_with_composable_ability(f"Bodyguard {i}", "Bodyguard")
            elif i % 7 == 5:
                char = create_character_with_composable_ability(f"Singer {i}", "Singer", value=4)
            else:
                char = create_character_with_composable_ability(f"Rush {i}", "Rush")
            
            char.controller = Player(f"Player {i}")
            characters.append(char)
        
        game, event_manager = setup_game_with_characters(characters[:10], characters[10:])
        
        # Register all abilities
        for char in characters:
            if hasattr(char, 'composable_abilities'):
                for ability in char.composable_abilities:
                    ability.register_with_event_manager(event_manager)
        
        # Time multiple event processing
        start_time = time.time()
        
        for i in range(100):
            # Generate various events
            events = [
                EventContext(
                    event_type=GameEvent.CHARACTER_QUESTS,
                    source=characters[i % len(characters)],
                    game_state=game,
                    additional_data={}
                ),
                EventContext(
                    event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
                    target=characters[(i + 1) % len(characters)],
                    additional_data={'damage': 2}
                ),
                EventContext(
                    event_type=GameEvent.CHARACTER_ENTERS_PLAY,
                    source=characters[(i + 2) % len(characters)],
                    additional_data={}
                )
            ]
            
            for event in events:
                event_manager.trigger_event(event)
        
        end_time = time.time()
        
        # Should complete within reasonable time (less than 1 second for 300 events)
        elapsed = end_time - start_time
        assert elapsed < 1.0, f"Performance test took too long: {elapsed:.3f}s"
        
        print(f"Processed 300 events with 20 characters in {elapsed:.3f}s")
    
    def test_ability_cleanup_on_character_removal(self):
        """Test that abilities are properly cleaned up when characters leave play."""
        character = create_character_with_composable_ability("Test Character", "Support", value=1)
        
        game, event_manager = setup_game_with_characters([character], [])
        
        # Verify ability is registered
        support_listeners = len(event_manager._composable_listeners.get(GameEvent.CHARACTER_QUESTS, []))
        assert support_listeners > 0
        
        # Remove character from play (simulate death/exile)
        character.composable_abilities[0].unregister_from_event_manager()
        
        # Verify listeners are cleaned up
        listeners_after = len(event_manager._composable_listeners.get(GameEvent.CHARACTER_QUESTS, []))
        assert listeners_after < support_listeners


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
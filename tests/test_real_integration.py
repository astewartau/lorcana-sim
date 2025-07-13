"""Real integration tests for composable keyword abilities with actual CharacterCard objects."""

import pytest

from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.game.game_state import GameState
from lorcana_sim.engine.event_system import GameEventManager, GameEvent, EventContext

# Import our composable keyword abilities
from lorcana_sim.models.abilities.composable.keyword_abilities import (
    create_resist_ability, create_ward_ability, create_bodyguard_ability,
    create_evasive_ability, create_singer_ability, create_support_ability, 
    create_rush_ability
)


def create_character_card(name: str, cost: int = 3, strength: int = 2, willpower: int = 3, lore: int = 1) -> CharacterCard:
    """Create a real CharacterCard object."""
    return CharacterCard(
        id=hash(name) % 10000,  # Simple deterministic ID
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
        strength=strength,
        willpower=willpower,
        lore=lore,
        abilities=[]
    )


def setup_game_with_characters(player1_characters: list, player2_characters: list) -> tuple:
    """Set up a real game state with characters and event manager."""
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Set up controllers
    for char in player1_characters:
        char.controller = player1
    for char in player2_characters:
        char.controller = player2
    
    # Put characters in play
    player1.characters_in_play = player1_characters
    player2.characters_in_play = player2_characters
    
    game = GameState(players=[player1, player2])
    
    # Set up event manager
    event_manager = GameEventManager(game)
    
    # Register all composable abilities with the event manager
    for char in player1_characters + player2_characters:
        char.register_composable_abilities(event_manager)
    
    return game, event_manager


class TestResistAbilityRealIntegration:
    """Test Resist ability with real CharacterCard objects."""
    
    def test_resist_reduces_damage_with_real_character(self):
        """Test Resist ability reduces damage on real character."""
        # Create real character
        character = create_character_card("Resist Character", willpower=5)
        
        # Add resist ability
        resist_ability = create_resist_ability(2, character)
        character.add_composable_ability(resist_ability)
        
        game, event_manager = setup_game_with_characters([], [character])
        
        # Create damage event
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=character,
            game_state=game,
            additional_data={'damage': 4}
        )
        
        # Trigger through event manager
        event_manager.trigger_event(damage_event)
        
        # Damage should be reduced from 4 to 2
        assert damage_event.additional_data['damage'] == 2
    
    def test_resist_cannot_reduce_below_zero(self):
        """Test Resist cannot reduce damage below 0."""
        character = create_character_card("High Resist Character")
        
        resist_ability = create_resist_ability(10, character)
        character.add_composable_ability(resist_ability)
        
        game, event_manager = setup_game_with_characters([], [character])
        
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=character,
            game_state=game,
            additional_data={'damage': 3}
        )
        
        event_manager.trigger_event(damage_event)
        
        # Should be reduced to 0, not negative
        assert damage_event.additional_data['damage'] == 0


class TestSupportAbilityRealIntegration:
    """Test Support ability with real CharacterCard objects."""
    
    def test_support_gives_lore_bonus_to_real_character(self):
        """Test Support ability gives lore bonus to real character."""
        support_char = create_character_card("Support Character")
        target_char = create_character_card("Target Character")
        
        # Add support ability
        support_ability = create_support_ability(2, support_char)
        support_char.add_composable_ability(support_ability)
        
        game, event_manager = setup_game_with_characters([support_char, target_char], [])
        
        # Verify target starts with no bonuses
        assert len(target_char.lore_bonuses) == 0
        assert target_char.current_lore == 1  # Base lore
        
        # Create quest event - target_char quests, gets bonus from support_char
        quest_event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=target_char,  # target_char quests, gets bonus from support_char
            game_state=game,
            additional_data={}
        )
        
        event_manager.trigger_event(quest_event)
        
        # Target should have received lore bonus
        assert len(target_char.lore_bonuses) == 1
        assert target_char.lore_bonuses[0] == (2, "this_turn")
        assert target_char.current_lore == 3  # Base 1 + bonus 2
    
    def test_support_only_targets_other_characters(self):
        """Test Support doesn't give bonus to itself."""
        support_char = create_character_card("Support Character")
        
        support_ability = create_support_ability(1, support_char)
        support_char.add_composable_ability(support_ability)
        
        game, event_manager = setup_game_with_characters([support_char], [])
        
        quest_event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=support_char,
            game_state=game,
            additional_data={}
        )
        
        event_manager.trigger_event(quest_event)
        
        # Support character shouldn't have received the bonus
        assert len(support_char.lore_bonuses) == 0
        assert support_char.current_lore == 1  # Only base lore


class TestRushAbilityRealIntegration:
    """Test Rush ability with real CharacterCard objects."""
    
    def test_rush_grants_immediate_challenge_ability(self):
        """Test Rush grants immediate challenge ability to real character."""
        character = create_character_card("Rush Character")
        
        rush_ability = create_rush_ability(character)
        character.add_composable_ability(rush_ability)
        
        game, event_manager = setup_game_with_characters([character], [])
        
        # Character starts without rush property
        assert character.metadata.get('can_challenge_with_wet_ink', False) == False
        
        # Simulate character entering play
        play_event = EventContext(
            event_type=GameEvent.CHARACTER_ENTERS_PLAY,
            source=character,
            game_state=game,
            additional_data={}
        )
        
        event_manager.trigger_event(play_event)
        
        # Character should now have rush property
        assert character.metadata.get('can_challenge_with_wet_ink', False) == True


class TestWardAbilityRealIntegration:
    """Test Ward ability with real CharacterCard objects."""
    
    def test_ward_prevents_targeting(self):
        """Test Ward prevents ability targeting."""
        character = create_character_card("Ward Character")
        
        ward_ability = create_ward_ability(character)
        character.add_composable_ability(ward_ability)
        
        game, event_manager = setup_game_with_characters([], [character])
        
        # Create targeting event
        targeting_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,  # Using as placeholder
            target=character,
            game_state=game,
            additional_data={'targeting_attempt': True}
        )
        
        event_manager.trigger_event(targeting_event)
        
        # Event should be prevented
        assert targeting_event.additional_data.get('prevented', False) == True


class TestEvasiveAbilityRealIntegration:
    """Test Evasive ability with real CharacterCard objects."""
    
    def test_evasive_prevents_normal_challenges(self):
        """Test Evasive prevents challenges from non-evasive characters."""
        evasive_char = create_character_card("Evasive Character")
        normal_attacker = create_character_card("Normal Attacker")
        
        evasive_ability = create_evasive_ability(evasive_char)
        evasive_char.add_composable_ability(evasive_ability)
        
        game, event_manager = setup_game_with_characters([normal_attacker], [evasive_char])
        
        challenge_event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=normal_attacker,
            target=evasive_char,
            game_state=game,
            additional_data={}
        )
        
        event_manager.trigger_event(challenge_event)
        
        # Challenge should be prevented
        assert challenge_event.additional_data.get('prevented', False) == True


class TestSingerAbilityRealIntegration:
    """Test Singer ability with real CharacterCard objects."""
    
    def test_singer_enables_song_singing(self):
        """Test Singer ability enables singing songs."""
        character = create_character_card("Singer Character")
        
        singer_ability = create_singer_ability(5, character)
        character.add_composable_ability(singer_ability)
        
        game, event_manager = setup_game_with_characters([character], [])
        
        sing_event = EventContext(
            event_type=GameEvent.SONG_SUNG,
            source=character,
            game_state=game,
            additional_data={'singer': character, 'required_cost': 4}
        )
        
        event_manager.trigger_event(sing_event)
        
        # Should enable singing
        assert sing_event.additional_data.get('can_sing', False) == True
        assert sing_event.additional_data.get('singer_cost') == 5


class TestBodyguardAbilityRealIntegration:
    """Test Bodyguard ability with real CharacterCard objects."""
    
    def test_bodyguard_redirects_challenges(self):
        """Test Bodyguard redirects challenges."""
        bodyguard = create_character_card("Bodyguard")
        protected_char = create_character_card("Protected Character")
        attacker = create_character_card("Attacker")
        
        bodyguard_ability = create_bodyguard_ability(bodyguard)
        bodyguard.add_composable_ability(bodyguard_ability)
        
        # Set up game with bodyguard and protected on one side, attacker on other
        game, event_manager = setup_game_with_characters([attacker], [bodyguard, protected_char])
        
        challenge_event = EventContext(
            event_type=GameEvent.CHARACTER_CHALLENGES,
            source=attacker,
            target=protected_char,
            game_state=game,
            additional_data={}
        )
        
        event_manager.trigger_event(challenge_event)
        
        # Challenge should be retargeted
        assert challenge_event.additional_data.get('retargeted', False) == True


class TestMultipleAbilitiesRealIntegration:
    """Test multiple abilities on real characters."""
    
    def test_character_with_resist_and_support(self):
        """Test character with both Resist and Support abilities."""
        multi_char = create_character_card("Multi Character", willpower=5)
        friendly_char = create_character_card("Friendly Character")
        
        # Add both abilities
        resist_ability = create_resist_ability(1, multi_char)
        support_ability = create_support_ability(2, multi_char)
        multi_char.add_composable_ability(resist_ability)
        multi_char.add_composable_ability(support_ability)
        
        game, event_manager = setup_game_with_characters([multi_char, friendly_char], [])
        
        # Test Support triggers on quest - friendly_char quests, gets bonus from multi_char
        quest_event = EventContext(
            event_type=GameEvent.CHARACTER_QUESTS,
            source=friendly_char,  # friendly_char quests, gets bonus from multi_char
            game_state=game,
            additional_data={}
        )
        
        event_manager.trigger_event(quest_event)
        
        # Friendly character should have received lore bonus
        assert len(friendly_char.lore_bonuses) == 1
        assert friendly_char.lore_bonuses[0] == (2, "this_turn")
        assert friendly_char.current_lore == 3  # Base 1 + bonus 2
        
        # Test Resist reduces damage
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=multi_char,
            game_state=game,
            additional_data={'damage': 4}
        )
        
        event_manager.trigger_event(damage_event)
        
        # Damage should be reduced
        assert damage_event.additional_data['damage'] == 3  # 4 - 1 resist
    
    def test_stat_bonus_persistence(self):
        """Test that stat bonuses persist and affect current_* properties."""
        character = create_character_card("Test Character", strength=2, willpower=3, lore=1)
        
        # Add various bonuses
        character.add_strength_bonus(1, "permanent")
        character.add_strength_bonus(2, "this_turn")
        character.add_willpower_bonus(1, "this_turn")
        character.add_lore_bonus(3, "permanent")
        
        # Check current values include bonuses
        assert character.current_strength == 5  # 2 + 1 + 2
        assert character.current_willpower == 4  # 3 + 1
        assert character.current_lore == 4  # 1 + 3
        
        # Clear temporary bonuses
        character.clear_temporary_bonuses()
        
        # Only permanent bonuses should remain
        assert character.current_strength == 3  # 2 + 1 (permanent only)
        assert character.current_willpower == 3  # 3 (no permanent bonus)
        assert character.current_lore == 4  # 1 + 3 (permanent bonus remains)


class TestEventSystemIntegration:
    """Test event system integration with composable abilities."""
    
    def test_event_manager_handles_composable_abilities(self):
        """Test that GameEventManager properly handles composable abilities."""
        character = create_character_card("Test Character")
        
        resist_ability = create_resist_ability(1, character)
        character.add_composable_ability(resist_ability)
        
        game, event_manager = setup_game_with_characters([], [character])
        
        # Verify ability is registered
        assert len(event_manager._composable_listeners.get(GameEvent.CHARACTER_TAKES_DAMAGE, [])) > 0
        
        # Test event triggering
        damage_event = EventContext(
            event_type=GameEvent.CHARACTER_TAKES_DAMAGE,
            target=character,
            game_state=game,
            additional_data={'damage': 3}
        )
        
        results = event_manager.trigger_event(damage_event)
        
        # Should have triggered the ability
        assert len(results) > 0
        assert any("composable ability" in result.lower() for result in results)
        assert damage_event.additional_data['damage'] == 2  # 3 - 1 resist


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""Tests for the ink drying (summoning sickness) system."""

import pytest
from lorcana_sim.abilities.keywords import KeywordRegistry
from lorcana_sim.models.game.game_state import GameAction
from tests.helpers import (
    create_test_character, create_character_with_ability,
    setup_game_with_characters, advance_to_main_phase
)


class TestInkDryingSystem:
    """Test the ink drying (summoning sickness) system."""
    
    def test_character_is_dry_when_turn_played_is_none(self):
        """Test that characters with no turn_played are considered dry."""
        char = create_test_character("Test Character")
        assert char.turn_played is None
        assert char.is_dry(1) == True
        assert char.is_dry(5) == True
    
    def test_character_has_wet_ink_on_turn_played(self):
        """Test that characters have wet ink on the turn they're played."""
        char = create_test_character("Test Character")
        char.turn_played = 3  # Played on turn 3
        
        # Ink is wet on the same turn
        assert char.is_dry(3) == False
        # Ink dries on subsequent turns
        assert char.is_dry(4) == True
        assert char.is_dry(5) == True
    
    def test_normal_character_cannot_quest_with_wet_ink(self):
        """Test that normal characters cannot quest on the turn they're played."""
        char = create_test_character("Normal Character")
        char.turn_played = 2
        char.exerted = False
        
        # Cannot quest on turn played (wet ink)
        assert char.can_quest(2) == False
        # Can quest on subsequent turns (dry ink)
        assert char.can_quest(3) == True
    
    def test_normal_character_cannot_challenge_with_wet_ink(self):
        """Test that normal characters cannot challenge on the turn they're played."""
        char = create_test_character("Normal Character")
        char.turn_played = 2
        char.exerted = False
        
        # Cannot challenge on turn played (wet ink)
        assert char.can_challenge(2) == False
        # Can challenge on subsequent turns (dry ink)
        assert char.can_challenge(3) == True
    
    def test_rush_character_can_challenge_with_wet_ink(self):
        """Test that Rush characters can challenge on the turn they're played."""
        rush_ability = KeywordRegistry.create_keyword_ability('Rush')
        char = create_character_with_ability("Rush Character", rush_ability)
        char.turn_played = 2
        char.exerted = False
        
        # Rush allows challenging even with wet ink
        assert char.can_challenge(2) == True
        assert char.can_challenge(3) == True
    
    def test_rush_character_still_cannot_quest_with_wet_ink(self):
        """Test that Rush doesn't affect questing - characters still need dry ink to quest."""
        rush_ability = KeywordRegistry.create_keyword_ability('Rush')
        char = create_character_with_ability("Rush Character", rush_ability)
        char.turn_played = 2
        char.exerted = False
        
        # Rush doesn't affect questing - still needs dry ink
        assert char.can_quest(2) == False
        assert char.can_quest(3) == True
    
    def test_exerted_character_cannot_act_regardless_of_ink_state(self):
        """Test that exerted characters cannot act even with dry ink."""
        char = create_test_character("Exerted Character")
        char.turn_played = 1  # Old character with dry ink
        char.exerted = True
        
        # Cannot act when exerted, even with dry ink
        assert char.can_quest(5) == False
        assert char.can_challenge(5) == False
    
    def test_dead_character_cannot_act_regardless_of_ink_state(self):
        """Test that dead characters cannot act even with dry ink."""
        char = create_test_character("Dead Character", willpower=3)
        char.turn_played = 1  # Old character with dry ink
        char.damage = 5  # More damage than willpower
        char.exerted = False
        
        # Cannot act when dead, even with dry ink
        assert char.is_alive == False
        assert char.can_quest(5) == False
        assert char.can_challenge(5) == False


class TestInkDryingGameIntegration:
    """Test ink drying system integration with game mechanics."""
    
    def test_character_gets_turn_played_when_played(self):
        """Test that characters get turn_played set when played."""
        char = create_test_character("Test Character", cost=2)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([], [])
        
        # Add character to hand and give ink
        game_state.current_player.hand.append(char)
        for i in range(5):
            dummy_ink = create_test_character(f"Ink{i}")
            game_state.current_player.inkwell.append(dummy_ink)
        
        # Set to main phase
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        
        # Play the character
        initial_turn = game_state.turn_number
        success, message = engine.execute_action(GameAction.PLAY_CHARACTER, {'card': char})
        
        assert success == True
        assert char.turn_played == initial_turn
        assert char.is_dry(initial_turn) == False  # Wet ink on turn played
        assert char.is_dry(initial_turn + 1) == True  # Dry ink next turn
    
    def test_normal_character_cannot_quest_turn_played(self):
        """Test that normal characters cannot quest on the turn they're played."""
        char = create_test_character("Normal Character", cost=1, lore=2)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([], [])
        
        # Add character to hand and give ink
        game_state.current_player.hand.append(char)
        for i in range(3):
            dummy_ink = create_test_character(f"Ink{i}")
            game_state.current_player.inkwell.append(dummy_ink)
        
        # Set to main phase and play character
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        engine.execute_action(GameAction.PLAY_CHARACTER, {'card': char})
        
        # Try to quest - should fail due to wet ink
        legal_actions = validator.get_all_legal_actions()
        quest_actions = [(action, params) for action, params in legal_actions 
                        if action == GameAction.QUEST_CHARACTER]
        
        assert len(quest_actions) == 0  # No quest actions available
        
        # Verify direct check
        assert char.can_quest(game_state.turn_number) == False
    
    def test_normal_character_cannot_challenge_turn_played(self):
        """Test that normal characters cannot challenge on the turn they're played."""
        attacker = create_test_character("Normal Attacker", cost=1, strength=2)
        defender = create_test_character("Defender", willpower=3)
        
        # Setup game with defender already in play
        game_state, validator, engine = setup_game_with_characters([], [defender])
        
        # Add attacker to hand and give ink
        game_state.current_player.hand.append(attacker)
        for i in range(3):
            dummy_ink = create_test_character(f"Ink{i}")
            game_state.current_player.inkwell.append(dummy_ink)
        
        # Set to main phase and play attacker
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        engine.execute_action(GameAction.PLAY_CHARACTER, {'card': attacker})
        
        # Try to challenge - should fail due to wet ink
        legal_actions = validator.get_all_legal_actions()
        challenge_actions = [(action, params) for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        assert len(challenge_actions) == 0  # No challenge actions available
        
        # Verify direct check
        assert attacker.can_challenge(game_state.turn_number) == False
    
    def test_rush_character_can_challenge_turn_played(self):
        """Test that Rush characters can challenge on the turn they're played."""
        rush_ability = KeywordRegistry.create_keyword_ability('Rush')
        attacker = create_character_with_ability("Rush Attacker", rush_ability, cost=1, strength=2)
        defender = create_test_character("Defender", willpower=3)
        
        # Setup game with defender in play
        game_state, validator, engine = setup_game_with_characters([], [defender])
        
        # Add rush attacker to hand and give ink
        game_state.current_player.hand.append(attacker)
        for i in range(3):
            dummy_ink = create_test_character(f"Ink{i}")
            game_state.current_player.inkwell.append(dummy_ink)
        
        # Set to main phase and play rush character
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        engine.execute_action(GameAction.PLAY_CHARACTER, {'card': attacker})
        
        # Rush character should be able to challenge immediately
        legal_actions = validator.get_all_legal_actions()
        challenge_actions = [(action, params) for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        assert len(challenge_actions) == 1  # Rush enables challenge
        action, params = challenge_actions[0]
        assert params['attacker'] == attacker
        assert params['defender'] == defender
        
        # Verify direct check
        assert attacker.can_challenge(game_state.turn_number) == True
    
    def test_rush_character_still_cannot_quest_turn_played(self):
        """Test that Rush doesn't affect questing - still need dry ink."""
        rush_ability = KeywordRegistry.create_keyword_ability('Rush')
        char = create_character_with_ability("Rush Character", rush_ability, cost=1, lore=2)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([], [])
        
        # Add character to hand and give ink
        game_state.current_player.hand.append(char)
        for i in range(3):
            dummy_ink = create_test_character(f"Ink{i}")
            game_state.current_player.inkwell.append(dummy_ink)
        
        # Set to main phase and play rush character
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        engine.execute_action(GameAction.PLAY_CHARACTER, {'card': char})
        
        # Rush character should NOT be able to quest (only affects challenges)
        legal_actions = validator.get_all_legal_actions()
        quest_actions = [(action, params) for action, params in legal_actions 
                        if action == GameAction.QUEST_CHARACTER]
        
        assert len(quest_actions) == 0  # No quest actions even with Rush
        
        # Verify direct check
        assert char.can_quest(game_state.turn_number) == False
    
    def test_character_can_act_after_turn_passes(self):
        """Test that characters can act normally after their ink dries."""
        char = create_test_character("Test Character", cost=1, strength=2, lore=1)
        defender = create_test_character("Defender", willpower=3)
        
        # Setup game
        game_state, validator, engine = setup_game_with_characters([], [defender])
        
        # Add character to hand and give ink
        game_state.current_player.hand.append(char)
        for i in range(3):
            dummy_ink = create_test_character(f"Ink{i}")
            game_state.current_player.inkwell.append(dummy_ink)
        
        # Set to main phase and play character
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        engine.execute_action(GameAction.PLAY_CHARACTER, {'card': char})
        
        # Pass turn to let ink dry - need to simulate complete round
        game_state.end_turn()  # Player 1 -> Player 2 (still turn 1)
        game_state.end_turn()  # Player 2 -> Player 1 (now turn 2)
        
        # On the next turn, character should be able to act
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        legal_actions = validator.get_all_legal_actions()
        
        quest_actions = [(action, params) for action, params in legal_actions 
                        if action == GameAction.QUEST_CHARACTER]
        challenge_actions = [(action, params) for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        # Character should now be able to quest and challenge
        assert len(quest_actions) == 1
        assert len(challenge_actions) == 1
        
        # Verify direct checks
        assert char.can_quest(game_state.turn_number) == True
        assert char.can_challenge(game_state.turn_number) == True
    
    def test_multiple_characters_different_ink_states(self):
        """Test multiple characters with different ink drying states."""
        # Create characters
        old_char = create_test_character("Old Character", strength=2, lore=1)
        old_char.turn_played = 1  # Played earlier, dry ink
        
        rush_char = create_character_with_ability(
            "Rush Character", 
            KeywordRegistry.create_keyword_ability('Rush'),
            strength=3, lore=1
        )
        
        normal_char = create_test_character("Normal Character", strength=2, lore=1)
        defender = create_test_character("Defender", willpower=5)
        
        # Setup game with old character and defender in play
        game_state, validator, engine = setup_game_with_characters([old_char], [defender])
        
        # Set current turn to 3
        game_state.turn_number = 3
        
        # Add new characters to hand and give ink
        game_state.current_player.hand.extend([rush_char, normal_char])
        for i in range(10):
            dummy_ink = create_test_character(f"Ink{i}")
            game_state.current_player.inkwell.append(dummy_ink)
        
        # Set to main phase and play both characters
        from lorcana_sim.models.game.game_state import Phase
        game_state.current_phase = Phase.MAIN
        engine.execute_action(GameAction.PLAY_CHARACTER, {'card': rush_char})
        engine.execute_action(GameAction.PLAY_CHARACTER, {'card': normal_char})
        
        # Check action availability
        legal_actions = validator.get_all_legal_actions()
        quest_actions = [(action, params) for action, params in legal_actions 
                        if action == GameAction.QUEST_CHARACTER]
        challenge_actions = [(action, params) for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        # Only old character can quest (dry ink)
        quest_characters = [params['character'] for action, params in quest_actions]
        assert old_char in quest_characters
        assert rush_char not in quest_characters  # Rush doesn't affect questing
        assert normal_char not in quest_characters
        
        # Old character and rush character can challenge
        challenge_attackers = [params['attacker'] for action, params in challenge_actions]
        assert old_char in challenge_attackers  # Dry ink
        assert rush_char in challenge_attackers  # Rush bypasses wet ink
        assert normal_char not in challenge_attackers  # Wet ink, no Rush
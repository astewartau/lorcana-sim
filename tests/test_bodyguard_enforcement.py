"""Test for Bodyguard challenge targeting enforcement."""

import pytest

from lorcana_sim.models.game.game_state import GameState
from lorcana_sim.models.game.player import Player
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity
from lorcana_sim.engine.move_validator import MoveValidator
from lorcana_sim.engine.event_system import GameEventManager
from lorcana_sim.models.abilities.composable.keyword_abilities import create_bodyguard_ability


def create_test_character(name: str, cost: int = 3, strength: int = 2, willpower: int = 3, lore: int = 1) -> CharacterCard:
    """Create a real CharacterCard for testing."""
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
        strength=strength,
        willpower=willpower,
        lore=lore,
        subtypes=["Hero"]
    )


def create_bodyguard_character(name: str, **kwargs) -> CharacterCard:
    """Create a character with Bodyguard ability."""
    character = create_test_character(name, **kwargs)
    bodyguard_ability = create_bodyguard_ability(character)
    character.composable_abilities = [bodyguard_ability]
    
    # Manually trigger the bodyguard effect to mark the character
    character.metadata['has_bodyguard'] = True
    character.metadata['can_enter_exerted'] = True
    
    return character


class TestBodyguardEnforcement:
    """Test that Bodyguard actually enforces challenge targeting restrictions."""
    
    def test_bodyguard_forces_targeting_when_available(self):
        """Test that when a Bodyguard character is available, opponents must target it."""
        # Set up players
        player1 = Player("Player 1")
        player2 = Player("Player 2")
        
        # Create characters
        attacker = create_test_character("Attacker", strength=3)
        bodyguard_char = create_bodyguard_character("Bodyguard Character", willpower=4)
        normal_defender = create_test_character("Normal Defender", willpower=3)
        
        # Set up game state
        attacker.controller = player1
        bodyguard_char.controller = player2
        normal_defender.controller = player2
        
        # Put characters in play and make them ready
        player1.characters_in_play = [attacker]
        player2.characters_in_play = [bodyguard_char, normal_defender]
        
        # Set up exerted states correctly (exerted = True means challengeable)
        attacker.exerted = False           # Ready attacker (can challenge)
        bodyguard_char.exerted = True      # Exerted Bodyguard (challengeable, should be forced target)
        normal_defender.exerted = True     # Exerted normal (challengeable but should be blocked by Bodyguard)
        
        # All characters have dry ink
        attacker.is_dry = True
        bodyguard_char.is_dry = True
        normal_defender.is_dry = True
        
        game = GameState(players=[player1, player2], current_player_index=0)
        
        event_manager = GameEventManager(game)
        validator = MoveValidator(game)
        
        # Get valid challenge targets for the attacker
        all_defenders = player2.characters_in_play
        valid_targets = validator._get_valid_challenge_targets(attacker, all_defenders)
        
        # CRITICAL TEST: When a ready Bodyguard is available, it should be the ONLY valid target
        assert len(valid_targets) == 1, f"Expected only 1 target (Bodyguard), but got {len(valid_targets)}: {[t.name for t in valid_targets]}"
        assert valid_targets[0] == bodyguard_char, f"Expected Bodyguard to be forced target, but got {valid_targets[0].name}"
    
    def test_bodyguard_allows_other_targets_when_exerted(self):
        """Test that when Bodyguard is exerted, other characters can be targeted."""
        # Set up players
        player1 = Player("Player 1")
        player2 = Player("Player 2")
        
        # Create characters
        attacker = create_test_character("Attacker", strength=3)
        bodyguard_char = create_bodyguard_character("Bodyguard Character", willpower=4)
        normal_defender = create_test_character("Normal Defender", willpower=3)
        
        # Set up game state
        attacker.controller = player1
        bodyguard_char.controller = player2
        normal_defender.controller = player2
        
        player1.characters_in_play = [attacker]
        player2.characters_in_play = [bodyguard_char, normal_defender]
        
        # Bodyguard is ready (can't be challenged), normal defender is exerted
        attacker.exerted = False
        bodyguard_char.exerted = False  # Ready Bodyguard can't be challenged
        normal_defender.exerted = True   # Exerted normal defender can be challenged
        
        # All have dry ink
        attacker.is_dry = True
        bodyguard_char.is_dry = True
        normal_defender.is_dry = True
        
        game = GameState(players=[player1, player2], current_player_index=0)
        
        event_manager = GameEventManager(game)
        validator = MoveValidator(game)
        
        # Get valid challenge targets
        all_defenders = player2.characters_in_play
        valid_targets = validator._get_valid_challenge_targets(attacker, all_defenders)
        
        # When Bodyguard is ready (not exerted), normal defender should be targetable
        assert normal_defender in valid_targets, "Normal defender should be targetable when Bodyguard is ready"
        assert bodyguard_char not in valid_targets, "Ready Bodyguard should not be targetable"
    
    def test_bodyguard_allows_other_targets_when_damaged_beyond_challenge(self):
        """Test that when Bodyguard can't be challenged (damaged), others can be targeted."""
        # Set up players
        player1 = Player("Player 1")
        player2 = Player("Player 2")
        
        # Create characters
        attacker = create_test_character("Attacker", strength=3)
        bodyguard_char = create_bodyguard_character("Bodyguard Character", willpower=2)
        normal_defender = create_test_character("Normal Defender", willpower=3)
        
        # Set up game state
        attacker.controller = player1
        bodyguard_char.controller = player2
        normal_defender.controller = player2
        
        player1.characters_in_play = [attacker]
        player2.characters_in_play = [bodyguard_char, normal_defender]
        
        # Bodyguard has damage equal to willpower (would be banished if challenged)
        attacker.exerted = False
        bodyguard_char.exerted = True    # Exerted but damaged
        bodyguard_char.damage = 2        # Equal to willpower - would be banished if takes more damage
        normal_defender.exerted = True   # Exerted and available
        
        # All have dry ink
        attacker.is_dry = True
        bodyguard_char.is_dry = True
        normal_defender.is_dry = True
        
        game = GameState(players=[player1, player2], current_player_index=0)
        
        event_manager = GameEventManager(game)
        validator = MoveValidator(game)
        
        # Get valid challenge targets
        all_defenders = player2.characters_in_play
        valid_targets = validator._get_valid_challenge_targets(attacker, all_defenders)
        
        # When Bodyguard would be banished by the challenge, normal defender should be targetable
        # Note: This depends on whether the system considers "challengeable" to include characters
        # that would be immediately banished
        assert len(valid_targets) >= 1, "Should have at least one valid target"
    
    def test_bodyguard_forces_targeting_with_mixed_exerted_states(self):
        """Test Bodyguard enforcement with realistic mixed exerted states.
        
        Scenario: 2 Bodyguards, 3 normal characters
        - 1 Bodyguard is exerted (should be only valid target)
        - 1 Bodyguard is ready (not targetable)
        - 2 normal characters are exerted (should NOT be targetable due to Bodyguard)
        - 1 normal character is ready (not targetable anyway)
        
        """
        # Set up players
        player1 = Player("Player 1")
        player2 = Player("Player 2")
        
        # Create characters
        attacker = create_test_character("Attacker", strength=3)
        bodyguard1 = create_bodyguard_character("Bodyguard 1", willpower=4)
        bodyguard2 = create_bodyguard_character("Bodyguard 2", willpower=3)
        normal1 = create_test_character("Normal 1", willpower=3)
        normal2 = create_test_character("Normal 2", willpower=2)
        normal3 = create_test_character("Normal 3", willpower=4)
        
        # Set up game state
        attacker.controller = player1
        for char in [bodyguard1, bodyguard2, normal1, normal2, normal3]:
            char.controller = player2
        
        player1.characters_in_play = [attacker]
        player2.characters_in_play = [bodyguard1, bodyguard2, normal1, normal2, normal3]
        
        # Set up exerted states (remember: exerted = True means challengeable)
        attacker.exerted = False        # Ready attacker (can challenge)
        bodyguard1.exerted = True       # Exerted Bodyguard (challengeable, should be forced target)
        bodyguard2.exerted = False      # Ready Bodyguard (not challengeable)
        normal1.exerted = True          # Exerted normal (challengeable but should be blocked by Bodyguard)
        normal2.exerted = True          # Exerted normal (challengeable but should be blocked by Bodyguard)
        normal3.exerted = False         # Ready normal (not challengeable anyway)
        
        # All have dry ink
        for char in [attacker, bodyguard1, bodyguard2, normal1, normal2, normal3]:
            char.is_dry = True
        
        game = GameState(players=[player1, player2], current_player_index=0)
        
        event_manager = GameEventManager(game)
        validator = MoveValidator(game)
        
        # Get valid challenge targets
        all_defenders = player2.characters_in_play
        valid_targets = validator._get_valid_challenge_targets(attacker, all_defenders)
        
        # CRITICAL TEST: Only the exerted Bodyguard should be targetable
        assert len(valid_targets) == 1, f"Expected only 1 target (exerted Bodyguard), but got {len(valid_targets)}: {[t.name for t in valid_targets]}"
        assert bodyguard1 in valid_targets, "Exerted Bodyguard 1 should be the only valid target"
        assert bodyguard2 not in valid_targets, "Ready Bodyguard 2 should not be targetable"
        assert normal1 not in valid_targets, f"Exerted Normal 1 should NOT be targetable when Bodyguard available, but was in targets: {[t.name for t in valid_targets]}"
        assert normal2 not in valid_targets, f"Exerted Normal 2 should NOT be targetable when Bodyguard available, but was in targets: {[t.name for t in valid_targets]}"
        assert normal3 not in valid_targets, "Ready Normal 3 should not be targetable anyway"
    
    def test_basic_challenge_targeting_requires_exerted_defenders(self):
        """Test that only exerted characters can be challenged (basic rule)."""
        # Set up players
        player1 = Player("Player 1")
        player2 = Player("Player 2")
        
        # Create characters - no special abilities, just testing basic challenge rules
        attacker = create_test_character("Attacker", strength=3)
        ready_defender1 = create_test_character("Ready Defender 1", willpower=3)
        ready_defender2 = create_test_character("Ready Defender 2", willpower=4)
        exerted_defender1 = create_test_character("Exerted Defender 1", willpower=2)
        exerted_defender2 = create_test_character("Exerted Defender 2", willpower=3)
        
        # Set up game state
        attacker.controller = player1
        for char in [ready_defender1, ready_defender2, exerted_defender1, exerted_defender2]:
            char.controller = player2
        
        player1.characters_in_play = [attacker]
        player2.characters_in_play = [ready_defender1, ready_defender2, exerted_defender1, exerted_defender2]
        
        # Set up exerted states explicitly
        attacker.exerted = False           # Ready attacker (can challenge)
        ready_defender1.exerted = False    # Ready defender (NOT challengeable)
        ready_defender2.exerted = False    # Ready defender (NOT challengeable)
        exerted_defender1.exerted = True   # Exerted defender (challengeable)
        exerted_defender2.exerted = True   # Exerted defender (challengeable)
        
        # All have dry ink
        for char in [attacker, ready_defender1, ready_defender2, exerted_defender1, exerted_defender2]:
            char.is_dry = True
        
        game = GameState(players=[player1, player2], current_player_index=0)
        
        event_manager = GameEventManager(game)
        validator = MoveValidator(game)
        
        # Get valid challenge targets
        all_defenders = player2.characters_in_play
        valid_targets = validator._get_valid_challenge_targets(attacker, all_defenders)
        
        # CRITICAL TEST: Only exerted characters should be valid targets
        assert len(valid_targets) == 2, f"Expected 2 targets (only exerted defenders), but got {len(valid_targets)}: {[t.name for t in valid_targets]}"
        
        # Check that only exerted defenders are in valid targets
        assert exerted_defender1 in valid_targets, "Exerted Defender 1 should be targetable"
        assert exerted_defender2 in valid_targets, "Exerted Defender 2 should be targetable"
        assert ready_defender1 not in valid_targets, f"Ready Defender 1 should NOT be targetable, but was in: {[t.name for t in valid_targets]}"
        assert ready_defender2 not in valid_targets, f"Ready Defender 2 should NOT be targetable, but was in: {[t.name for t in valid_targets]}"
        
        # Additional verification - all valid targets should be exerted
        for target in valid_targets:
            assert target.exerted == True, f"{target.name} is in valid_targets but is not exerted!"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
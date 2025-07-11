"""Integration tests for abilities with game state."""

import pytest
from dataclasses import dataclass
from typing import List

from src.lorcana_sim.models.game.game_state import GameState, Phase, GameAction
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.action_card import ActionCard
from src.lorcana_sim.models.cards.base_card import Card, CardColor, Rarity
from src.lorcana_sim.models.abilities.base_ability import Ability, AbilityType
from src.lorcana_sim.abilities.keywords import SingerAbility, EvasiveAbility, BodyguardAbility
from src.lorcana_sim.engine.move_validator import MoveValidator
from src.lorcana_sim.engine.game_engine import GameEngine


def create_character_with_ability(name: str, ability_keyword: str, value: int = None, 
                                 cost: int = 3, strength: int = 2, willpower: int = 3) -> CharacterCard:
    """Create a character card with a specific keyword ability."""
    if ability_keyword == "Singer":
        ability = SingerAbility(
            name="Singer",
            type=AbilityType.KEYWORD,
            effect=f"Singer {value}" if value else "Singer",
            full_text=f"Singer {value}" if value else "Singer",
            keyword="Singer",
            value=value
        )
    elif ability_keyword == "Evasive":
        ability = EvasiveAbility(
            name="Evasive",
            type=AbilityType.KEYWORD,
            effect="Only characters with Evasive can challenge this character",
            full_text="Evasive",
            keyword="Evasive",
            value=None
        )
    elif ability_keyword == "Bodyguard":
        ability = BodyguardAbility(
            name="Bodyguard",
            type=AbilityType.KEYWORD,
            effect="Opponents must challenge this character if able",
            full_text="Bodyguard",
            keyword="Bodyguard",
            value=None
        )
    else:
        ability = None
    
    return CharacterCard(
        id=1,
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
        lore=1,
        abilities=[ability] if ability else []
    )


def create_song_card(name: str, cost: int, singer_cost: int) -> ActionCard:
    """Create a song action card."""
    song_ability = Ability(
        name="Song Effect",
        type=AbilityType.STATIC,
        effect=f"A character with cost {singer_cost} or more can sing this song for free.",
        full_text=f"A character with cost {singer_cost} or more can sing this song for free."
    )
    
    return ActionCard(
        id=2,
        name=name,
        version=None,
        full_name=name,
        cost=cost,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=2,
        story="Test",
        abilities=[song_ability]
    )


def setup_game_with_characters(player1_characters: List[CharacterCard], 
                              player2_characters: List[CharacterCard]) -> tuple:
    """Set up a game state with characters already in play."""
    player1 = Player("Player 1")
    player2 = Player("Player 2")
    
    # Put characters in play
    player1.characters_in_play = player1_characters
    player2.characters_in_play = player2_characters
    
    # Give players some ink
    for i in range(5):
        player1.inkwell.append(create_character_with_ability(f"Ink {i}", None))
        player2.inkwell.append(create_character_with_ability(f"Ink {i}", None))
    
    game = GameState(players=[player1, player2])
    game.current_phase = Phase.MAIN  # Start in main phase where actions happen
    
    validator = MoveValidator(game)
    engine = GameEngine(game)
    
    return game, validator, engine


class TestSingerAbilityIntegration:
    """Test Singer ability integration with game state."""
    
    def test_singer_enables_song_singing(self):
        """Test that Singer ability enables singing songs as a legal move."""
        # Create a Singer 5 character and a song that costs 5 to sing
        singer_char = create_character_with_ability("Singer Character", "Singer", value=5)
        song = create_song_card("Test Song", cost=4, singer_cost=5)
        
        # Set up game
        game, validator, engine = setup_game_with_characters([singer_char], [])
        game.current_player.hand.append(song)
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Check that singing the song is a legal action
        sing_actions = [action for action, params in legal_actions 
                       if action == GameAction.SING_SONG]
        assert len(sing_actions) > 0, "Should be able to sing song with Singer"
        
        # Verify the specific song-singer combination
        sing_params = [params for action, params in legal_actions 
                      if action == GameAction.SING_SONG]
        assert any(p['song'] == song and p['singer'] == singer_char for p in sing_params)
    
    def test_singer_value_restriction(self):
        """Test that Singer value restricts which songs can be sung."""
        # Create a Singer 3 character and songs requiring different costs
        singer_3 = create_character_with_ability("Singer 3", "Singer", value=3)
        song_cost_3 = create_song_card("Easy Song", cost=2, singer_cost=3)
        song_cost_5 = create_song_card("Hard Song", cost=4, singer_cost=5)
        
        # Set up game
        game, validator, engine = setup_game_with_characters([singer_3], [])
        game.current_player.hand.extend([song_cost_3, song_cost_5])
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Get all sing actions
        sing_params = [params for action, params in legal_actions 
                      if action == GameAction.SING_SONG]
        
        # Singer 3 can only sing the song requiring cost 3
        songs_can_sing = [p['song'] for p in sing_params if p['singer'] == singer_3]
        assert song_cost_3 in songs_can_sing
        assert song_cost_5 not in songs_can_sing
    
    def test_exerted_singer_cannot_sing(self):
        """Test that exerted singers cannot sing songs."""
        singer = create_character_with_ability("Singer", "Singer", value=5)
        singer.exerted = True  # Exert the singer
        song = create_song_card("Test Song", cost=4, singer_cost=5)
        
        # Set up game
        game, validator, engine = setup_game_with_characters([singer], [])
        game.current_player.hand.append(song)
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Should not be able to sing with exerted character
        sing_actions = [action for action, params in legal_actions 
                       if action == GameAction.SING_SONG]
        assert len(sing_actions) == 0, "Exerted singer should not be able to sing"


class TestEvasiveAbilityIntegration:
    """Test Evasive ability integration with game state."""
    
    def test_evasive_prevents_normal_challenges(self):
        """Test that Evasive characters cannot be challenged by non-evasive characters."""
        # Create an evasive defender and a normal attacker
        evasive_defender = create_character_with_ability("Evasive Defender", "Evasive")
        normal_attacker = create_character_with_ability("Normal Attacker", None)
        
        # Set up game
        game, validator, engine = setup_game_with_characters([normal_attacker], [evasive_defender])
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Get all challenge actions
        challenge_params = [params for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        # Normal attacker should not be able to challenge evasive defender
        can_challenge_evasive = any(
            p['attacker'] == normal_attacker and p['defender'] == evasive_defender 
            for p in challenge_params
        )
        assert not can_challenge_evasive, "Normal character should not be able to challenge evasive"
    
    def test_evasive_can_challenge_evasive(self):
        """Test that Evasive characters can challenge other evasive characters."""
        # Create two evasive characters
        evasive_attacker = create_character_with_ability("Evasive Attacker", "Evasive")
        evasive_defender = create_character_with_ability("Evasive Defender", "Evasive")
        
        # Set up game
        game, validator, engine = setup_game_with_characters([evasive_attacker], [evasive_defender])
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Get all challenge actions
        challenge_params = [params for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        # Evasive attacker should be able to challenge evasive defender
        can_challenge_evasive = any(
            p['attacker'] == evasive_attacker and p['defender'] == evasive_defender 
            for p in challenge_params
        )
        assert can_challenge_evasive, "Evasive character should be able to challenge another evasive"
    
    def test_evasive_with_multiple_targets(self):
        """Test challenge options when opponent has both evasive and non-evasive characters."""
        normal_attacker = create_character_with_ability("Normal Attacker", None)
        evasive_attacker = create_character_with_ability("Evasive Attacker", "Evasive")
        
        normal_defender = create_character_with_ability("Normal Defender", None)
        evasive_defender = create_character_with_ability("Evasive Defender", "Evasive")
        
        # Set up game
        game, validator, engine = setup_game_with_characters(
            [normal_attacker, evasive_attacker], 
            [normal_defender, evasive_defender]
        )
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        challenge_params = [params for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER]
        
        # Check what each attacker can challenge
        normal_targets = [p['defender'] for p in challenge_params if p['attacker'] == normal_attacker]
        evasive_targets = [p['defender'] for p in challenge_params if p['attacker'] == evasive_attacker]
        
        # Normal attacker can only challenge normal defender
        assert normal_defender in normal_targets
        assert evasive_defender not in normal_targets
        
        # Evasive attacker can challenge both
        assert normal_defender in evasive_targets
        assert evasive_defender in evasive_targets


class TestBodyguardAbilityIntegration:
    """Test Bodyguard ability integration with game state."""
    
    def test_bodyguard_must_be_challenged_first(self):
        """Test that Bodyguard characters must be challenged before others."""
        # Create a bodyguard and a normal defender
        bodyguard = create_character_with_ability("Bodyguard", "Bodyguard")
        normal_defender = create_character_with_ability("Normal Defender", None)
        attacker = create_character_with_ability("Attacker", None)
        
        # Set up game
        game, validator, engine = setup_game_with_characters([attacker], [bodyguard, normal_defender])
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Get all challenge targets for the attacker
        challenge_params = [params for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER and params['attacker'] == attacker]
        
        targets = [p['defender'] for p in challenge_params]
        
        # Can only challenge the bodyguard
        assert bodyguard in targets
        assert normal_defender not in targets, "Cannot challenge normal character when bodyguard is present"
    
    def test_multiple_bodyguards_can_be_challenged(self):
        """Test that any bodyguard can be challenged when multiple exist."""
        bodyguard1 = create_character_with_ability("Bodyguard 1", "Bodyguard")
        bodyguard2 = create_character_with_ability("Bodyguard 2", "Bodyguard")
        normal_defender = create_character_with_ability("Normal Defender", None)
        attacker = create_character_with_ability("Attacker", None)
        
        # Set up game
        game, validator, engine = setup_game_with_characters(
            [attacker], 
            [bodyguard1, bodyguard2, normal_defender]
        )
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Get all challenge targets
        challenge_params = [params for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER and params['attacker'] == attacker]
        
        targets = [p['defender'] for p in challenge_params]
        
        # Can challenge either bodyguard but not the normal character
        assert bodyguard1 in targets
        assert bodyguard2 in targets
        assert normal_defender not in targets
    
    def test_no_bodyguard_allows_normal_challenges(self):
        """Test that without bodyguards, any character can be challenged."""
        defender1 = create_character_with_ability("Defender 1", None)
        defender2 = create_character_with_ability("Defender 2", None)
        attacker = create_character_with_ability("Attacker", None)
        
        # Set up game
        game, validator, engine = setup_game_with_characters([attacker], [defender1, defender2])
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Get all challenge targets
        challenge_params = [params for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER and params['attacker'] == attacker]
        
        targets = [p['defender'] for p in challenge_params]
        
        # Can challenge any defender
        assert defender1 in targets
        assert defender2 in targets
    
    def test_damaged_bodyguard_still_protects(self):
        """Test that damaged (but alive) bodyguards still enforce challenge rules."""
        bodyguard = create_character_with_ability("Bodyguard", "Bodyguard", willpower=5)
        bodyguard.damage = 3  # Damaged but not dead
        normal_defender = create_character_with_ability("Normal Defender", None)
        attacker = create_character_with_ability("Attacker", None)
        
        # Set up game
        game, validator, engine = setup_game_with_characters([attacker], [bodyguard, normal_defender])
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Get all challenge targets
        challenge_params = [params for action, params in legal_actions 
                           if action == GameAction.CHALLENGE_CHARACTER and params['attacker'] == attacker]
        
        targets = [p['defender'] for p in challenge_params]
        
        # Still must challenge the damaged bodyguard
        assert bodyguard in targets
        assert normal_defender not in targets


class TestAbilityInteractions:
    """Test interactions between different abilities."""
    
    def test_evasive_bodyguard_interaction(self):
        """Test interaction between Evasive and Bodyguard abilities."""
        # Create characters with combined abilities
        evasive_bodyguard = create_character_with_ability("Evasive Bodyguard", "Bodyguard")
        # Manually add Evasive ability too
        evasive_ability = EvasiveAbility(
            name="Evasive",
            type=AbilityType.KEYWORD,
            effect="Only characters with Evasive can challenge this character",
            full_text="Evasive",
            keyword="Evasive",
            value=None
        )
        evasive_bodyguard.abilities.append(evasive_ability)
        
        normal_defender = create_character_with_ability("Normal Defender", None)
        normal_attacker = create_character_with_ability("Normal Attacker", None)
        evasive_attacker = create_character_with_ability("Evasive Attacker", "Evasive")
        
        # Set up game
        game, validator, engine = setup_game_with_characters(
            [normal_attacker, evasive_attacker], 
            [evasive_bodyguard, normal_defender]
        )
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Get challenge options for each attacker
        normal_challenge_params = [
            params for action, params in legal_actions 
            if action == GameAction.CHALLENGE_CHARACTER and params['attacker'] == normal_attacker
        ]
        evasive_challenge_params = [
            params for action, params in legal_actions 
            if action == GameAction.CHALLENGE_CHARACTER and params['attacker'] == evasive_attacker
        ]
        
        # Normal attacker cannot challenge anyone (bodyguard is evasive)
        assert len(normal_challenge_params) == 0
        
        # Evasive attacker must challenge the evasive bodyguard
        evasive_targets = [p['defender'] for p in evasive_challenge_params]
        assert evasive_bodyguard in evasive_targets
        assert normal_defender not in evasive_targets
    
    def test_singer_quest_interaction(self):
        """Test that singers can quest and sing in the same turn."""
        singer = create_character_with_ability("Singer", "Singer", value=5)
        song = create_song_card("Test Song", cost=4, singer_cost=5)
        
        # Set up game
        game, validator, engine = setup_game_with_characters([singer], [])
        game.current_player.hand.append(song)
        
        # Get initial legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Should be able to both quest and sing
        can_quest = any(
            action == GameAction.QUEST_CHARACTER and params['character'] == singer 
            for action, params in legal_actions
        )
        can_sing = any(
            action == GameAction.SING_SONG and params['singer'] == singer 
            for action, params in legal_actions
        )
        
        assert can_quest, "Singer should be able to quest"
        assert can_sing, "Singer should be able to sing"
        
        # After singing, singer should be exerted
        sing_action = next(
            (action, params) for action, params in legal_actions 
            if action == GameAction.SING_SONG and params['singer'] == singer
        )
        success, message = engine.execute_action(sing_action[0], sing_action[1])
        assert success
        assert singer.exerted, "Singer should be exerted after singing"
        
        # Now check legal actions again
        legal_actions_after = validator.get_all_legal_actions()
        
        # Should not be able to quest or sing anymore
        can_quest_after = any(
            action == GameAction.QUEST_CHARACTER and params['character'] == singer 
            for action, params in legal_actions_after
        )
        can_sing_after = any(
            action == GameAction.SING_SONG and params['singer'] == singer 
            for action, params in legal_actions_after
        )
        
        assert not can_quest_after, "Exerted singer should not be able to quest"
        assert not can_sing_after, "Exerted singer should not be able to sing"


class TestAbilityEdgeCases:
    """Test edge cases and special scenarios with abilities."""
    
    def test_empty_board_state(self):
        """Test abilities when no characters are in play."""
        game, validator, engine = setup_game_with_characters([], [])
        
        # Add a song to hand
        song = create_song_card("Test Song", cost=4, singer_cost=3)
        game.current_player.hand.append(song)
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Should not be able to sing without a singer
        sing_actions = [action for action, params in legal_actions 
                       if action == GameAction.SING_SONG]
        assert len(sing_actions) == 0
    
    def test_all_characters_exerted(self):
        """Test that exerted characters limit available actions."""
        char1 = create_character_with_ability("Character 1", None)
        char2 = create_character_with_ability("Character 2", None)
        char1.exerted = True
        char2.exerted = True
        
        game, validator, engine = setup_game_with_characters([char1, char2], [])
        
        # Get legal actions
        legal_actions = validator.get_all_legal_actions()
        
        # Should not be able to quest or challenge with exerted characters
        quest_actions = [action for action, params in legal_actions 
                        if action == GameAction.QUEST_CHARACTER]
        challenge_actions = [action for action, params in legal_actions 
                            if action == GameAction.CHALLENGE_CHARACTER]
        
        assert len(quest_actions) == 0
        assert len(challenge_actions) == 0
    
    def test_dead_characters_removed(self):
        """Test that dead characters are properly removed and don't affect game state."""
        bodyguard = create_character_with_ability("Bodyguard", "Bodyguard", willpower=3)
        normal_defender = create_character_with_ability("Normal Defender", None)
        attacker = create_character_with_ability("Attacker", None, strength=3)
        
        # Set up game
        game, validator, engine = setup_game_with_characters([attacker], [bodyguard, normal_defender])
        
        # Execute challenge to kill the bodyguard
        legal_actions = validator.get_all_legal_actions()
        challenge_action = next(
            (action, params) for action, params in legal_actions 
            if action == GameAction.CHALLENGE_CHARACTER and 
            params['attacker'] == attacker and params['defender'] == bodyguard
        )
        
        success, message = engine.execute_action(challenge_action[0], challenge_action[1])
        assert success
        
        # Bodyguard should be dead and removed
        assert bodyguard not in game.players[1].characters_in_play
        assert bodyguard in game.players[1].discard_pile
        
        # Now get new legal actions
        legal_actions_after = validator.get_all_legal_actions()
        
        # Should now be able to challenge the normal defender (bodyguard is gone)
        # But attacker is exerted from the previous challenge
        challenge_actions_after = [
            params for action, params in legal_actions_after 
            if action == GameAction.CHALLENGE_CHARACTER
        ]
        assert len(challenge_actions_after) == 0  # Attacker is exerted
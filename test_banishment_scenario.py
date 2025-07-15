#!/usr/bin/env python3
"""
Test script to verify that CHARACTER_BANISHED events trigger correctly during challenges.
"""

from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.fly_my_pet import create_fly_my_pet

def test_banishment_scenario():
    """Test that abilities trigger when characters are banished in challenges."""
    
    # Create players with proper hand initialization
    player1 = Player("Ashley", "Amethyst-Steel")
    player2 = Player("Tace", "Ruby-Emerald")
    player1.hand = []
    player2.hand = []
    player1.deck = []
    player2.deck = []
    
    # Add cards to Tace's deck
    for i in range(5):
        from src.lorcana_sim.models.cards.action_card import ActionCard
        dummy_card = ActionCard(
            id=i+100,
            name="Test Card",
            version=None,
            full_name="Test Card",
            cost=1,
            color=CardColor.RUBY,
            inkwell=True,
            rarity=Rarity.COMMON,
            set_code="TEST",
            number=i+100,
            story=""
        )
        player2.deck.append(dummy_card)
    
    # Create game state and engine
    game_state = GameState([player1, player2])
    game_engine = GameEngine(game_state)
    
    # Create Diablo with FLY, MY PET! ability
    diablo = CharacterCard(
        id=1,
        name="Diablo",
        version="Fly, My Pet!",
        full_name="Diablo - Fly, My Pet!",
        cost=1,
        color=CardColor.RUBY,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TFC",
        number=1,
        story="",
        strength=0,
        willpower=1,
        lore=1,
        subtypes=["Storyborn", "Bird"],
        controller=player2
    )
    
    # Create HeiHei as attacker
    heihei = CharacterCard(
        id=2,
        name="HeiHei",
        version=None,
        full_name="HeiHei",
        cost=1,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TFC",
        number=2,
        story="",
        strength=2,
        willpower=2,
        lore=1,
        subtypes=["Storyborn", "Rooster"],
        controller=player1
    )
    
    # Add FLY, MY PET! ability to Diablo
    fly_my_pet_ability = create_fly_my_pet(diablo, {})
    diablo.composable_abilities.append(fly_my_pet_ability)
    
    # Put characters in play
    player1.characters_in_play.append(heihei)
    player2.characters_in_play.append(diablo)
    
    # Make sure characters are ready and can challenge
    heihei.exerted = False
    heihei.is_dry = True
    diablo.exerted = False 
    diablo.is_dry = True
    
    # Set current player
    game_state.current_player_index = 0  # player1 is at index 0
    
    # Register abilities
    diablo.register_composable_abilities(game_engine.event_manager)
    
    print(f"Before challenge:")
    print(f"  Tace hand size: {len(player2.hand)}")
    print(f"  Tace deck size: {len(player2.deck)}")
    print(f"  Diablo in play: {diablo in player2.characters_in_play}")
    
    # Execute challenge directly using internal method
    result = game_engine._execute_challenge(heihei, diablo)
    
    print(f"After challenge:")
    print(f"  Challenge result: {result.success}")
    if hasattr(result, 'message'):
        print(f"  Challenge message: {result.message}")
    if hasattr(result, 'error_message'):
        print(f"  Challenge error: {result.error_message}")
    print(f"  Tace hand size: {len(player2.hand)}")
    print(f"  Tace deck size: {len(player2.deck)}")
    print(f"  Diablo in play: {diablo in player2.characters_in_play}")
    print(f"  Diablo in discard: {diablo in player2.discard_pile}")
    
    # Check if card was drawn (indication that FLY, MY PET! triggered)
    if len(player2.hand) > 0 and len(player2.deck) < 5:
        print("✅ SUCCESS: FLY, MY PET! triggered and drew a card!")
        return True
    else:
        print("❌ FAILURE: FLY, MY PET! did not trigger")
        return False

if __name__ == "__main__":
    test_banishment_scenario()
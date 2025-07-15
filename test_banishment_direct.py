#!/usr/bin/env python3
"""
Direct test of banishment event triggering after fixing CONTROLLER selector.
"""

from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.engine.event_system import GameEventManager, EventContext, GameEvent
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.fly_my_pet import create_fly_my_pet
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity

def test_banishment_direct():
    """Test FLY, MY PET! by directly triggering banishment event."""
    
    # Create players with proper setup
    player1 = Player("Ashley", "Amethyst-Steel")
    player2 = Player("Tace", "Ruby-Emerald")
    
    # Initialize as empty lists
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
    
    # Create game state
    game_state = GameState([player1, player2])
    event_manager = GameEventManager(game_state)
    
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
    
    # Add FLY, MY PET! ability
    fly_my_pet_ability = create_fly_my_pet(diablo, {})
    diablo.composable_abilities.append(fly_my_pet_ability)
    
    # Put Diablo in play and register abilities
    player2.characters_in_play.append(diablo)
    diablo.register_composable_abilities(event_manager)
    
    print(f"Before banishment:")
    print(f"  Tace hand size: {len(player2.hand)}")
    print(f"  Tace deck size: {len(player2.deck)}")
    
    # Directly trigger CHARACTER_BANISHED event
    banish_context = EventContext(
        event_type=GameEvent.CHARACTER_BANISHED,
        source=diablo,
        player=player2,
        game_state=game_state,
        banishment_cause="challenge"
    )
    
    results = event_manager.trigger_event(banish_context)
    print(f"Event results: {results}")
    
    print(f"After banishment:")
    print(f"  Tace hand size: {len(player2.hand)}")
    print(f"  Tace deck size: {len(player2.deck)}")
    
    # Check if card was drawn
    if len(player2.hand) > 0 and len(player2.deck) == 4:
        print("✅ SUCCESS: FLY, MY PET! triggered and drew a card!")
        return True
    else:
        print("❌ FAILURE: FLY, MY PET! did not draw a card")
        return False

if __name__ == "__main__":
    test_banishment_direct()
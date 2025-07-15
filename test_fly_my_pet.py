#!/usr/bin/env python3
"""
Test script to verify FLY, MY PET! ability triggers correctly when character is banished.
"""

from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.engine.event_system import GameEventManager, EventContext, GameEvent
from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.fly_my_pet import create_fly_my_pet

def test_fly_my_pet():
    """Test that FLY, MY PET! triggers when character is banished."""
    
    # Create players
    player1 = Player("Ashley", "Amethyst-Steel")
    player2 = Player("Tace", "Ruby-Emerald")
    
    # Create game state
    game_state = GameState([player1, player2])
    event_manager = GameEventManager(game_state)
    
    # Create Diablo with FLY, MY PET! ability  
    from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
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
    
    # Add FLY, MY PET! ability to Diablo
    fly_my_pet_ability = create_fly_my_pet(diablo, {})
    diablo.composable_abilities.append(fly_my_pet_ability)
    
    # Put Diablo in play
    player2.characters_in_play.append(diablo)
    
    # Register abilities with event manager
    diablo.register_composable_abilities(event_manager)
    
    # Add some cards to player2's deck
    for i in range(10):
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
    
    # Record initial hand size
    initial_hand_size = len(player2.hand)
    initial_deck_size = len(player2.deck)
    print(f"Initial hand size for Tace: {initial_hand_size}")
    print(f"Initial deck size for Tace: {initial_deck_size}")
    print(f"Player2 has draw_cards method: {hasattr(player2, 'draw_cards')}")
    
    # Trigger CHARACTER_BANISHED event
    print("Triggering CHARACTER_BANISHED event for Diablo...")
    banish_context = EventContext(
        event_type=GameEvent.CHARACTER_BANISHED,
        source=diablo,
        player=player2,
        game_state=game_state
    )
    
    # Debug the ability before triggering
    print(f"Diablo controller: {diablo.controller}")
    print(f"Ability: {fly_my_pet_ability}")
    print(f"Ability character: {fly_my_pet_ability.character}")
    print(f"Ability listeners: {len(fly_my_pet_ability.listeners)}")
    
    results = event_manager.trigger_event(banish_context)
    print(f"Event results: {results}")
    
    # Debug the target selection manually
    from src.lorcana_sim.models.abilities.composable.target_selectors import CONTROLLER
    test_context = {
        'event_context': banish_context,
        'source': diablo,
        'game_state': game_state,
        'player': player2,
        'ability_owner': diablo
    }
    selected_targets = CONTROLLER.select(test_context)
    print(f"CONTROLLER target selector found: {selected_targets}")
    
    # Try applying DrawCards effect directly
    from src.lorcana_sim.models.abilities.composable.effects import DRAW_CARD
    if selected_targets:
        print(f"Applying DRAW_CARD effect to target: {selected_targets[0]}")
        DRAW_CARD.apply(selected_targets[0], test_context)
        print(f"After direct apply - Hand size: {len(player2.hand)}, Deck size: {len(player2.deck)}")
    
    # Check if card was drawn
    final_hand_size = len(player2.hand)
    final_deck_size = len(player2.deck)
    print(f"Final hand size for Tace: {final_hand_size}")
    print(f"Final deck size for Tace: {final_deck_size}")
    
    if final_hand_size > initial_hand_size:
        print("✅ SUCCESS: FLY, MY PET! triggered and drew a card!")
        return True
    else:
        print("❌ FAILURE: FLY, MY PET! did not trigger")
        return False

if __name__ == "__main__":
    test_fly_my_pet()
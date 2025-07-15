#!/usr/bin/env python3
"""Demonstrate the new choice system with specific scenarios."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.lorcana_sim.models.cards.character_card import CharacterCard
from src.lorcana_sim.models.cards.base_card import CardColor, Rarity
from src.lorcana_sim.models.game.player import Player
from src.lorcana_sim.models.game.game_state import GameState
from src.lorcana_sim.engine.game_engine import GameEngine
from src.lorcana_sim.engine.event_system import EventContext, GameEvent


def create_test_game():
    """Create a test game with specific characters to trigger choices."""
    # Create players
    player1 = Player("Ashley", "Amethyst-Steel")
    player2 = Player("Tace", "Ruby-Emerald")
    
    # Initialize empty decks/hands
    player1.hand = []
    player2.hand = []
    player1.deck = [None] * 10  # Mock cards
    player2.deck = [None] * 10
    
    # Create game state
    game_state = GameState([player1, player2])
    engine = GameEngine(game_state)
    
    # Give players some ink
    for _ in range(5):
        player1.inkwell.append(None)
        player2.inkwell.append(None)
    
    return game_state, engine, player1, player2


def test_fly_my_pet_choice():
    """Test FLY, MY PET! choice when character is banished."""
    print("=== Testing FLY, MY PET! Choice ===")
    
    game_state, engine, player1, player2 = create_test_game()
    
    # Create Diablo with FLY, MY PET!
    diablo = CharacterCard(
        id=1,
        name="Diablo",
        version="Devoted Herald",
        full_name="Diablo - Devoted Herald",
        cost=1,
        color=CardColor.RUBY,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=1,
        story="",
        strength=1,
        willpower=1,
        lore=1,
        subtypes=["Storyborn", "Ally"],
        controller=player1
    )
    
    # Add FLY, MY PET! ability
    from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.fly_my_pet import create_fly_my_pet
    ability = create_fly_my_pet(diablo, {})
    diablo.composable_abilities.append(ability)
    
    # Put Diablo in play
    player1.characters_in_play.append(diablo)
    
    # Register abilities
    diablo.register_composable_abilities(engine.event_manager)
    
    # Trigger banishment
    print(f"Banishing {diablo.name}...")
    banish_context = EventContext(
        event_type=GameEvent.CHARACTER_BANISHED,
        source=diablo,
        player=player1,
        game_state=game_state
    )
    
    engine.trigger_event_with_choices(banish_context)
    
    # Check if game is paused for choice
    if engine.is_paused_for_choice():
        choice = engine.get_current_choice()
        print(f"✅ Game paused for choice!")
        print(f"   Player: {choice.player.name}")
        print(f"   Ability: {choice.ability_name}")
        print(f"   Prompt: {choice.prompt}")
        print(f"   Options: {[f'{opt.id}: {opt.description}' for opt in choice.options]}")
        
        # Make the choice (yes)
        print(f"   Choosing: yes")
        success = engine.provide_player_choice(choice.choice_id, "yes")
        if success:
            print(f"✅ Choice provided successfully!")
            print(f"   Hand size after: {len(player1.hand)}")
        else:
            print(f"❌ Failed to provide choice")
    else:
        print(f"⚠️  No choice triggered")
    
    print()


def test_play_rough_choice():
    """Test PLAY ROUGH choice when character quests."""
    print("=== Testing PLAY ROUGH Choice ===")
    
    game_state, engine, player1, player2 = create_test_game()
    
    # Create Madam Mim with PLAY ROUGH
    mim = CharacterCard(
        id=2,
        name="Madam Mim",
        version="Rivalry Wrangler",
        full_name="Madam Mim - Rivalry Wrangler",
        cost=3,
        color=CardColor.AMETHYST,
        inkwell=True,
        rarity=Rarity.UNCOMMON,
        set_code="TEST",
        number=2,
        story="",
        strength=3,
        willpower=3,
        lore=2,
        subtypes=["Storyborn", "Sorcerer", "Villain"],
        controller=player1
    )
    
    # Add PLAY ROUGH ability
    from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.play_rough import create_play_rough
    ability = create_play_rough(mim, {})
    mim.composable_abilities.append(ability)
    
    # Put Mim in play
    player1.characters_in_play.append(mim)
    mim.is_dry = True  # Can act
    
    # Create some opposing characters
    enemy1 = CharacterCard(
        id=3,
        name="Donald Duck",
        version="Test",
        full_name="Donald Duck - Test",
        cost=2,
        color=CardColor.RUBY,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=3,
        story="",
        strength=2,
        willpower=3,
        lore=1,
        subtypes=["Storyborn", "Hero"],
        controller=player2
    )
    
    enemy2 = CharacterCard(
        id=4,
        name="Mickey Mouse",
        version="Test",
        full_name="Mickey Mouse - Test",
        cost=3,
        color=CardColor.RUBY,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=4,
        story="",
        strength=3,
        willpower=4,
        lore=2,
        subtypes=["Hero", "Captain"],
        controller=player2
    )
    
    player2.characters_in_play.extend([enemy1, enemy2])
    
    # Register abilities
    mim.register_composable_abilities(engine.event_manager)
    
    # Trigger quest event
    print(f"{mim.name} quests...")
    quest_context = EventContext(
        event_type=GameEvent.CHARACTER_QUESTS,
        source=mim,
        player=player1,
        game_state=game_state
    )
    
    engine.trigger_event_with_choices(quest_context)
    
    # Check if game is paused for choice
    if engine.is_paused_for_choice():
        choice = engine.get_current_choice()
        print(f"✅ Game paused for choice!")
        print(f"   Player: {choice.player.name}")
        print(f"   Ability: {choice.ability_name}")
        print(f"   Prompt: {choice.prompt}")
        print(f"   Options:")
        for opt in choice.options:
            print(f"     • {opt.id}: {opt.description}")
        
        # Choose the first character
        valid_options = [opt for opt in choice.options if opt.id != "none"]
        if valid_options:
            chosen = valid_options[0]
            print(f"   Choosing: {chosen.description}")
            success = engine.provide_player_choice(choice.choice_id, chosen.id)
            if success:
                print(f"✅ Choice provided successfully!")
                # Check if character was exerted
                for char in player2.characters_in_play:
                    if char.exerted:
                        print(f"   {char.name} is now exerted!")
            else:
                print(f"❌ Failed to provide choice")
    else:
        print(f"⚠️  No choice triggered")
    
    print()


def test_mysterious_advantage_choice():
    """Test MYSTERIOUS ADVANTAGE choice when character enters play."""
    print("=== Testing MYSTERIOUS ADVANTAGE Choice ===")
    
    game_state, engine, player1, player2 = create_test_game()
    
    # Create Giant Cobra with MYSTERIOUS ADVANTAGE
    cobra = CharacterCard(
        id=5,
        name="Giant Cobra",
        version="Scheming Henchman",
        full_name="Giant Cobra - Scheming Henchman",
        cost=4,
        color=CardColor.AMETHYST,
        inkwell=False,
        rarity=Rarity.UNCOMMON,
        set_code="TEST",
        number=5,
        story="",
        strength=4,
        willpower=3,
        lore=2,
        subtypes=["Storyborn", "Villain"],
        controller=player1
    )
    
    # Add MYSTERIOUS ADVANTAGE ability
    from src.lorcana_sim.models.abilities.composable.named_abilities.triggered.mysterious_advantage import create_mysterious_advantage
    ability = create_mysterious_advantage(cobra, {})
    cobra.composable_abilities.append(ability)
    
    # Add some cards to hand
    card1 = CharacterCard(
        id=6,
        name="Test Card 1",
        version="",
        full_name="Test Card 1",
        cost=1,
        color=CardColor.AMETHYST,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=6,
        story="",
        strength=1,
        willpower=1,
        lore=1,
        subtypes=[],
        controller=player1
    )
    
    card2 = CharacterCard(
        id=7,
        name="Test Card 2",
        version="",
        full_name="Test Card 2",
        cost=2,
        color=CardColor.STEEL,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=7,
        story="",
        strength=2,
        willpower=2,
        lore=1,
        subtypes=[],
        controller=player1
    )
    
    player1.hand.extend([card1, card2])
    print(f"Hand before: {[c.name for c in player1.hand]}")
    print(f"Lore before: {player1.lore}")
    
    # Put cobra in play
    player1.characters_in_play.append(cobra)
    
    # Register abilities
    cobra.register_composable_abilities(engine.event_manager)
    
    # Trigger enters play event
    print(f"Playing {cobra.name}...")
    enter_context = EventContext(
        event_type=GameEvent.CHARACTER_ENTERS_PLAY,
        source=cobra,
        player=player1,
        game_state=game_state
    )
    
    engine.trigger_event_with_choices(enter_context)
    
    # Check if game is paused for choice
    if engine.is_paused_for_choice():
        choice = engine.get_current_choice()
        print(f"✅ Game paused for choice!")
        print(f"   Player: {choice.player.name}")
        print(f"   Ability: {choice.ability_name}")
        print(f"   Prompt: {choice.prompt}")
        print(f"   Options:")
        for opt in choice.options:
            print(f"     • {opt.id}: {opt.description}")
        
        # Choose a card to discard
        card_options = [opt for opt in choice.options if opt.id.startswith("card_")]
        if card_options:
            chosen = card_options[0]
            print(f"   Choosing: {chosen.description}")
            success = engine.provide_player_choice(choice.choice_id, chosen.id)
            if success:
                print(f"✅ Choice provided successfully!")
                print(f"   Hand after: {[c.name for c in player1.hand]}")
                print(f"   Lore after: {player1.lore}")
            else:
                print(f"❌ Failed to provide choice")
    else:
        print(f"⚠️  No choice triggered")
    
    print()


def main():
    """Run all choice system demonstrations."""
    print("🎮 Demonstrating New Player Choice System")
    print("=" * 50)
    
    test_fly_my_pet_choice()
    test_play_rough_choice()
    test_mysterious_advantage_choice()
    
    print("✅ All choice demonstrations complete!")


if __name__ == "__main__":
    main()
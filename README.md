# Lorcana Simulation

A comprehensive Python-based simulation of the Lorcana Trading Card Game.

## Features

### Phase 1: Core Data Models ✅
- **Card Models**: Character, Action, Item, Location cards with full property support
- **Ability System**: Keyword, Triggered, Static, and Activated abilities
- **Deck Building**: Legal deck validation, shuffling, and analysis
- **Player State**: Hand, deck, inkwell, and character management
- **Game State**: Turn structure, phase management, and legal action validation
- **JSON Parsing**: Full lorcana-json format support with robust error handling

### Advanced Deck Building ✅
- **Smart Deck Builder**: Generates legal decks with various strategies
- **Archetype Support**: Aggro, Control, and Balanced deck construction
- **Tribal Decks**: Character subtype-focused builds
- **Color Filtering**: Mono-color and multi-color deck generation
- **Curve Optimization**: Intelligent cost distribution
- **Real Data Integration**: Works with 1900+ real Lorcana cards

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e .[dev]
```

## Quick Start

### Basic Card Loading
```python
from lorcana_sim.models.cards import CardFactory
from lorcana_sim.loaders import LorcanaJsonParser

# Load card database
parser = LorcanaJsonParser("data/all-cards/allCards.json")

# Create card objects
cards = [CardFactory.from_json(card_data) for card_data in parser.cards[:10]]

# Examine a character card
mickey = cards[0]  # Assuming first card is Mickey Mouse
print(f"{mickey.full_name} - {mickey.strength}/{mickey.willpower} for {mickey.cost} ink")
```

### Smart Deck Building
```python
from lorcana_sim.utils import DeckBuilder
from lorcana_sim.models.cards.base_card import CardColor

# Initialize deck builder
builder = DeckBuilder(parser.cards)

# Build different deck types
aggro_deck = builder.build_aggro_deck(CardColor.RUBY, "Ruby Rush")
control_deck = builder.build_control_deck(CardColor.SAPPHIRE, "Sapphire Control") 
tribal_deck = builder.build_character_tribal_deck("Princess", "Princess Power")

# Analyze decks
print(f"Aggro deck: {aggro_deck.get_cost_curve()}")
print(f"Control deck: {control_deck.get_color_distribution()}")
```

### Game Simulation
```python
from lorcana_sim.models.game import Deck, Player, GameState

# Create players with decks
player1 = Player("Alice")
player2 = Player("Bob")

player1.deck = aggro_deck.shuffle()
player2.deck = control_deck.shuffle()

# Draw opening hands
player1.draw_cards(7)
player2.draw_cards(7)

# Initialize game
game = GameState(players=[player1, player2])

# Show game state
print(f"Turn {game.turn_number} - {game.active_player.name}'s {game.current_phase.value} phase")
print(f"Legal actions: {len(game.get_legal_actions())}")
```

## Examples

Run the demo scripts to see the system in action:

```bash
# Basic Phase 1 functionality
python examples/demo_phase1.py

# Advanced deck building showcase
python examples/demo_deck_builder.py

# Simple deck builder with complete analysis
python examples/simple_deck_builder.py

# Interactive deck builder (create custom decks with analysis)
python examples/build_random_deck.py

# Deck analysis demo (non-interactive)
python examples/demo_interactive_builder.py
```

## Testing

Run the comprehensive test suite:

```bash
# All tests
pytest

# Specific test categories
pytest tests/test_integration.py  # Real data integration
pytest tests/test_deck_builder.py # Deck building features
pytest tests/test_card_factory.py # JSON parsing
```

## Architecture

- **`models/`**: Core game object definitions (cards, decks, players, game state)
- **`loaders/`**: Data parsing from lorcana-json and Dreamborn formats
- **`utils/`**: Advanced utilities like the intelligent deck builder
- **`tests/`**: Comprehensive test suite with real data validation

## Database

The system works with the [lorcana-json](https://github.com/hexastorm/lorcana-json) database format. Place `allCards.json` in `data/all-cards/` to enable full functionality.

## Development Status

- ✅ **Phase 1**: Core Data Models and Deck Building
- 🔄 **Phase 2**: Advanced Ability System (Planned)
- 🔄 **Phase 3**: Complete Game Rules Engine (Planned)  
- 🔄 **Phase 4**: AI Players and Simulation (Planned)

See `plan/` directory for detailed implementation roadmap.
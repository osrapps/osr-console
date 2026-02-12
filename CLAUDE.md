# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

OSR Console is an SDK for a turn-based dungeon crawler RPG in the Old-School Renaissance (OSR) style. Game rules and mechanics are inspired by TSR's 1981 D&D Basic/Expert sets (B/X). The project uses a **uv workspace** monorepo with these packages:

- **`osrlib`** - Core game engine library (dice, combat, characters, dungeons, encounters, treasure, monsters)
- **`osrgame`** - Textual TUI frontend that demonstrates osrlib
- **`osrcli`** - CLI interface using questionary
- **`tests`** - pytest test suite for osrlib
- **`utils`** - Standalone utilities (e.g., OpenAI file helper)

## Build and development commands

```bash
# Install all workspace dependencies
uv sync

# Run all tests (from repo root)
uv run pytest tests/

# Run a single test file
uv run pytest tests/test_unit_treasure.py

# Run a single test by name
uv run pytest tests/test_unit_treasure.py -k "test_name"

# Run tests with verbose logging
uv run pytest tests/ --log-cli-level=DEBUG

# Run tests including opt-in tests (e.g., those requiring OpenAI API key)
uv run pytest tests/ --run-optin-tests

# Skip flaky tests
uv run pytest tests/ -m "not flaky"

# Lint
uv run ruff check

# Format
uv run ruff format

# Serve docs locally
uv run mkdocs serve
```

## Test conventions

- Test files live in `tests/` and follow the naming pattern `test_unit_*.py` or `test_integration_*.py`.
- Custom pytest markers: `flaky`, `integration`, `optin` (defined in `tests/pytest.ini`).
- Tests marked `optin` are skipped by default; pass `--run-optin-tests` to include them.
- `conftest.py` in `tests/` handles the opt-in marker filtering.

## Architecture

### Core game engine (`osrlib/osrlib/`)

The game models a hierarchical structure: **Adventure > Dungeon > Location > Encounter**.

- **`adventure.py`** - Top-level game container. An `Adventure` holds `Dungeon` and `Quest` collections and manages the active `Party`. Handles save/load via JSON serialization to a data directory.
- **`dungeon.py`** - Contains `Dungeon`, `Location`, and `Exit` classes. Locations are connected bidirectionally via exits with cardinal/vertical `Direction` values. Can optionally use OpenAI to generate location descriptions.
- **`encounter.py`** - Manages combat encounters at locations. Handles initiative, turn order (via `deque`), attack rounds, and treasure/XP awards. A `MonsterParty` is the opponent group.
- **`party.py`** - Collection of `PlayerCharacter` instances. Provides `get_default_party()` factory for quick setup with pre-named characters.
- **`player_character.py`** - PC with abilities, class, level, inventory, HP, saving throws, and XP tracking.
- **`character_classes.py`** - Defines class progressions (XP thresholds, HP dice, THAC0, saving throws) for all B/X classes.
- **`monster.py`** / **`monster_manual.py`** - Monster stat blocks and the monster catalog used to populate encounters.
- **`treasure.py`** - Treasure generation using B/X treasure type tables (types A-V). Generates coins, gems, jewelry, and magic items.
- **`item.py`** / **`item_factories.py`** - Item definitions and factory functions for equipping characters with weapons/armor.
- **`inventory.py`** - Character inventory management with equip/unequip logic affecting AC and attack modifiers.
- **`dice_roller.py`** - Dice notation parser and roller (e.g., "3d6", "1d8+2").
- **`enums.py`** - Shared enumerations: `CharacterClassType`, `ItemType`, `TreasureType`, `CoinType`, `Direction`, `AbilityType`, etc.
- **`dungeon_assistant.py`** - OpenAI integration for AI-generated dungeon descriptions (optional, requires API key).
- **`saving_throws.py`** / **`ability.py`** - Saving throw tables and ability score modifier calculations.

### TUI (`osrgame/osrgame/`)

Built on [Textual](https://textual.textualize.io/). Screen-based architecture:

- `osrgame.py` - Main app entry point
- `screen_welcome.py`, `screen_adventure_browser.py`, `screen_explore.py`, `screen_character.py` - Game screens
- `screen_modal_new_char.py` - Modal for character creation
- `widgets.py` - Custom Textual widgets
- `screen.tcss` - Textual CSS styling

### Data persistence

Game state is serialized to JSON via TinyDB. Save/load paths are managed by `osrlib.utils.get_data_dir_path()`.

# osrlib: Python library for OSR-style turn-based RPGs

The `osrlib` package is the main rules and game engine library for OSR Console.

If you want to play the game, learn how to install and start the app in [osrgame: Textual TUI for an OSR-style turn-based RPG](../osrgame/README.md).

If you want contribute code to the `osrlib` package itself, read on to learn how to build and test the library.

## Prerequisites

- Python 3.11+
- Poetry 1.6+

## Installation

Use Poetry to create a Python virtual environment and install `osrlib` and its dependencies:

```sh
# Create osrlib project venv and install its deps with Poetry
poetry install
```

## Build the package

You can also build the `osrlib` package by using Poetry:

```sh
# Build the 'osrlib' Python package
poetry build
```

## Test the library

Install the unit and integration test dependencies with Poetry:

```sh
# Move into the tests directory (assumes you're in <repo-root>/osrlib)
cd ../tests

# Create tests venv and install test deps with Poetry
poetry install
```

### Run all the tests

To run all unit and integration tests, run `pytest` with `poetry run`, passing only the test directory path as the only argument:

```sh
# Run ALL unit and integration tests in <repo-root>/tests/*.py
poetry run pytest ../tests
```

You should see a bunch of test output ending in a summary of the test results. Here's an abridge example of test output:

```console
$ poetry run pytest ../tests
========================================================================= test session starts ==========================================================================
platform darwin -- Python 3.11.6, pytest-7.4.2, pluggy-1.3.0
rootdir: /Users/username/repos/osr-console/tests
configfile: pytest.ini
collecting ...
------------------------------------------------------------------------- live log collection --------------------------------------------------------------------------
2023-10-15 19:10:19 [INFO] Initializing the GameManager...
2023-10-15 19:10:19 [INFO] GameManager initialized. There are 0 adventures available.
2023-10-15 19:10:19 [INFO] Testing dice_roller.py
collected 196 items

../tests/test_integration_saveload.py::test_abilities_saveload
---------------------------------------------------------------------------- live log setup ----------------------------------------------------------------------------
2023-10-15 19:10:19 [INFO] Creating TinyDB @ /Users/username/repos/osr-console/osrlib/test_db.json
2023-10-15 19:10:19 [INFO] Created TinyDB: <TinyDB tables=[], tables_count=0, default_table_documents_count=0, all_tables_documents_count=[]>
PASSED                                                                                                                                                           [  0%]
-------------------------------------------------------------------------- live log teardown ---------------------------------------------------------------------------
2023-10-15 19:10:19 [INFO] Dropping tables from TinyDB: <TinyDB tables=['abilities'], tables_count=1, default_table_documents_count=0, all_tables_documents_count=['abilities=6']>
2023-10-15 19:10:19 [INFO] Closing TinyDB: <TinyDB tables=[], tables_count=0, default_table_documents_count=0, all_tables_documents_count=[]>

../tests/test_integration_saveload.py::test_item_saveload

## MANY MORE LINES OF TEST OUTPUT OMITTED ##

../tests/test_unit_party.py::test_clear_party
---------------------------------------------------------------------------- live log call -----------------------------------------------------------------------------
2023-10-15 19:10:19 [INFO] Adding 'Sckricko' to party 'The B-Team'...
2023-10-15 19:10:19 [INFO] Setting 'Sckricko' as the active character in party 'The B-Team'...
2023-10-15 19:10:19 [INFO] Set 'Sckricko' as the active character in the party.
2023-10-15 19:10:19 [INFO] Adding 'Mazpar' to party 'The B-Team'...
2023-10-15 19:10:19 [INFO] Setting 'Mazpar' as the active character in party 'The B-Team'...
2023-10-15 19:10:19 [INFO] Set 'Mazpar' as the active character in the party.
2023-10-15 19:10:19 [INFO] Adding 'Slick' to party 'The B-Team'...
2023-10-15 19:10:19 [INFO] Setting 'Slick' as the active character in party 'The B-Team'...
2023-10-15 19:10:19 [INFO] Set 'Slick' as the active character in the party.
PASSED                                                                                                                                                           [ 99%]
../tests/test_unit_utils.py::test_format_modifiers
---------------------------------------------------------------------------- live log call -----------------------------------------------------------------------------
2023-10-15 19:10:19 [INFO] Testing empty modifiers: ''
2023-10-15 19:10:19 [INFO] Testing single modifier with positive value: 'To hit: +1'
2023-10-15 19:10:19 [INFO] Testing single modifier with negative value: 'Damage: -1'
2023-10-15 19:10:19 [INFO] Testing single modifier with no (zero) value: 'Open doors: 0'
2023-10-15 19:10:19 [INFO] Testing multiple modifiers with positive and negative values: 'To hit: +1, Damage: -1, Open doors: 0'
PASSED                                                                                                                                                           [100%]

========================================================================= 196 passed in 0.13s ==========================================================================
```

### Run specific tests

You can pass any argument you normally would to `pytest` when you run it with Poetry. For example, to run only the `test_remove_character_not_in_party` test, pass the `-k` filtering option followed by the test name:

```console
$ poetry run pytest ../tests -k "test_remove_character"
======================================================= test session starts ========================================================
platform darwin -- Python 3.11.6, pytest-7.4.2, pluggy-1.3.0
rootdir: /Users/username/repos/osr-console/tests
configfile: pytest.ini
collecting ...
------------------------------------------------------- live log collection --------------------------------------------------------
2023-10-15 19:17:14 [INFO] Initializing the GameManager...
2023-10-15 19:17:14 [INFO] GameManager initialized. There are 0 adventures available.
2023-10-15 19:17:14 [INFO] Testing dice_roller.py
collected 196 items / 194 deselected / 2 selected

../tests/test_unit_party.py::test_remove_character
---------------------------------------------------------- live log call -----------------------------------------------------------
2023-10-15 19:17:14 [INFO] Adding 'Sckricko' to party 'The B-Team'...
2023-10-15 19:17:14 [INFO] Setting 'Sckricko' as the active character in party 'The B-Team'...
2023-10-15 19:17:14 [INFO] Set 'Sckricko' as the active character in the party.
PASSED                                                                                                                       [ 50%]
../tests/test_unit_party.py::test_remove_character_not_in_party PASSED                                                       [100%]

================================================ 2 passed, 194 deselected in 0.03s =================================================
```

# osrgame: Textual TUI for an OSR-style turn-based RPG

The `osrgame` package provides user interface for the OSR Console application--it's the thing you run to play the game.

## Prerequisites

- Python 3.11+
- Poetry 1.6+

## Installation

Install the application's dependencies and its virtual environment by using Poetry. This command will create a Python virtual environment and install `osrlib` and other dependencies for you.

```sh
# Run from within the <repo-root>/osrgame directory
poetry install
```

## Usage

Launch the OSR Console game application by using Poetry:

```sh
# Run from within the <repo-root>/osrgame directory (same dir as install command)
poetry run python ./osrgame/osrgame.py
```

By starting the game with `poetry run`, you don't have to worry about manually entering a virtual environment because Poetry handles it for you.

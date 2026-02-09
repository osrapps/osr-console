# OSR Console: Adventures in turn-based text

OSR Console is an SDK for a turn-based dungeon crawler RPG in the Old-School Renaissance (OSR) style for your terminal. The SDK's main library, `osrlib`, is written in Python, as is the example user interface which uses the [Textual](https://textual.textualize.io/) TUI framework.

![Screenshot of the OSR Console application running in an iTerm2 window in macOS](images/character-sheet-01.png)

## Prerequisites

- [Python](https://www.python.org/) 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [OpenAI API](https://platform.openai.com/docs/) key (optional, for AI-generated dungeon descriptions)

## Installation

Clone the repo and install all workspace dependencies:

```bash
git clone https://github.com/mmacy/osr-console.git
cd osr-console
uv sync --all-packages
```

## Quickstart

### Run the TUI (osrgame)

The `osrgame` package is a [Textual](https://textual.textualize.io/) terminal UI that demonstrates `osrlib`. Launch it with:

```bash
uv run python -m osrgame
```

Use the on-screen buttons to start a random adventure, load a saved adventure, or quit.

### Run the CLI (osrcli)

The `osrcli` package is an interactive command-line interface built with [questionary](https://github.com/tmbo/questionary). Launch it with:

```bash
uv run osrcli
```

Follow the prompts to create a party, explore dungeons, and manage encounters.

### Run the tests

```bash
uv run pytest tests/
```

## Project structure

This monorepo uses a [uv workspace](https://docs.astral.sh/uv/concepts/workspaces/) with these packages:

- [osrlib](osrlib/README.md) - Core Python library for OSR-style turn-based RPGs
- [osrgame](osrgame/README.md) - Textual TUI demonstrating use of `osrlib`
- [osrcli](osrcli/) - Interactive CLI demonstrating use of `osrlib`
- [tests](tests/README.md) - pytest-based unit and integration tests for `osrlib`

## Usage of AI

A game based on the `osrlib` library can optionally leverage AI to generate text content. In the current implementation, if you have an OpenAI API key, you can have one of their GPT models like `gpt-3.5` or `gpt-4-turbo` generate dungeon location descriptions, encounter battle summaries, and adventure session summaries at runtime.

**The use of AI is entirely optional.** Enabling the creation and play-through of hand-crafted-by-a-human adventures was the original intended use case for the `osrlib` library, and that intent remains.

OpenAI's language models, however, are proving useful in testing the library and for experimentating with using an LLM as a real-time(ish) game content generator. The library acts as the rules engine while the language model produces the long-form content for room descriptions and adventure log-type stuff.

It's also just plain fascinating to see what the LLM comes up with for location descriptions in an auto-generated test dungeon. Provided with only an adventure name and a few sentences for an intro, you can have `osrlib` populate a random dungeon with 'n' locations and then have the language model generate keywords for those locations. Then, as the player moves their party through the dungeon, you can have the LLM generate a location description on-the-fly from the location's keywords.

This screenshot shows an example of LLM-generated content in the (very much *for testing purposes only*) exploration [screen](https://textual.textualize.io/guide/screens/) in `osrgame`, the sample Textual-based TUI:

![Screenshot of the OSR Console TUI's exploration test screen](images/exploration-screen-01.png)

## Contribute

Contributions are welcome! See the open issues or submit a pull request.

## License

[MIT License](LICENSE) for now.

## Credits

- Project owner: [@mmacy](https://github.com/mmacy)
- Game rules and mechanics heavily inspired by TSR's 1981 versions of the Dungeons & Dragons Basic and Expert sets, or *D&D B/X*.

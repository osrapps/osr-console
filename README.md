# OSR Console: Adventures in turn-based text

OSR Console is a turn-based dungeon crawler RPG in the Old-School Renaissance (OSR) style for your terminal. The game's main library, `osrlib`, is written in Python, as is its user interface which uses the [Textual](https://textual.textualize.io/) TUI framework.

![Screenshot of the OSR Console application running in an iTerm2 window in macOS](images/character-sheet-01.png)

## Project status

Character creation isn't quite in, and there are no monsters or spells or combat or anything fun like that. This isn't yet a game you can actually play; more like early-stage hackin' stuff together-type stuff.

👉  = In progress

- [x] Build partial proof-of-concept in private repo.
- [x] Create public repo (this one).
- [x] Init `mkdocs` project (sans actual docs).
- [x] Move `osrlib`, `osrgame`, and `tests` projects to this repo.
- [x] Move to [Poetry](https://python-poetry.org/).
- [ ] 👉 Character save/load in [TinyDB](https://tinydb.readthedocs.io/).
- [ ] Party and character creation workflow in UI.
- [ ] ...and everything else you need for a turn-based dungeon crawler fantasty RPG.

## Prerequisites

- Python 3.11+
- Poetry 1.6+

## Installation

This is a monorepo housing two projects: the game's library, `osrlib`, and its user interface, `osrgame`. For more information about each, see their respective `README.md` files.

- [osrgame: Textual TUI for an OSR-style turn-based RPG](osrgame/README.md)
- [osrlib: Python library for OSR-style turn-based RPGs](osrlib/README.md)

## Usage

TODO

## Contribute

TODO

## License

[MIT License](LICENSE) for now.

## Credits

- Project owner: [@mmacy](https://github.com/mmacy)
- Game rules and mechanics heavily inspired by the TSR's 1981 versions of the Dungeons & Dragons Basic and Expert sets, or *D&D B/X*.

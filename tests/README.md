# tests: pytest module for the OSR Console project

This project houses the unit and integration tests for the [`osrlib`](../osrlib/README.md) package. In the future, it might also house similar tests for [`osrgame`](../osrgame/README.md).

## Prerequisites

- Python 3.11+
- Poetry 1.6+

## Installation

Use Poetry to create a Python virtual environment and install `osrlib` and its dependencies:

```sh
# Create osrlib project venv and install its deps with Poetry
poetry install
```

## Update dependencies

Any time you make code changes to `osrlib`, you need to update this `tests` project to use the latest `osrlib` code before you run the unit and integration tests defined here.

The process goes like this:

1. Make your code change in `osrlib`.
2. Bump `osrlib`'s package version in its [`pyproject.toml`](../osrlib/pyproject.toml) file.

    The version string to bump is in the `[tool.poetry]` section:

    ```toml
    [tool.poetry]
    name = "osrlib"
    version = "0.1.3"
    ```

3. Update *this* project with the latest `osrlib` package version (and your code changes) by running `poetry udpate` from within the `tests/` directory--the same directory as this `README.md` file:

    ```console
    $ poetry update
    Updating dependencies
    Resolving dependencies... (0.2s)

    Package operations: 0 installs, 1 update, 0 removals

    • Updating osrlib (0.1.2 /Users/username/repos/osr-console/osrlib -> 0.1.3 /Users/username/repos/osr-console/osrlib)

    Writing lock file
    ```

## Run all the tests

To run all unit and integration tests, run `pytest` with `poetry run`:

```sh
# Run ALL unit and integration tests in this project - run from within this tests/ directory
poetry run pytest
```

You should see a bunch of test output ending in a summary of the test results. Here's an abridged example of test output:

```console
$ poetry run pytest
============================= test session starts ==============================
platform darwin -- Python 3.11.6, pytest-7.4.2, pluggy-1.3.0
rootdir: /Users/mmacy/repos/osr-console/tests
configfile: pytest.ini

----------------------------- live log collection ------------------------------
2023-10-18 20:13:56 [INFO] Initializing the GameManager...
2023-10-18 20:13:56 [INFO] GameManager initialized. There are 0 adventures available.
2023-10-18 20:13:56 [INFO] Testing dice_roller.py
collected 213 items

...

test_unit_utils.py::test_format_modifiers
-------------------------------- live log call ---------------------------------
2023-10-18 20:14:01 [INFO] Testing empty modifiers: ''
2023-10-18 20:14:01 [INFO] Testing single modifier with positive value: 'To hit: +1'
2023-10-18 20:14:01 [INFO] Testing single modifier with negative value: 'Damage: -1'
2023-10-18 20:14:01 [INFO] Testing single modifier with no (zero) value: 'Open doors: 0'
2023-10-18 20:14:01 [INFO] Testing multiple modifiers with positive and negative values: 'To hit: +1, Damage: -1, Open doors: 0'
PASSED                                                                   [100%]

============================= 213 passed in 0.12s ==============================
```

## Run certain tests

You can pass any argument you normally would to `pytest` when you run it with Poetry.

For example, to run only the test that adds the first character to a party, pass `test_add_firstcharacter` as an arg to the `-k` filtering option:

```console
$ poetry run pytest -k test_add_firstcharacter
============================================ test session starts =============================================
platform darwin -- Python 3.11.6, pytest-7.4.2, pluggy-1.3.0
rootdir: /Users/mmacy/repos/osr-console/tests
configfile: pytest.ini
collecting ...
-------------------------------------------- live log collection ---------------------------------------------
2023-10-19 04:54:56 [INFO] Initializing the GameManager...
2023-10-19 04:54:56 [INFO] GameManager initialized. There are 0 adventures available.
2023-10-19 04:54:56 [INFO] Testing dice_roller.py
collected 213 items / 212 deselected / 1 selected

test_unit_party.py::test_add_firstcharacter
----------------------------------------------- live log call ------------------------------------------------
2023-10-19 04:54:56 [INFO] Adding 'Sckricko' to party 'The B-Team'...
2023-10-19 04:54:56 [INFO] Setting 'Sckricko' as the active character in party 'The B-Team'...
2023-10-19 04:54:56 [INFO] Set 'Sckricko' as the active character in the party.
PASSED                                                                                                 [100%]

===================================== 1 passed, 212 deselected in 0.03s ======================================
```

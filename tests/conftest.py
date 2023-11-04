import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--run-optin-tests", action="store_true", default=False, help="Include tests marked with the 'optin' marker in the test run."
    )

def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-optin-tests"):
        # Do not NOT exclude tests marked with the 'optin' marker, so return early.
        # The --run-optin-tests option was passed on the command line.
        return
    skip_optin = pytest.mark.skip(reason="Test marked opt-in. To run it, pass --run-optin-tests to pytest at the command line.")
    for item in items:
        if "optin" in item.keywords:
            item.add_marker(skip_optin)

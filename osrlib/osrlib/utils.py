"""Utility functions and globals for logging and working with strings, paths, and other common tasks.

To enable debug logging, set the environment variable `OSR_DEBUG` to `true`. Otherwise, logging is set to INFO level.
"""
import os
import platform
import textwrap
import re
import logging
from pathlib import Path

from osrlib.ability import ModifierType


def format_modifiers(modifiers: dict[ModifierType, int]) -> str:
    """Get a string representation of the given modifiers.

    The formatted modifier string returned by this function is a comma-delimited list of the given modifiers. Each
    modifier includes its name and value. The value string includes its polarity if it's positive or negative.

    Example:

        >>> # This should return "Strength: +1, Dexterity: -1"
        >>> format_modifiers({ModifierType.STRENGTH: 1, ModifierType.DEXTERITY: -1})

    Args:
        modifiers: A dictionary of modifiers to format.

    Returns:
        A comma-delimited string representation of the modifiers.
    """
    return ", ".join(
        f"{mod.value}: {'+' if val > 0 else ''}{val}" for mod, val in modifiers.items()
    )


def wrap_text(text: str, width: int = 100) -> str:
    """
    Wrap a given string of text to a specified width.

    This function utilizes the `textwrap` module to break a long string of text into lines of
    a given width. It's particularly useful for formatting long strings into a more readable
    form, especially in user interfaces where space is limited.

    Args:
        text (str): The text string to be wrapped.
        width (int, optional): The maximum width of the wrapped lines. Defaults to 100 characters.

    Returns:
        str: A new string with the original text wrapped to the specified width.

    Example:
        >>> sample_text = "This is a long text string that needs to be wrapped for better readability."
        >>> print(wrap_text(sample_text, 40))
        This is a long text string that needs
        to be wrapped for better readability.
    """
    return textwrap.fill(text, width)


def sanitize_path_element(path_element: str, replace_space: str = "_") -> str:
    """
    Sanitize a string to ensure it's a valid path element for file and directory names.

    This function removes or replaces characters that are not allowed in file and directory names
    on various operating systems. Use this function to sanitize any part of a file path.

    Args:
        path_element (str): The path element (e.g., file name, directory name) to sanitize.
        replace_space (str, optional): The character to replace spaces with. Defaults to '_'.
                                       Set to None to remove spaces instead.

    Returns:
        str: The sanitized path element.

    Example:
        >>> sanitized_name = sanitize_path_element("Invalid/Name*<>?")
        >>> print(sanitized_name)
        InvalidName
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "", path_element)

    # Replace or remove spaces
    if replace_space is not None:
        sanitized = sanitized.replace(" ", replace_space)
    else:
        sanitized = sanitized.replace(" ", "")

    # Limit length (optional, here 255 characters as an example)
    sanitized = sanitized[:255]

    return sanitized


def create_dir_tree_if_not_exist(directory: Path):
    """
    Create the entire directory tree if it does not already exist.

    This function checks if the specified directory exists, and if not, it creates not only
    the directory but also any necessary parent directories. It's useful for ensuring that
    the entire path structure is ready for file operations.

    Args:
        directory (Path): The Path object representing the directory to check and create.

    Raises:
        OSError: If the directory cannot be created due to permissions or other file system errors.
    """
    if not directory.exists():
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Unable to create directory tree {directory}: {e}")


def get_data_dir_path(app_name: str) -> Path:
    """
    Determine the appropriate directory for saving game data based on the operating system.

    This function dynamically identifies the standard directory for storing application data
    on different platforms (Windows, macOS, Linux/Unix-like). On Windows, it uses the
    'LOCALAPPDATA' environment variable to find the local application data folder. On macOS,
    it defaults to the 'Library/Application Support' directory within the user's home directory.
    For Linux and Unix-like systems, it uses the 'XDG_DATA_HOME' environment variable, defaulting
    to '.local/share' in the user's home directory if the variable is not set.

    Args:
        app_name (str): The name of the application. Used to create a subdirectory within the standard
                         application data directory.

    Returns:
        Path: An object representing the absolute path to the directory where game save data
              should be stored.

    Raises:
        ValueError: If the operating system is not supported (not Windows, macOS, or Linux/Unix-like).

    Example:
        >>> game_save_dir = get_save_game_directory("YourAppName")
        >>> print(game_save_dir)
        /home/username/.local/share/YourAppName  # On Linux
        C:\\Users\\username\\AppData\\Local\\YourAppName  # On Windows
        /Users/username/Library/Application Support/YourAppName  # On macOS
    """
    system = os.name
    if system == "nt":  # Windows
        base_dir = Path(os.environ.get("LOCALAPPDATA", ""))
    elif system == "posix":
        if platform.system() == "Darwin":  # macOS
            base_dir = Path.home() / "Library" / "Application Support"
        else:  # Linux and Unix-like
            base_dir = Path(
                os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
            )
    else:
        raise ValueError("Unsupported operating system.")

    return base_dir / sanitize_path_element(app_name)

class LastMessageHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.last_message = None

    def emit(self, record):
        self.last_message = self.format(record)

    def format(self, record):
        # Return only the message part of the log record
        return record.getMessage()

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s][%(module)s::%(funcName)s] %(message)s",
)

logger = logging.getLogger(__name__)

if os.environ.get("OSR_DEBUG", "").lower() == "true":
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
last_message_handler = LastMessageHandler()
logger.addHandler(last_message_handler)
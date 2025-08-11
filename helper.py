import sys
import os


def resource_path(relative_path: str) -> str:
    # If the attribute does not exist (since we are in development mode),
    # getattr() returns the default value: the absolute path of the current directory.
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))

    return os.path.join(base_path, relative_path)
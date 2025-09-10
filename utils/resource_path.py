import os, sys

def get_resource_path(relative_path: str) -> str:
    try:
        # When running from a PyInstaller bundle, resources are extracted
        # into a temporary folder accessible via sys._MEIPASS
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.normpath(os.path.join(base_path, relative_path))
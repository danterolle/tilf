import os
import sys


def get_resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    return os.path.normpath(os.path.join(base_path, relative_path))

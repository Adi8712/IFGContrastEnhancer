"""Resource helpers used by the application (packaging-friendly)"""

import os
import sys
from typing import Optional


def resource_path(rel_path: str, base: Optional[str] = None) -> str:
    """
    Resolve a file path that works both in source layout and when bundled by
    PyInstaller (which sets sys._MEIPASS)

    Parameters
    ----------
    rel_path : str
        Relative path inside the project (e.g. "samples" or "data/foo.png")
    base : Optional[str]
        Optional explicit base directory override (used in tests or custom runners)

    Returns
    -------
    str
        Absolute filesystem path to the requested resource
    """
    if base is None:
        base = getattr(sys, "_MEIPASS", None) or os.path.abspath(".")
    return os.path.join(base, rel_path)

"""Select the active song module via $SONG (default: song).
Each song module must expose build_song() and TITLE (output slug)."""

import os
import importlib


def get_song():
    return importlib.import_module(os.environ.get("SONG", "song"))


def build_song():
    return get_song().build_song()


def title():
    return getattr(get_song(), "TITLE", "song")

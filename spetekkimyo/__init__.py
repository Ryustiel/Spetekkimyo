import os

# CONSTANTS =================================================

# Define the base directory for the `spetekkimyo` package dynamically
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEBUG_EXAMPLE = ["s", "p", "e", "t", "e", "k"]

# Adjust paths to be relative to the `BASE_DIR`
FEATURE_PATH = os.path.join(BASE_DIR, "generated/features.fea")
GLYPH_FOLDER_PATH = os.path.join(BASE_DIR, "glyphs/")
SETS_PATH = os.path.join(BASE_DIR, "sets.json")
DEFAULT_OUTPUT_PATH = os.path.join(BASE_DIR, "generated/seiso.otf")
DEBUG_LOG_PATH = os.path.join(BASE_DIR, "generated/log.txt")

# Other constants
DEFAULT_GLYPH = "head/a.eps"  # This is the location of a glyph RELATIVE to the GLYPH_FOLDER

# FUNCTIONS =================================================

import fontforge
from .index import GlyphIndex
from .features import ClassIndex, Feature, install_feature
from .config import generate_font

# EXPORTS ===================================================

__all__ = [
    "GlyphIndex",
    "ClassIndex",
    "Feature",
    "install_feature",
    "fontforge",
    "generate_font",
]
# CONSTANTS =================================================

DEFAULT_GLYPH = "head/a.eps"
FEATURE_PATH = "./spetekkimyo/generated/features.fea"
GLYPH_FOLDER_PATH = "./spetekkimyo/glyphs/"
SETS_PATH = "./spetekkimyo/sets.json"
DEFAULT_OUTPUT_PATH = "./spetekkimyo/generated/seiso.otf"

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

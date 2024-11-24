"""
Defines general parameters for the font, 
import glyphs and features.

CREATE FONT
"""
import fontforge
from .index import GlyphIndex
from .features import ClassIndex, Feature, install_feature
from . import DEFAULT_GLYPH, FEATURE_PATH, DEFAULT_OUTPUT_PATH, SETS_PATH, GLYPH_FOLDER_PATH, DEBUG_LOG_PATH, DEBUG_EXAMPLE

def generate_font(output_path: str = DEFAULT_OUTPUT_PATH):

    # DATA OBJECTS

    font = fontforge.font()
    glyphs = GlyphIndex(font, GLYPH_FOLDER_PATH, SETS_PATH, DEFAULT_GLYPH)  # Loads the glyphs from the folder
    classes = ClassIndex(font, glyphs)
    
    # FEATURES

    feature = Feature("ccmp", font, glyphs, classes)

    # FONT METADATA

    font.fontname = "Seiso"
    font.fullname = "spe seiso tekkimyo"
    font.familyname = "Seiso"
    font.encoding = "UnicodeFull"  # Use full Unicode encoding

    # DEFINE LOOKUPS

    feature.REPLACE("f", "f2")  # TODO : Fix replacement value treated as a list (string indexes 1, 2 separated : check the output)

    # nealajabm osei tai sob
    feature.APPEND_LEFT([], "Ha glyphs", [], "Ha")
    feature.APPEND_LEFT([], "Ho glyphs", [], "Ho")

    # 'nealajabm o''s'ei ''t'ai ''s'o'''b
    ...

    _, message = feature.apply_lookups(glyph_list=DEBUG_EXAMPLE, display=False, debug=True)
    with open(DEBUG_LOG_PATH, 'w') as f:
        f.write(message)

    install_feature(f"{classes} \n{feature}", FEATURE_PATH, font, debug=True)

    font.generate(output_path)

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

    feature = Feature("ccmp", font, glyphs, classes, language=["dflt", "dflt"], script=["DFLT", "latn"])

    # FONT METADATA

    font.fontname = "Seiso"
    font.fullname = "spe seiso tekkimyo"
    font.familyname = "Seiso"
    font.encoding = "UnicodeFull"  # Use full Unicode encodingdisc

    # DEFINE LOOKUPS

    # Step 1 : Preprocess height glyphs
    feature.SUBSTITUTION(["t"], "a", [], ["head.t.a", "tail.a"])

    # 'nealajabm o''s'ei ''t'ai ''s'o'''b
    ...

    _, message = feature.apply_lookups(glyph_list="t a i s t a i".split(), display=False, debug=True)
    with open(DEBUG_LOG_PATH, 'w') as f:
        f.write(message)

    install_feature(f"{classes} \n{feature}", FEATURE_PATH, font, debug=True)

    font.generate(output_path)

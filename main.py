"""
Defines general parameters for the font, 
import glyphs and features.

CREATE FONT
"""
import fontforge
from index import GlyphIndex
from features import ClassIndex, Feature, install_feature
import os

DEFAULT_GLYPH = "head/a.eps"
FEATURE_PATH = "features.fea"
OUTPUT_PATH = "C:/Users/rapha/Documents/ExampleFont.otf"

print(os.getcwd())  # Print the current working directory

font = fontforge.font()
glyphs = GlyphIndex(font, "glyphs/", "sets.json", DEFAULT_GLYPH)  # Loads the glyphs from the folder
classes = ClassIndex(font, glyphs)
feature = Feature("ccmp", font, glyphs, classes)

# FONT METADATA

font.fontname = "ExampleFont"
font.fullname = "Example Font"
font.familyname = "Example Font Family"
font.encoding = "UnicodeFull"  # Use full Unicode encoding

# DEFINE LOOKUPS

feature.REPLACE("f", "f2")  # TODO : Fix replacement value treated as a list (string indexes 1, 2 separated : check the output)

# nealajabm osei tai sob
feature.APPEND_LEFT([], "Ha glyphs", [], "Ha")
feature.APPEND_LEFT([], "Ho glyphs", [], "Ho")

# 'nealajabm o''s'ei ''t'ai ''s'o'''b
...

install_feature(f"{classes} \n{feature}", FEATURE_PATH, font, debug=True)

font.generate(OUTPUT_PATH)

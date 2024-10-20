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

# nealajabm osei tai sob
feature.SUBSTITUTION([["#start", "o"]], "a", [], "e")

# 'nealajabm o''s'ei ''t'ai ''s'o'''b
...

install_feature(str(classes) + " \n" + str(feature), FEATURE_PATH, font, True)

font.generate(OUTPUT_PATH)

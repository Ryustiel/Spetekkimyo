"""
Defines general parameters for the font, 
import glyphs and features.

CREATE FONT
"""
import fontforge
from index import GlyphIndex
from features import Features
import os

DEFAULT_GLYPH = "head/a.eps"

print(os.getcwd())  # Print the current working directory

font = fontforge.font()
index = GlyphIndex(font, "glyphs/", "sets.json", DEFAULT_GLYPH)  # Loads the glyphs from the folder

# METADATA
font.fontname = "ExampleFont"
font.fullname = "Example Font"
font.familyname = "Example Font Family"
font.encoding = "UnicodeFull"  # Use full Unicode encoding

features = Features(font, index)

print(features.substitutions.tables)
print(features.classes.classes)

font.generate("C:/Users/rapha/Documents/ExampleFont.otf")

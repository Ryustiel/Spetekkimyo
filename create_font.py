"""
Defines general parameters for the font, 
import glyphs and features.
"""
import fontforge
from index import GlyphIndex
import features
import os

print(os.getcwd())  # Print the current working directory

font = fontforge.font()
index = GlyphIndex(font)  # Loads the glyphs from the folder

# METADATA
font.fontname = "ExampleFont"
font.fullname = "Example Font"
font.familyname = "Example Font Family"
font.encoding = "UnicodeFull"  # Use full Unicode encoding

for attr_name in dir(features):
    if callable(getattr(features, attr_name)):
        print(f"EXECUTING {attr_name}")

font.generate("C:/Users/rapha/Documents/ExampleFont.otf")

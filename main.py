"""
Defines general parameters for the font, 
import glyphs and features.

CREATE FONT
"""
import fontforge
from index import GlyphIndex
from features import ClassIndex, Feature
import os

DEFAULT_GLYPH = "head/a.eps"

print(os.getcwd())  # Print the current working directory

font = fontforge.font()
glyphs = GlyphIndex(font, "glyphs/", "sets.json", DEFAULT_GLYPH)  # Loads the glyphs from the folder
classes = ClassIndex(font, glyphs)

# METADATA
font.fontname = "ExampleFont"
font.fullname = "Example Font"
font.familyname = "Example Font Family"
font.encoding = "UnicodeFull"  # Use full Unicode encoding

feature = Feature("ccmp", font, glyphs, classes)

feature.REPLACE("a", "o")
feature.SUBSTITUTION(["o", "b"], ["e", "u"], ["o", "b"], "o")

print(classes)
print(feature)

# with open("features.fea", "w") as f:
#     f.write()

try:
    font.mergeFeature("features.fea")
    print("Features successfully imported.")
except Exception as e:
    print(f"An error occurred while importing features: {e}")

font.generate("C:/Users/rapha/Documents/ExampleFont.otf")

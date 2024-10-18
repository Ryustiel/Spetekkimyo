
import fontforge
from index import GlyphIndex, GlyphManager
import features
import os

print(os.getcwd())  # Print the current working directory

font = fontforge.font()
index = GlyphIndex(font, "glyphs/", "sets.json")  # Loads the glyphs from the folder

print(index["jl.large"])
print(index["head.k.a"])
print(index["space"])
print(index.gset("a"))
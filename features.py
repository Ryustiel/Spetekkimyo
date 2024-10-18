"""
Define how chains of glyphs are produced from a sentence input.
Define classes of characters via index (relevant checks and imports are run in index).
"""
import fontforge
from index import GlyphIndex
from lookups import *
from typing import Union, List

class Features():

    def __init__(self, font: fontforge.font, index: GlyphIndex):
        self.font = font
        self.index = index
        self.classes = ClassIndex(font, index)
        self.substitutions = SubstitutionManager(font, index, self.classes)

        # Runs feature creation functions
        self.HEIGHT_ADJUSTMENT()


    def HEIGHT_ADJUSTMENT(self):
        """
        Create height adjustment characters by adding 'a_height' glyph before letters that are not
        adjacent to other letters. If a letter has another letter before or after it, it will be
        skipped and no height adjustment will be added.

        This function sets up GSUB tables and context chain rules to achieve this behavior.
        """
        lookup1 = ContextualLookup(self.font, self.index, self.substitutions, "STEP 1")
        lookup2 = ContextualLookup(self.font, self.index, self.substitutions, "STEP 2")

        # lookup1.APPEND_LEFT([], "a", [], "e")
        lookup2.REPLACE([], "a", [], "o")

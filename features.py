"""
Define how chains of glyphs are produced from a sentence input.
Define classes of characters via index (relevant checks and imports are run in index).
"""

def test_lookup(font, index):
    # 1. Add a 'ccmp' lookup (character composition/substitution)
    font.addLookup("ccmp_substitution", "gsub_multiple", None, (("ccmp", (("latn", "dflt"),)),))
    # 2. Add a subtable for this lookup
    font.addLookupSubtable("ccmp_substitution", "ccmp_substitution_sub")
    # 3. Add substitution rule: Replace 'a' with 'head.a' followed by 'tail.a'
    index["glyph_a"].addPosSub("ccmp_substitution_sub", ["head.a", "tail.a"])  # Replace 'a' with 'head.a' + 'tail.a'
import os
import sys
from typing import List # type: ignore
from pathlib import Path # type: ignore
import fontforge
import json

if len(sys.argv) <= 1: raise ValueError("Missing output_dir argument")

root_dir = Path(__file__).parent.resolve()
feature_path = root_dir / 'input' / 'features.fea'
glyph_dir = root_dir / 'input' / 'glyphs'
padding_path = root_dir / 'input' / 'padding.json'
output_path = root_dir / Path(sys.argv[1]) if sys.argv[1][1] == ":" else Path(sys.argv[1])

font = fontforge.font()

# CONFIG ========================================

font.fontname = "Seiso"
font.fullname = "spe seiso tekkimyo"
font.familyname = "Seiso"
font.encoding = "UnicodeFull"  # Use full Unicode encodingdisc

default_padding = 0

# END CONFIG ====================================

with open(padding_path, 'r') as f: padding_dict = json.load(f)

imported: List[str] = []

for entry in os.listdir(glyph_dir):

    glyph_path = os.path.join(glyph_dir, entry)
    if os.path.isfile(glyph_path):

        glyph_name = entry.removesuffix(".eps")
        imported.append(glyph_name)
        
        glyph = font.createChar(-1, glyph_name)
        glyph.importOutlines(glyph_path)
        
        # Set glyph width based on rightmost point
        bbox = glyph.boundingBox()
        # Use custom padding if available, otherwise use default
        padding = padding_dict.get(glyph_name, default_padding)
        glyph.width = int(bbox[2] + padding)  # Use xmax (rightmost point) + padding

print("Imported", len(imported), "glyphs:", " ".join(imported))

font.mergeFeature(str(feature_path))
print("Imported features")

font.generate(str(output_path))

print("Font generated at", output_path)

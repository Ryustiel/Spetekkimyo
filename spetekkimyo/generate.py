
import os
import sys
import fontforge
from typing import List # type: ignore
from pathlib import Path # type: ignore

if len(sys.argv) <= 1: raise ValueError("Missing output_dir argument")

root_dir = Path(__file__).parent.resolve()
feature_path = root_dir / 'input' / 'features.fea'
glyph_dir = root_dir / 'input' / 'glyphs'
output_path = root_dir / Path(sys.argv[1])

font = fontforge.font()

font.fontname = "Seiso"
font.fullname = "spe seiso tekkimyo"
font.familyname = "Seiso"
font.encoding = "UnicodeFull"  # Use full Unicode encodingdisc

imported: List[str] = []

for entry in os.listdir(glyph_dir):

    glyph_path = os.path.join(glyph_dir, entry)
    if os.path.isfile(glyph_path):

        glyph_name = entry.removesuffix(".eps")
        imported.append(glyph_name)
        
        glyph = font.createChar(-1, glyph_name)
        glyph.importOutlines(glyph_path)

print("Imported", len(imported), "glyphs:", " ".join(imported))

# font.mergeFeature(str(feature_path))
print("Imported features :)")

# font.generate(str(output_path))

print("Font generated at", output_path)

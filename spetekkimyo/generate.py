
import os
import sys
import fontforge
from pathlib import Path # type: ignore

print("hello")

if len(sys.argv) <= 1: raise ValueError("Missing output_dir argument")

root_dir = Path(__file__).parent.resolve()
feature_path = root_dir / 'input' / 'features.fea'
glyph_dir = root_dir / 'input' / 'glyphs'
output_dir = root_dir / Path(sys.argv[1])

font = fontforge.font()

font.fontname = "Seiso"
font.fullname = "spe seiso tekkimyo"
font.familyname = "Seiso"
font.encoding = "UnicodeFull"  # Use full Unicode encodingdisc

for entry in os.listdir(glyph_dir):
    full_path = os.path.join(glyph_dir, entry)
    if os.path.isfile(full_path):
        print(entry)

# glyph = font.createChar(-1, glyph_name)
# glyph.importOutlines(os.path.join(dirpath, filename))

# font.mergeFeature(str(feature_path))
# print("Features successfully imported.")

# font.generate(output_path)

print("Font successfully generated at", output_dir)

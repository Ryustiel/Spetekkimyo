# FontForge script to export each glyph as a .eps file

import fontforge
import os

# Define the path to the .sfd font file
input_sfd_path = "rework.sfd"

# Open the font using FontForge
font = fontforge.open(input_sfd_path)

# Create a new directory for the EPS files
output_directory = "result"
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Iterate over all glyphs in the font
for glyph in font.glyphs():
    # Generate EPS filename using the glyph name
    eps_filename = os.path.join(output_directory, f"{glyph.glyphname}.eps")

    # Print the glyph name for informational purposes
    print(f"Exporting {glyph.glyphname} to {eps_filename}")

    # Select the glyph and export it as an EPS file
    glyph.export(eps_filename)

# Close the font to free resources
font.close()

print("All glyphs have been exported.")
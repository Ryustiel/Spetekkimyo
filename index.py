"""
Glyph index : imports glyphs from the glyph folder or create them.
Also creates the main combination paths.
"""

import os
import fontforge
from typing import List, Dict # type: ignore

class GlyphIndex:
    """
    Glyph index: imports glyphs from the glyph folder or creates them.
    """

    def __init__(self, font: fontforge.font):
        self.font = font
        self.glyphs_folder = "./glyphs"
        self.solo_letters_mapping = {}      # Maps letters to their glyph components
        self.loaded_glyphs = {}             # Maps glyph names (e.g., 'head.a') to glyph objects
        self.glyph_sets = {}                # Maps set names to lists of glyph dictionaries

        self._load_glyphs()
        self._count_loaded_letters()
        self.create_standalone_vowels()

    def _load_glyphs(self):
        """
        Load all glyphs from the glyphs folder. Raise an error if the folder
        does not exist or is empty. Adds loaded glyphs as class properties
        and maintains a mapping from glyph names to glyph objects.
        """
        if not os.path.isdir(self.glyphs_folder):
            raise FileNotFoundError(f"Glyphs folder '{self.glyphs_folder}' does not exist.")

        glyph_files = [f for f in os.listdir(self.glyphs_folder) if f.endswith('.eps')]
        if not glyph_files:
            raise FileNotFoundError(f"No glyph files found in '{self.glyphs_folder}'.")

        for file_name in glyph_files:
            base_name = os.path.splitext(file_name)[0]  # Remove .eps extension
            parts = base_name.split('.')

            # Add glyphs with single-component names only (e.g., head.a, tail.o)
            if len(parts) >= 2 and len(parts[1]) == 1:
                if len(parts) == 2:
                    glyph_type, letter = parts
                    glyph_name = f"{glyph_type}.{letter}"
                    glyph_property_name = f"glyph_{glyph_type}_{letter}"

                elif len(parts) == 3:
                    glyph_type, letter, next = parts
                    glyph_name = f"{glyph_type}.{letter}.{next}"
                    glyph_property_name = f"glyph_{glyph_type}_{letter}_{next}"

                elif len(parts) == 4:
                    glyph_type, letter, next, next2 = parts
                    glyph_name = f"{glyph_type}.{letter}.{next}.{next2}"
                    glyph_property_name = f"glyph_{glyph_type}_{letter}_{next}_{next2}"
                

                # Create the glyph without a Unicode mapping
                glyph = self.font.createChar(-1, glyph_name)
                glyph.importOutlines(os.path.join(self.glyphs_folder, file_name))

                # Add the glyph as a property of the class
                setattr(self, glyph_property_name, glyph)

                # Update the solo_letters_mapping dictionary
                if letter not in self.solo_letters_mapping:
                    self.solo_letters_mapping[letter] = {}
                self.solo_letters_mapping[letter][glyph_type] = glyph

                # Update the loaded_glyphs dictionary
                self.loaded_glyphs[glyph_name] = glyph

    def _count_loaded_letters(self):
        """
        Debug print the number of unique single-letter glyphs loaded.
        """
        unique_letters = set(self.solo_letters_mapping.keys())
        print(f"Loaded {len(unique_letters)} unique single-letter glyphs: {', '.join(sorted(unique_letters))}")

    def exists(self, glyph_name: str) -> bool:
        """
        Check if a glyph with the given name exists.

        :param glyph_name: The name of the glyph to check (e.g., 'head.a').
        :return: True if the glyph exists, False otherwise.
        """
        return glyph_name in self.loaded_glyphs

    def create_set(self, set_name: str, glyph_names: List[str]):
        """
        Create a set of glyphs and store it in the class.

        :param set_name: The name of the set to create.
        :param glyph_names: A list of glyph names to include in the set.
        :raises ValueError: If any of the glyphs in glyph_names do not exist.
        """
        if set_name in self.glyph_sets:
            raise ValueError(f"Set '{set_name}' already exists.")

        glyph_set = []
        missing_glyphs = []
        for name in glyph_names:
            if self.exists(name):
                glyph_set.append({name: self.loaded_glyphs[name]})
            else:
                missing_glyphs.append(name)

        if missing_glyphs:
            raise ValueError(f"The following glyph(s) do not exist and cannot be added to the set '{set_name}': {', '.join(missing_glyphs)}")

        self.glyph_sets[set_name] = glyph_set
        print(f"Set '{set_name}' created with {len(glyph_set)} glyph(s).")

    def get_set(self, set_name: str) -> List[Dict[str, fontforge.glyph]]:
        """
        Retrieve a set of glyphs by its name.

        :param set_name: The name of the set to retrieve.
        :return: A list of dictionaries mapping glyph names to glyph objects.
        :raises KeyError: If the set_name does not exist.
        """
        if set_name not in self.glyph_sets:
            raise KeyError(f"Set '{set_name}' does not exist.")
        return self.glyph_sets[set_name]

    def create_standalone_vowels(self):
        """
        Create glyphs for standalone vowels by merging their head and tail components.
        This method can be extended to handle more vowels as needed.
        """
        vowels = ['a', 'e', 'o', 'u']  # Extend this list as needed
        for vowel in vowels:
            head_key = 'head'
            tail_key = 'tail'

            # Ensure both head and tail components are loaded for the vowel
            if (vowel in self.solo_letters_mapping and
                head_key in self.solo_letters_mapping[vowel] and
                tail_key in self.solo_letters_mapping[vowel]):

                # Create the standalone vowel glyph with the appropriate Unicode code point
                unicode_code = ord(vowel)
                standalone_glyph = self.font.createChar(unicode_code, vowel)
                pen = standalone_glyph.glyphPen()

                # Draw head component at original position
                self.solo_letters_mapping[vowel][head_key].draw(pen)

                # Draw tail component shifted horizontally by 300 units
                transform_matrix = (1, 0, 0, 1, 300, 0)  # Identity matrix with translation
                self.solo_letters_mapping[vowel][tail_key].draw(pen, transform_matrix)

                print(f"Created standalone glyph for vowel '{vowel}'.")
            else:
                print(f"Skipping creation of standalone glyph for vowel '{vowel}' as required components are missing.")

    def createset_from_existing_sets(self, new_set_name: str, existing_set_names: List[str]):
        """
        Create a new set by combining existing sets.

        :param new_set_name: The name of the new set to create.
        :param existing_set_names: A list of existing set names to combine.
        :raises KeyError: If any of the existing sets do not exist.
        """
        combined_set = []
        for existing_set in existing_set_names:
            if existing_set not in self.glyph_sets:
                raise KeyError(f"Set '{existing_set}' does not exist and cannot be combined.")
            combined_set.extend(self.glyph_sets[existing_set])

        if new_set_name in self.glyph_sets:
            raise ValueError(f"Set '{new_set_name}' already exists.")

        self.glyph_sets[new_set_name] = combined_set
        print(f"Set '{new_set_name}' created by combining sets: {', '.join(existing_set_names)}.")


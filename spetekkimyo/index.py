import os
import fontforge
import json
import logging
from typing import List, Dict, Union

class GlyphMissingError(Exception):
    """Exception raised for missing glyphs."""
    pass

class GlyphManager:
    """
    Imports all the glyphs from the glyph folder and subfolders 
    and exposes them as a dictionary, using a flattened key structure.
    """
    glyphs: Dict[str, fontforge.glyph]

    def __init__(self, font: fontforge.font, glyph_folder: str):
        self.font = font
        self.glyphs_folder = glyph_folder
        self.glyphs = {}
        self.import_glyphs()

    def import_glyphs(self):
        """
        Imports glyphs from the folder and its subfolders to self.glyphs.
        Stores glyphs using a flattened key structure.
        """
        if not os.path.isdir(self.glyphs_folder):
            raise FileNotFoundError(f"Glyphs folder '{self.glyphs_folder}' does not exist.")

        for dirpath, _, filenames in os.walk(self.glyphs_folder):
            for filename in filenames:
                if filename.endswith('.eps'):
                    # Determine the glyph's key based on the relative path
                    relative_path = os.path.relpath(dirpath, self.glyphs_folder)
                    key = os.path.splitext(filename)[0]
                    if relative_path != '.':
                        key = f"{relative_path.replace(os.path.sep, '.')}.{key}"

                    # Import the glyph using fontforge
                    glyph_name = self._construct_glyph_name(dirpath, filename)
                    glyph = self.font.createChar(-1, glyph_name)
                    glyph.importOutlines(os.path.join(dirpath, filename))

                    # print(f"{glyph_name} ADDED as {os.path.join(dirpath, filename)}")
                    
                    # Add the glyph directly to the flat glyph dictionary
                    self.glyphs[key] = glyph

    def glyph_exists(self, glyph_name: str) -> bool:
        return glyph_name in self.glyphs.keys()

    def _construct_glyph_name(self, dirpath: str, filename: str) -> str:
        """
        Constructs the glyph name based on the subfolder structure and file name.

        :return: The created glyph name.
        """
        base_name = os.path.splitext(filename)[0]
        rel_path = os.path.relpath(dirpath, self.glyphs_folder)
        relative_glyph_name = rel_path.replace(os.path.sep, '.')

        if len(relative_glyph_name) > 1:  # more than a "." was detected
            glyph_name = f"{relative_glyph_name}.{base_name}"
        else:
            glyph_name = base_name

        return glyph_name

    def __getitem__(self, glyph_name: str) -> fontforge.glyph:
        """
        Returns the glyph with the given name.
        Raises a KeyError if the glyph does not exist.
        """
        if glyph_name in self.glyphs:
            return self.glyphs[glyph_name]
        else:
            raise KeyError(f"Glyph '{glyph_name}' does not exist.")

    def __setitem__(self, key: str, glyph: fontforge.glyph):
        """
        Allows adding or updating a glyph using subscript notation.
        """
        self.glyphs[key] = glyph

class GlyphIndex(GlyphManager):
    """
    Imports all the glyphs from the glyph folder and subfolders 
    and exposes them as a dictionary with a flattened key structure.
    Also provides accessor functions based on a "glyph set" config file.
    """
    def __init__(self, font: fontforge.font, glyph_folder: str, gset_path: str, default_glyph: str):
        self.gset_path = gset_path
        self.glyphs_folder = glyph_folder
        self.default_glyph = default_glyph

        super().__init__(font, glyph_folder)

        # Checks if sets components were loaded, load them as default otherwise
        missing_glyphs = self._check_sets()
        for glyph_name in missing_glyphs:
            glyph = self.font.createChar(-1, glyph_name) # CREATE missing glyphs as default glyphs to be used as intermediate steps in lookups
            glyph.importOutlines(os.path.join(self.glyphs_folder, self.default_glyph))
            self.glyphs.update({glyph_name: glyph})
        if len(missing_glyphs) > 0:
            print(f"\nLoaded missing glyphs as DEFAULT GLYPH : {missing_glyphs}\n")
            # raise GlyphMissingError(missing_glyphs)

    def gset(self, set_name: str) -> List[str]:
        """
        Returns a set of glyphs defined in sets.json as a list of glyph names.
        Raises a KeyError if the set does not exist.
        """
        assert self.gset_path, "gset_path must be set"
        
        with open(self.gset_path, "r") as f:
            sets = json.load(f)

        if set_name not in sets.keys():
            raise KeyError(f"Glyph set '{set_name}' does not exist.")

        glyph_names = sets[set_name]
        return glyph_names
    
    def gset_glyphs(self, set_name: str) -> List[fontforge.glyph]:
        """
        Returns a set of glyphs defined in sets.json as a list of GLYPH objects.
        """
        glyph_names = self.gset(set_name)
        return [self[glyph_name] for glyph_name in glyph_names]
    
    def gset_exists(self, set_name: str) -> bool:
        with open(self.gset_path, "r") as f:
            sets = json.load(f)
        return set_name in sets.keys()
    
    def get_glyph_or_gset(self, inp: str) -> List[str]:
        """
        Returns the name of the glyph in a standard List, 
        or a gset if the input is the name of a gset.
        Raise an error if the name was neither part of the gsets or the loaded glyphs.
        """
        if self.glyph_exists(inp):
            return [inp]
        elif self.gset_exists(inp):
            return self.gset(inp)
        else:
            raise KeyError(f"Neither a glyph nor a glyph set found for '{inp}'.")


    def _check_sets(self) -> List[str]:
        """
        FOR DEFAULT LOAD
        Checks if all the glyphs defined in the gset_path json have been loaded.
        Returns a list of (missing glyph name) to be loaded as default glyphs.
        """
        assert self.gset_path, "gset_path must be set"
        
        with open(self.gset_path, "r") as f:
            sets = json.load(f)

        missing_glyphs = []
        
        for set_name, glyph_names in sets.items():
            for glyph_name in glyph_names:
                try:
                    self[glyph_name]
                except KeyError:
                    if not glyph_name in missing_glyphs and not " " in glyph_name and not "#" in glyph_name:
                        missing_glyphs.append(f"{glyph_name}")
        
        return missing_glyphs
    
    def _check_sets_no_load(self) -> List[str]:
        """
        Checks if all the glyphs defined in the gset_path json have been loaded.
        Returns a list of (set name).(missing glyph name) indicating which glyphs were missing.
        """
        assert self.gset_path, "gset_path must be set"
        
        with open(self.gset_path, "r") as f:
            sets = json.load(f)

        missing_glyphs = []
        
        for set_name, glyph_names in sets.items():
            for glyph_name in glyph_names:
                try:
                    self[glyph_name]
                except KeyError:
                    missing_glyphs.append(f"{set_name}.{glyph_name}")
        
        return missing_glyphs
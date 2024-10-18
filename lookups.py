"""
Create an interface on fontforge to create lookup tables easily.
"""
import fontforge
from index import GlyphIndex
from typing import Union, List

GLYPH = str
SET = str
LOOKUP = str
CLASS = str

def _create_gsub_multiple(font: fontforge.font, name: str):  # Create a gsub table
    """
    Create a character substitution table and subtable with the same name.
    """
    font.addLookup(name, "gsub_multiple", None, (("ccmp", (("latn", "dflt"),)),))
    font.addLookupSubtable(name, name)

def _create_contextchain(font: fontforge.font, name: str):  # Create a contextchain table
    """
    Create a contextchain table (chaining contextual lookup).
    """
    font.addLookup(name, "gsub_contextchain", None, (("ccmp", (("latn", "dflt"),)),))

def _create_contextchain_feature(
        font: fontforge.font, 
        feature_name: str, 
        backtrack_classes: List[Union[GLYPH, CLASS]], 
        input: Union[GLYPH, CLASS], 
        lookahead_classes: List[Union[GLYPH, CLASS]],
        lookup: LOOKUP,
    ): # Create an entry for a contextchain table
    """
    Adds a chaining contextual feature to the given FontForge font.

    Parameters:
    - font: FontForge font object.
    - feature_name: Name of the feature to add.
    - backtrack_classes: List of class names for the backtrack context.
    - input: glyph name or class name of the glyphs to be changed by the lookup.
    - lookahead_classes: List of class names for the lookahead context.
    - lookup_list: List of existing lookup names to apply.

    Example:
        _create_contextchain_feature(font,
            feature_name="contextualSubstitution",
            backtrack_classes=["@before1", "@before2"],
            input_classes="@input1",
            lookahead_classes=["@after1"],
            lookup="substitutionLookup")
    """
    # Construct class references
    backtrack_str = " ".join(backtrack_classes)
    lookahead_str = " ".join(lookahead_classes)
    
    # Build the FEA feature string
    fea = f"""
    lookup {feature_name} {{
        substitute [{backtrack_str}] [{input}] [{lookahead_str}] by {lookup};
    }} {feature_name};

    feature {feature_name} {{
        lookup {feature_name};
    }} {feature_name};
    """
    
    # Debug: Print the constructed FEA string
    print("Constructed FEA Feature String:")
    print(fea)
    
    try:
        font.mergeFeatureString(fea)
        print(f"Feature '{feature_name}' successfully added to the font.")
    except Exception as e:
        print(f"Error merging feature '{feature_name}': {e}")



class ClassIndex():
    """
    Manages glyph classes, create glyph classes dynamically when needed.
    """
    current_id = 0
    classes = {}

    def __init__(self, font: fontforge.font, index: GlyphIndex):
        self.font = font
        self.index = index

    def _create_class(self, glyphs: List[GLYPH]) -> CLASS:
        self.font.defineClass(str(self.current_id), glyphs)
        self.current_id += 1
        return str(self.current_id)

    def exists(self, glyphs: List[GLYPH]) -> bool:
        return any([glyphs == glyph_class for glyph_class in self.classes.values()])
    
    def get_class(self, glyphs: List[GLYPH]) -> CLASS:
        """
        Provide the class id for a given set of glyphs.
        """
        for class_id, glyph_class in self.classes.items():
            if glyphs == glyph_class: 
                print(f"FOUND EXISTING CLASS {glyphs}")
                return class_id

        return self._create_class(glyphs)


class SubstitutionTable():
    """
    Metadata for a substitution table.
    """
    replacements = {}  # {character: [replacements,]}

    def __init__(self, font: fontforge.font, index: GlyphIndex, name: str):
        self.font = font
        self.index = index
        self.name = name  # the name of the substitution table (both in fontforge and in the substitution manager system)
        _create_gsub_multiple(font, name)

    def exists(self, replacing: GLYPH) -> bool:
        """
        Whether a substitution for this character already exists in the table.
        """
        return replacing in self.replacements.keys()
    
    def get_replacement(self, replacing: str) -> List[str]:
        return self.replacements[replacing]

    def add_replacement(self, replacing: str, replacements: Union[GLYPH, List[str]]):
        if replacing not in self.replacements: self.replacements[replacing] = []  # Initialize list if did not exist
        if isinstance(replacements, str): replacements = [replacements]  # Convert to list
        for replacement in replacements:
            if replacement not in self.replacements:  # Only add replacement if it didnt exist already
                self.replacements[replacing].append(replacement)
                self.index[replacing].addPosSub(self.name, replacement)
    

class SubstitutionManager():
    """
    Create and append elements to substitution tables
    in order to minimize the number of different substitution tables automatically.
    """
    tables = {}
    def __init__(self, font: fontforge.font, index: GlyphIndex, classes: ClassIndex):
        self.font = font
        self.index = index

    def exists(self, table_name: str) -> bool:
        return table_name in self.tables.keys()
    
    def _create_substitution_table(self, table_name: str):
        """
        Create a new substitution table if it doesn't exist.
        """
        self.tables[table_name] = SubstitutionTable(self.font, self.index, table_name)

    def get_replacement(self, replacing: GLYPH, replacements: List[GLYPH]):
        """
        Return the id of the replacement table to do the required replacement.
        Create a new replacement on the first table with an empty slot available if it doesn't exist.
        Create a new substitution table if all of the existing ones already define replacements for the current glyph being replaced ("replacing")
        """
        # Checks if the substitution already exists in the table.
        for table in self.tables.values():
            if table.exists(replacing) and table.get_replacement(replacing) == replacements:
                raise Exception(f"The substitution table already exists {replacing}:{replacements} : Redundancy")
        
        # If the replacement exists in the index, find the first table 
        # which does not define a substitution for the character
        # and add it to it.
        for table_name, table in self.tables.values():
            if not table.exists(replacing):
                table.add_replacement(replacing, replacements)
                return table_name
        
        # If the substitution does not exist, create a new table and add it to the manager.
        name = "substitution." + replacing
        self._create_substitution_table(name)
        self.tables[name].add_replacement(replacing, replacements)
        return name


class ContextualLookup():
    """
    Handles regular substitution patterns.
    Those contextual patterns are by far the most common in Spetekkimyo font feature (~50% of the lookup loginc).
    (the next 3 most common are "chaining contextual positioning" (38%), "glyph composition" (10%) and then "ligature" (2%))
    """
    def __init__(self, font: fontforge.font, index: GlyphIndex, substitutions: SubstitutionManager, name: str):
        self.font = font
        self.index = index
        self.substitutions = substitutions
        self.name = name
        _create_contextchain(font, name)


    def CUSTOM(self, backtrack: List[GLYPH], input: List[GLYPH], lookahead: List[GLYPH], lookups: List[LOOKUP]):
        """
        Most general lookup creation pattern.
        """
        self.font.addContextualSubstitution(
            lookupName = self.name,
            subtableName = self.name,
            backtrackClasses = backtrack,
            inputClasses = input,
            lookaheadClasses = lookahead,
            lookups = [lookups]
        )


    def REPLACE(self, backtrack: List[GLYPH], replacing: GLYPH, lookahead: List[GLYPH], replacements: Union[GLYPH, SET, List[GLYPH]]):
        """
        Replace by the replacement string.
        """
        if isinstance(replacements, str): replacements = self.index.get_glyph_or_gset(replacements)  # Input can be gset name => List[GLYPH]

        lookup = self.substitutions.get_replacement(replacing, replacements)
        self.CUSTOM(backtrack, [replacing], lookahead, [lookup])
        

    def APPEND_LEFT(self,  backtrack: List[GLYPH], replacing: GLYPH, lookahead: List[GLYPH], left:  Union[GLYPH, SET, List[GLYPH]]):
        if isinstance(left, str): left = self.index.get_glyph_or_gset(left)  # Input can be gset name
        left.insert(0, replacing)  # Recalculating replacement
        self.REPLACE(backtrack, replacing, lookahead, left)


    def SKIP(self, backtrack: List[GLYPH], replacing: GLYPH, lookahead: List[GLYPH]):
        """
        Skips the update of the glyph in that particular context at this point in the lookup.
        """
        self.REPLACE(backtrack, replacing, lookahead, replacing)  # <=> Replacing the glyph by itself 
        # (because operations are limited to 1 per glyph per lookup, doing this disables any further operation)

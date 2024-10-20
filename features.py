"""
Create an interface on fontforge to create lookup tables easily.
"""
import fontforge
from index import GlyphIndex
from typing import Union, List, Dict
from abc import ABC, abstractmethod

GLYPH = str
SET = str
LOOKUP = str
CLASS = str


def install_feature(feature_string: str, feature_path: str, font: fontforge.font, debug=False):
    if debug: print(f"RESULT : \n{feature_string}")

    try:
        with open(feature_path, "w") as f: f.write(feature_string)
        font.mergeFeature(feature_path)
        print("Features successfully imported.")
    except Exception as e:
        print(f"An error occurred while importing features: {e}")


class Component(ABC):
    """
    A string component to be parsed into a feature string.
    """
    @abstractmethod
    def compile(self) -> str:
        ...
    def __str__(self) -> str:
        return self.compile()


class ClassIndex(Component):
    """
    Manages glyph classes, create glyph classes dynamically when needed.
    """
    def __init__(self, font: fontforge.font, index: GlyphIndex):
        self.font = font
        self.index = index
        self.current_id = 0
        self.classes: Dict = {}
    
    def _handle_presets(self, class_name: str) -> bool:
        """
        Glyph presets are some specific class names that can be used right away in instructions.
        They are only loaded as classes when used the first time.

        Aditionally, returns True if the class_name was a supported preset, False if it was not.

        Current presets are : 

        - @any : any existing glyph
        """
        if class_name == "@any":
            if not self.exists("@any"):
                self.create_class(self.index.glyphs.keys(), "@any")
        else:
            return False
        return True
    
    def _handle_settings(self, glyphs: List[GLYPH]) -> List[GLYPH]:
        """
        Modifies the glyph list according to the # elements that represent the class settings.

        Current behavior : 
        - "#none" is removed as it is intended to be treated outside of the class.
        - Any other class setting is unknown and triggers and error.
        """
        result = []
        for glyph in glyphs:
            if glyph == "#example":
                continue
            elif glyph[0] == "#":
                raise ValueError(f"Unknown class setting: {glyph} in {glyphs}. Also note that some settings like #none are not supposed end up here because they are managed at the Feature level.")
            else:  # is a regular glyph
                result.append(glyph)
                
        return result
    
    def complement(self, glyphs: List[GLYPH]) -> List[GLYPH]:
        """
        Computes the complement of the glyph set.
        """
        complement = []
        for glyph in self.index.glyphs.keys():
            if glyph not in glyphs:
                complement.append(glyph)
        return complement

    def create_class(self, glyphs: List[GLYPH], class_name: str = None) -> CLASS:
        if not class_name: class_name = f"@class{self.current_id}"
        elif class_name[0] != "@": class_name = "@" + class_name  # ensure the class name starts with a "@" character
        self.classes[class_name] = glyphs
        self.current_id += 1
        return class_name

    def exists(self, glyphs: Union[CLASS, List[GLYPH]]) -> bool:
        if isinstance(glyphs, str):
            class_name = glyphs
            return (class_name if class_name[0] == '@' else '@' + class_name) in self.classes.keys()  # Checks if the class exists
        else:
            return any([glyphs == glyph_class for glyph_class in self.classes.values()])  # Checks if the glyph list exists
        
    def complement_exists(self, glyphs: List[GLYPH]):
        """
        Checks if the glyph set's complement already exists as a class.
        """
        complement = self.complement(glyphs) 
        return any([complement == glyph_class for glyph_class in self.classes.values()])
    
    def get_class(self, glyphs: Union[CLASS, List[GLYPH]], new_class_name: str = None) -> CLASS:
        """
        Provide the class id for a given set of glyphs.
        If the class does not exist create a new one for the set of glyphs.

        - new_class_name: The name of the new class if it has to be created
        """
        if isinstance(glyphs, str): 
            class_name = glyphs if glyphs[0] == "@" else "@" + glyphs
            if (
                self.exists(class_name) or 
                self._handle_presets(class_name)
            ):
                return self.classes[class_name]
            else: 
                raise KeyError(f"Could not find class or preset : '{class_name}'")

        elif isinstance(glyphs, list):
            # Handles # characters
            glyphs = self._handle_settings(glyphs)

            # Attempt to find an existing class
            for class_name, class_content in self.classes.items():
                if glyphs == class_content: return class_name

            # Create a new class
            if new_class_name in self.classes.keys():  # Do not use the class_name to create the new class
                new_class_name = None
            return self.create_class(glyphs, new_class_name)
        
        else:
            raise TypeError("Input must be a glyph set or a class name")
    
    def compile(self) -> str:
        """
        Return the definition of all glyph classes.
        Example: 
            @trigger = [ o b ]; 
            @target = [ a e ];
        """
        compiled_string = ""
        for class_name, glyphs in self.classes.items():
            compiled_string += f"{class_name} = [ {' '.join(glyphs)} ];\n"
        return compiled_string


class Instruction(Component):
    """
    A lookup instruction.

    /!\ The base Instruction class do not define its own compile method : Only its child classes do.
    """
    @abstractmethod
    def validate(self, glyphs: GlyphIndex, classes: ClassIndex):
        ...
    @abstractmethod
    def compile(self) -> str:
        ...
    def format_one(self, item: Union[GLYPH, SET, CLASS, List[GLYPH]], glyphs: GlyphIndex, classes: ClassIndex) -> Union[CLASS, GLYPH]:
        """
        Converts gset names to classes, glyph lists to classes, does NOT convert single glyphs to classes as it is not needed.
        Also checks if a referenced class exists, corrects class names with missing @.
        This function determines what becomes a glyph class or not.
        """
        if isinstance(item, str):
            if item[0] == "@":
                return item
            elif classes.exists(item):  # item is a class without a @
                return "@" + item
            elif glyphs.gset_exists(item):  # item is a set name
                set_name = item
                return classes.get_class(glyphs.gset(set_name), set_name)  # create glyph
            elif glyphs.glyph_exists(item):  # is a glyph name
                return item  # a single glyphs do not need a class alias 
            else:
                raise ValueError(f"{item} is neither a class nor a set name nor a glyph. It cannot be used in this instruction.")
        elif isinstance(item, list):
            if any([not glyphs.glyph_exists(i) for i in item]): 
                raise ValueError(f"An instruction received {item} as a list of glyphs for a class definition. One of those glyphs does not exist. Check for accidental @ or gset names in that glyph list.")
            else:
                if len(item) == 1:  # glyph list contains 1 single glyph => 
                    return item[0]  # single glyphs do not need a class alias
                return classes.get_class(item)
        else:
            raise ValueError(f"Expected a string (glyph, gset, class name) or a list of strings (glyph names) for item. Instead got {type(item)}")


class Lookup(Component):
    instruction_type = None  # type of the instructions that the Lookup accepts

    def __init__(self, name: str, font: fontforge.font, glyphs: GlyphIndex, classes: ClassIndex):
        self.font = font
        self.glyphs = glyphs
        self.classes = classes
        self.name: str = name  # the name of the substitution table (both in fontforge and in the substitution manager system)
        self.instructions: List[Instruction] = []

    @abstractmethod
    def is_conflicting(self, instruction: Instruction):
        ...

    def add_instruction(self, instruction: Instruction, force=False):

        if not isinstance(instruction, self.instruction_type):
            raise ValueError(f"Tried to add [{instruction.__class__.__name__}] but the lookup table only accepts {self.instruction_type.__name__} instructions.")

        if self.is_conflicting(instruction):
            if force:
                print(f"Warning : Added [{instruction}] with force=True but it is conflicting with {self.is_conflicting(instruction, True)} in the lookup table.")
            else:
                raise ValueError(f"Tried to add [{instruction}] but it is conflicting with {self.is_conflicting(instruction, True)} in the lookup table. This error should not happen with auto-generated lookups.")
        self.instructions.append(instruction)

    def compile(self) -> str:
        """
        Create the lookup instruction list.
        Example: 
            lookup ccmp_lookup {
                sub @trigger @trigger @target' @trigger by p;
                sub @trigger @target' @trigger by i;
            } ccmp_lookup;
        """
        compiled_string = f"\tlookup {self.name}" + " {\n"
        for instruction in self.instructions:
            compiled_string += "\t\t" + instruction.compile() + "\n"
        compiled_string += "\t} " + self.name + ";"  # close the lookup block and the substitution table block
        return compiled_string


class SubInstruction(Instruction):
    def __init__(self, 
                backtrack: List[Union[GLYPH, SET, CLASS, List[GLYPH]]] = [], 
                replacing: Union[GLYPH, SET, CLASS, List[GLYPH]] = "",
                lookahead: List[Union[GLYPH, SET, CLASS, List[GLYPH]]] = [],
                replacement: Union[GLYPH, SET, List[GLYPH]] = "",
                ):
        self.backtrack: List[Union[CLASS, GLYPH]] = backtrack
        self.replacing: Union[CLASS, GLYPH] = replacing
        self.lookahead: List[Union[CLASS, GLYPH]] = lookahead
        self.replacement: List[GLYPH] = replacement

    def validate(self, glyphs: GlyphIndex, classes: ClassIndex):
        """
        Interpret set names, glyph names, lists of glyphs and class names with missing @ properly.
        Create glyph classes whenever it is needed.
        """
        self.backtrack = [self.format_one(item, glyphs, classes) for item in self.backtrack]
        self.replacing = self.format_one(self.replacing, glyphs, classes)
        self.lookahead = [self.format_one(item, glyphs, classes) for item in self.lookahead]
        
        if isinstance(self.replacement, str):
            if self.replacement[0] == "@":
                raise ValueError(f"The replacement glyph has a value of {self.replacement} which looks like a class name. This is likely an error. Only glyph lists can be used as replacements.")
            elif glyphs.gset_exists(self.replacement):
                self.replacement = glyphs.gset(self.replacement)  # Loads the gset as a list of glyphs
            elif not glyphs.glyph_exists(self.replacement):  # Is neither a gset nor a glyph
                raise ValueError(f"Replacement value '{self.replacement}' is neither a glyph nor a gset. It cannot be used in this instruction.")
        elif any([not glyphs.glyph_exists(i) for i in self.replacement]): 
            raise ValueError(f"An instruction received {self.replacement} as a glyph list for a replacement glyph. Replacement glyphs in that list cannot be gsets names nor classes (unlike backtracks and lookaheads). Check for accidental @ or gset names in that glyph list.")

    def compile(self):
        """
        Return the line corresponding to one single instruction.
        Example: 
            sub @trigger @trigger @target' @trigger by p;
        """
        compiled_string = f"sub {' '.join(self.backtrack) + ' ' if self.backtrack else ''}{self.replacing}'{' ' + ' '.join(self.lookahead) if self.lookahead else ''} by {' '.join(self.replacement)};"
        return compiled_string


class SubLookup(Lookup):
    """
    Metadata for a substitution table.
    """
    instruction_type = SubInstruction

    def is_conflicting(self, instruction: SubInstruction, return_conflicts: bool = False) -> bool:
        """
        Whether this instruction is conflicting with any instruction in this lookup.

        An instruction is conflicting if it has : 
        - A replacement glyph that appear in the backtrack of another instruction. (or in the lookahead if the lookup is reversed)
        - A backtrack glyph that appear in the replacement of an existing instruction (or lookahead respectively).
        - The same replacing as an existing instruction.
        """
        conflicts = []
        for existing_instruction in self.instructions:

            for x in instruction.backtrack:
                if x in existing_instruction.replacement:
                    conflicts.append(existing_instruction)
            for x in instruction.replacement:
                if x in existing_instruction.backtrack:
                    conflicts.append(existing_instruction)
            for x in existing_instruction.replacing:
                if x == instruction.replacing:
                    conflicts.append(existing_instruction)

        if return_conflicts:
            return [str(conflict) for conflict in conflicts]
        return len(conflicts) > 0



class Feature(Component):
    """
    Generate a feature item for the font.
    Provide lookup instruction settings.
    """
    @staticmethod
    def _filter_out(inp: list, key: str) -> list:
        result = []
        for item in inp: 
            if item != key:
                result.append(item)
        return result

    def __init__(self, name: str, font: fontforge.font, glyphs: GlyphIndex, classes: ClassIndex):
        self.name: str = name
        self.font: fontforge.font = font
        self.glyphs: GlyphIndex = glyphs
        self.classes: ClassIndex = classes
        self.counter: int = 0
        self.lookups: List[Lookup] = []

    def compile(self):
        """
        Create the feature definition in the font.
        Example:
            feature ccmp {
                script DFLT;
                language dflt;
                script latn;
                language dflt;

                lookup ccmp_lookup {
                    sub @trigger @trigger @target' @trigger by p;
                } ccmp_lookup;
            } ccmp;
        """
        compiled_string = f"feature {self.name}" + " {\n"
        compiled_string += f"\tscript DFLT;\n\tlanguage dflt;\n\tscript latn;\n\tlanguage dflt;\n\n"  # Add language string
        for lookup in self.lookups:
            compiled_string += lookup.compile() + "\n\n"
        compiled_string += "} " + f"{self.name};\n"  # close the feature block
        return compiled_string

    def _extend_or_create_lookup(self, instruction: Instruction) -> Lookup:
        """
        Find a lookup that is compatible with the given instruction
        or create a new one if none is found.

        The Lookup that was updated is returned.
        """
        instruction.validate(self.glyphs, self.classes)  # Validate the instruction, this function raises the appropriate Exceptions if needed.

        for lookup in self.lookups:
            if isinstance(instruction, lookup.instruction_type):
                if not lookup.is_conflicting(instruction):
                    lookup.add_instruction(instruction)
                    return lookup
            
        # Create a new lookup
        self.counter += 1

        match type(instruction).__name__:
            case "SubInstruction":
                new_name = self.name + "_" + SubLookup.__name__.lower() + "_" + str(self.counter)

                lookup = SubLookup(new_name, self.font, self.glyphs, self.classes)
                lookup.add_instruction(instruction)
                self.lookups.append(lookup)
                return lookup
            case _:
                raise ValueError(f"Feature {self.name} can not contain {type(instruction).__name__} instructions.")


    # Main Instruction parsing methods        

    def SUBSTITUTION(self, backtrack: Union[List, SubInstruction], replacing: Union[List, str] = None, lookahead: List = None, replacement: Union[List, str] = None) -> Lookup:
        """
        The default substitution implementation.

        Handles the following setting keywords :
            - #start : handles the case where a lookup can be triggered by "starting" the sentence.
        """
        # Convert to an Instruction object for uniform treatment
        if isinstance(backtrack, SubInstruction):
            instruction = backtrack
        elif isinstance(backtrack, list):
            instruction = SubInstruction(backtrack=backtrack, replacing=replacing, lookahead=lookahead, replacement=replacement)

        # Convert backtrack to list for uniform treatment
        if len(instruction.backtrack) > 0 and isinstance(instruction.backtrack[0], str) and instruction.backtrack[0] == '#start':
            instruction.backtrack[0] = [instruction.backtrack[0]]

        # Add the instructions for the #start case
        if len(instruction.backtrack) > 0  and '#start' in instruction.backtrack[0]:
            instruction.backtrack[0] = Feature._filter_out(instruction.backtrack[0], '#start')

            if len(instruction.backtrack) > 0:
                self.SUBSTITUTION(instruction.backtrack, instruction.replacing, instruction.lookahead, instruction.replacement)  # Manages the regular cases if there are any
                complement = self.classes.complement(instruction.backtrack[0])
            else:
                complement = ["@all"]
            skip_backtrack = instruction.backtrack.copy() 
            skip_backtrack[0] = complement
            
            skip_lookup = self.SKIP(skip_backtrack, instruction.replacing, instruction.lookahead)  # Skips any letter that does not fit the pattern (= complement of the 1st statement of the backtrack)
            substitution = SubInstruction(
                backtrack = instruction.backtrack[1:] if len(instruction.backtrack) >= 2 else [], 
                replacing = instruction.replacing,
                lookahead = instruction.lookahead,
                replacement = instruction.replacement  # The replacement remains the same as the original instruction, but the first backtrack statement is ignored (because the complement options have been skipped already)
            )
            substitution.validate(self.glyphs, self.classes)
            skip_lookup.add_instruction(substitution, force=True)
        # Otherwise process as usual
        else:
            return self._extend_or_create_lookup(instruction)


    # Action methods

    def REPLACE(self, replacing: GLYPH, replacement: Union[List[GLYPH], GLYPH]) -> Lookup:
        return self.SUBSTITUTION([], replacing, [], replacement)

    def APPEND_LEFT(self,  backtrack: List[GLYPH], replacing: GLYPH, lookahead: List[GLYPH], left:  Union[GLYPH, SET, List[GLYPH]]) -> Lookup:
        replacing = self.glyphs.get_glyph_or_gset(replacing)  # Preloading replacement glyphs
        if isinstance(left, str): left = self.glyphs.get_glyph_or_gset(left)  # Input can be gset name

        for glyph in replacing:
            replacement = left.copy()
            replacement.append(glyph)  # Recalculating replacement
            self.SUBSTITUTION(backtrack, glyph, lookahead, replacement)

    def SKIP(self, backtrack: List[GLYPH], replacing: GLYPH, lookahead: List[GLYPH]) -> Lookup:
        """
        Skips the update of the glyph in that particular context at this point in the lookup.
        """
        return self.SUBSTITUTION(backtrack, replacing, lookahead, replacing)  # <=> Replacing the glyph by itself 
        # (because operations are limited to 1 per glyph per lookup, doing this disables any further operation)

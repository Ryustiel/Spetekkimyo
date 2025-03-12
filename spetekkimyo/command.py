"""
Provide a command line interface (and a function) for generating the spetekmyo font
based the provided feature file and glyphs. (resources fetched internally for now)
"""

import os
import sys
import subprocess
from pathlib import Path

root_dir = Path(__file__).parent.resolve()
ffpython_exe = root_dir / 'ffpython' / 'bin' / 'ffpython.exe'
path_to_generate_script = root_dir / 'generate.py'

def generate_font(output_path: str):
    """
    Run generate.py using the ffpython library, 

    Parameters:
        output_path (str): The location of the file to write the font to. (such as "output/font.otf")

    NOTE : generate.py must be run in fontforge's custom python environment.
    """
    if output_path[0] in ("/", "\\"): raise ValueError("Path must not have / or \\ at position 0.")
    subprocess.run(
        [str(ffpython_exe), str(path_to_generate_script), str(root_dir / output_path)],
        cwd=str(root_dir),  # ensure the working directory is set to the root
        check=True,         # will raise CalledProcessError if the command fails
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    print(f"Font successfully generated at {str(root_dir.joinpath(output_path))}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python file.py <output_path>")
        sys.exit(1)

    output_path = sys.argv[1]

    try:
        generate_font(output_path)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

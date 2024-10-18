"""
Renamed exported glyphs and store them in subfolders based on the "." naming convention (of my own).
"""
import os

def list_files_in_directory(directory_path):
    for dirpath, dirnames, filenames in os.walk(directory_path):
        # Print the current directory path
        print(f'Current Directory: {dirpath}')
        # Print each file in the directory
        for filename in filenames:
            print(f'File: {filename}')

import os
import shutil

def organize_files(directory_path):
    # Iterate over all files in the directory
    for dirpath, _, filenames in os.walk(directory_path):
        for filename in filenames:
            # Skip files that are already moved
            if '.' not in filename:
                continue

            # Separate the base name and extension
            basename, extension = os.path.splitext(filename)

            # Split the basename by '.' to find subdirectory names
            subdirs = basename.split('.')

            if len(subdirs) > 1:
                # Create a new path using subdirectories
                new_dir_path = os.path.join(dirpath, *subdirs[:-1])

                # Ensure the new directory structure exists
                os.makedirs(new_dir_path, exist_ok=True)

                # Define the source file path
                source_file = os.path.join(dirpath, filename)

                # Define the destination file path
                destination_file = os.path.join(new_dir_path, subdirs[-1] + extension)

                # Move the file
                shutil.move(source_file, destination_file)
                print(f'Moved: {source_file} to {destination_file}')

# Replace 'glyphs' with the path to your directory
organize_files('glyphs')

# Replace 'your_directory_path' with the path to the folder you want to traverse
list_files_in_directory('glyphs')
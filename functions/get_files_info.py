# functions/get_files_info.py

'''
Return example:

- README.md: file_size=1032 bytes, is_dir=False
- src: file_size=128 bytes, is_dir=True
- package.json: file_size=1234 bytes, is_dir=False
'''

import os

from google.genai import types

schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)

def get_files_info(working_directory, directory=".") -> str:

    target_dir = os.path.join(working_directory, directory)
    abs_working_dir = os.path.abspath(working_directory)
    abs_target_dir = os.path.abspath(target_dir)

    # Check if the given directory is a sub-path of working_directory
    if not abs_target_dir.startswith(abs_working_dir):
        return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'

    # Check if the given directory is real
    if not os.path.isdir(abs_target_dir):
        return f'Error: "{directory}" is not a directory'

    if directory == ".":
        files_info = f"Result for current directory:\n"
    else:
        files_info = f"Result for '{directory}' directory:\n"

    path_contents = os.listdir(abs_target_dir)

    try:
        for thing in path_contents:
            file_size = os.path.getsize(abs_target_dir + "/" + thing)
            is_dir = os.path.isdir(abs_target_dir + "/" + thing)
            files_info += f"  - {thing}: file_size={file_size} bytes, is_dir={is_dir}\n"
    except Exception as e:
        return f"    Error: {e}"

    return files_info

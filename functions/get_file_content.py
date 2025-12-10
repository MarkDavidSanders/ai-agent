# functions/get_file_content.py

'''
target_dir = os.path.join(working_directory, directory)
abs_working_dir = os.path.abspath(working_directory)
abs_target_dir = os.path.abspath(target_dir)

# Check if the given directory is a sub-path of working_directory
if not abs_target_dir.startswith(abs_working_dir):
    return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'

# Check if the given directory is real
if not os.path.isdir(abs_target_dir):
    return f'Error: "{directory}" is not a directory'
'''

MAX_CHARS = 10000

import os

from google.genai import types

schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Prints contents of the specified file, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file path to read from, relative to the working directory.",
            ),
        },
    ),
)

def get_file_content(working_directory, file_path) -> str:

    target_file = os.path.join(working_directory, file_path)
    abs_working_dir = os.path.abspath(working_directory)
    abs_target_file = os.path.abspath(target_file)

    # Check if file_path is inside working_directory
    if not abs_target_file.startswith(abs_working_dir):
        return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'

    # Check if the given file_path leads to a real file
    if not os.path.isfile(abs_target_file):
        return f'Error: File not found or is not a regular file: "{file_path}"'

    try:
        with open(abs_target_file, "r", encoding="utf-8") as f:
            content = f.read(MAX_CHARS + 1)
            if len(content) > MAX_CHARS:
                content = content[:-1] + f'[...File "{file_path}" truncated at {MAX_CHARS} characters]'
            return content
    except Exception as e:
        return f"Error: {e}"

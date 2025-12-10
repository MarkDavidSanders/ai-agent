# functions/write_file.py

import os

from google.genai import types

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Writes the provided content to the specified file path, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file path to write to, relative to the working directory. File path is created if it doesn't exist.",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The content to write to the file path."
            ),
        },
    ),
)

def write_file(working_directory, file_path, content):

    target_file = os.path.join(working_directory, file_path)
    abs_working_dir = os.path.abspath(working_directory)
    abs_target_file = os.path.abspath(target_file)

    # Check if file_path is inside working_directory
    if not abs_target_file.startswith(abs_working_dir):
        return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'

    # Check if file_path exists and create it if not
    if not os.path.exists(os.path.dirname(abs_target_file)):
        try:
            os.makedirs(os.path.dirname(abs_target_file))
        except Exception as e:
            return f'Error: {e}'

    try:
        with open(abs_target_file, 'w', encoding='utf-8') as f:
            f.write(content)
            return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
    except Exception as e:
        print(f'Error: {e}')

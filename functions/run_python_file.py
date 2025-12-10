# functions/run_python_file.py

import os
import subprocess

from google.genai import types

schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Runs the provided Python file, constrained to the working directory. Dangerous!",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The Python file to run. File path must be relative to the working directory.",
            ),
            "args": types.Schema(
                type=types.Type.STRING,
                description="Arguments to pass to the Python script, if needed."
            ),
        },
    ),
)

def run_python_file(working_directory, file_path, args=[]):

    target_file = os.path.join(working_directory, file_path)
    abs_working_dir = os.path.abspath(working_directory)
    abs_target_file = os.path.abspath(target_file)

    # Check if file_path is inside working_directory
    if not abs_target_file.startswith(abs_working_dir):
        return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

    # Check if the given file_path leads to a real file
    if not os.path.exists(abs_target_file):
        return f'Error: File "{file_path}" not found.'

    # Check if file_path has a Python extension
    if not file_path.endswith(".py"):
        return f'Error: "{file_path}" is not a Python file.'

    try:
        arg_list = ["python3", abs_target_file] + args
        completed_process = subprocess.run(arg_list, timeout=30, capture_output=True)
        if completed_process == "":
            return "No output produced"
        return_string = f"STDOUT: {completed_process.stdout}\nSTDERR: {completed_process.stderr}"
        if completed_process.returncode != 0:
            return_string += f"\nProcess exited with code {completed_process.returncode}"
        return return_string
    except Exception as e:
        return f"Error: executing Python file: {e}"

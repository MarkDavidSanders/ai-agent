#!/usr/bin/env python3
# main.py

'''
The program we're building is a CLI tool that:

Accepts a coding task (e.g., "strings aren't splitting in my app")
Chooses from a set of predefined functions to work on the task, for example:
Scan the files in a directory
Read a file's contents
Overwrite a file's contents
Execute the Python interpreter on a file
Repeats step 2 until the task is complete (or it fails miserably, which is possible)

So that's nice!
'''

import argparse
# argparse lets us create a parser object, define the arguments we want to accept,
# then parse user-provided arguments

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from prompts import system_prompt
from functions.get_files_info import schema_get_files_info, get_files_info
from functions.get_file_content import schema_get_file_content, get_file_content
from functions.run_python_file import schema_run_python_file, run_python_file
from functions.write_file import schema_write_file, write_file

FUNCTION_NAMES = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "run_python_file": run_python_file,
    "write_file": write_file
}

# the function that calls functions: funcception
def call_function(function_call_part, verbose=False):
    '''
    function_call_part is a types.FunctionCall object
    function_call_part.name -> str
    function_call_part.args -> dict
    '''
    if verbose:
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    else:
        print(f" - Calling function: {function_call_part.name}")

    # working_directory is not managed by LLM so we need to manually add it
    function_call_part.args["working_directory"] = "./calculator"

    # call function and capture result
    try:
        function_name = FUNCTION_NAMES[function_call_part.name]
        function_args = function_call_part.args
        function_result = function_name(**function_args)

        # return types.Content object with function result
        # return.part.response is a dict with a "result" key
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_call_part.name,
                    response={"result": function_result},
                )
            ]
        )

    # invalid function name
    except KeyError:
        return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_call_part.name,
                response={"error": f"Unknown function: {function_call_part.name}"},
                )
            ],
        )

# create parser args object with two properties:
# args.user_prompt - whatever prompt the user provides
# args.verbose - set by "--verbose" flag ("store_true": args.verbose = True if set)
parser = argparse.ArgumentParser(description="Chatbot")
parser.add_argument("user_prompt", type=str, help="User prompt")
parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
args = parser.parse_args()

# create types.Tool list of all available functions
available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_write_file,
        schema_run_python_file
    ]
)

# Load .env file
load_dotenv()

# Get API key from .env file
api_key = os.environ.get("GEMINI_API_KEY")
if api_key is None:
    raise RuntimeError("GEMINI_API_KEY not found in environment variables.")

# Use API key to create new instance of Gemini client
client = genai.Client(api_key=api_key)

# create a list of messages containing only the user prompt (for now)
# Content types have two parameters: role and parts
# individual parts have their own type
messages = [types.Content(role="user", parts=[types.Part(text=args.user_prompt)])]

# set up a loop to interact with Gemini
for i in range(20):
    try:
        # use generate_content to send prompt(s) and capture response
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=types.GenerateContentConfig(
                tools=[available_functions], system_instruction=system_prompt
                ),
            )

        # If no candidate contains a function call and response.text is not empty, loop is finished
        if not response.function_calls and response.text:
            print(response.text)
            break

        # check response.candidates, a list of response variations (usually just one)
        # add candidates to messages list to create context for future calls
        if response.candidates:
            for candidate in response.candidates:
                messages.append(candidate.content)

        # Monitor token consumption. Tokens are limited!
        if response.usage_metadata:
            if args.verbose:
                print(f"User prompt: {args.user_prompt}")
                print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
                print(f"Response tokens: {response.usage_metadata.candidates_token_count}")
        else:
            raise RuntimeError("No usage metadata found. API request probably failed.")

        # Check the generate_content response for any function calls
        if response.function_calls:
            call_responses = []
            for call in response.function_calls:
                call_response = call_function(call, args.verbose)
                if not call_response.parts[0].function_response.response:
                    raise RuntimeError("Something went wrong with the function call")
                call_responses.append(call_response.parts[0])
                if args.verbose:
                    print(f"-> {call_response.parts[0].function_response.response}")

            # add function call responses to messages for context
            messages.append(
                types.Content(role="user", parts=call_responses)
            )

        else:
            print(response.text)

    except Exception as e:
        raise RuntimeError(f"    Error: {e}") from e

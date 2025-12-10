#!/usr/bin/env python3

import os
import argparse

from google import genai
from google.genai import types
from dotenv import load_dotenv

from prompts import system_prompt
from functions.get_files_info import *
from functions.get_file_content import *
from functions.run_python_file import *
from functions.write_file import *

FUNCTION_NAMES = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "run_python_file": run_python_file,
    "write_file": write_file
}

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if api_key is None:
    raise RuntimeError("Gemini API key not found!!!!!!!!!!!!!")

client = genai.Client(api_key=api_key)

available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_write_file,
        schema_run_python_file
        ]
)

def call_function(function_call_part, verbose=False):
    '''function_call_part is a types.FunctionCall object
    function_call_part.name -> str
    function_call_part.args -> dict
    '''
    if verbose:
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    else:
        print(f" - Calling function: {function_call_part.name}")

    function_call_part.args["working_directory"] = "./calculator"

    # run function
    try:
        function_name = FUNCTION_NAMES[function_call_part.name]
        function_args = function_call_part.args
        function_result = function_name(**function_args)
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_call_part.name,
                    response={"result": function_result},
                )
            ]
        )

    # if function name is invalid:
    except NameError:
        return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_call_part.name,
                response={"error": f"Unknown function: {function_call_part.name}"},
                )
            ],
        )

def main():
    parser = argparse.ArgumentParser(description="Agent")
    parser.add_argument("prompt", type=str, help="User prompt")
    # Now we can access 'args.prompt'
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    # Now we have a flag for verbosity

    args = parser.parse_args()

    messages = [types.Content(role="user", parts=[types.Part(text=args.prompt)])]

    for i in range(20):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=messages,
                config=types.GenerateContentConfig(
                    tools=[available_functions], system_instruction=system_prompt
                    )
            )

            # the model is finished if no candidates remain and response.text has text
            if response.candidates is None and response.text != "":
                print(f"Final response:\n{response.text}")
                break

            # check response.candidates and add contents to messages
            if response.candidates:
                for candidate in response.candidates:
                    function_call_content = candidate.content
                    messages.append(function_call_content)

            if response.usage_metadata is None:
                raise RuntimeError("Usage metadata not found. API request probably didn't work!!!!")

            if args.verbose:
                print(f"User prompt: {args.prompt}")
                print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
                print(f"Response tokens: {response.usage_metadata.candidates_token_count}")

        except Exception as e:
            raise RuntimeError(f"    Error: {e}") from e

    if response.function_calls is not None:
        for call in response.function_calls:
            call_responses = []
            call_response = call_function(call, args.verbose)
            if not call_response.parts[0].function_response.response:
                raise RuntimeError("Something went wrong with the function call. Sad shit")
            call_responses.append(call_response.parts[0].function_response.response)
            if args.verbose:
                print(f"-> {call_response.parts[0].function_response.response}")

        # this might be wrong:
        call_response_content = types.Content(role="user",parts=[types.Part(text=call_responses)])
        messages.append(call_response_content)
    else:
        print(response.text)


if __name__ == "__main__":
    main()

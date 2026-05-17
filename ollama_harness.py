import argparse
import json
import ollama
import subprocess
import sys

from pathlib import Path
from typing import Optional

import tool_funcs
from tools import TOOLS

# ---------------------------------------------------------------------------
# Model resolution
# ---------------------------------------------------------------------------

def resolve_model(cli_model: Optional[str], config_path: str = "config.json") -> Optional[str]:
    """Return the model to use, checking CLI arg → config file → auto-detect."""

    # 1. Explicit CLI takes priority
    if cli_model:
        return cli_model

    # 2. Config file
    if Path(config_path).exists():
        with open(config_path) as f:
            config = json.load(f)
        if "model" in config:
            return config["model"]

    # 3. Auto-detect: ask Ollama what's installed
    response = ollama.list()
    models = response.models  # list of ModelDetails objects
    if not models:
        print("No models found. Pulling llama3: `ollama pull llama3`.")
        try:
            subprocess.run(["ollama", "pull", "llama3"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to pull model: {e}")
            print("Please pull a model and try again.")
            sys.exit(1)
            
        return "llama3"

    detected = models[0].model
    print(f"No model specified — using first available: {detected}")
    return detected


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def execute_tool(tool_name: str, tool_args: dict) -> str:
    """Given a tool name and arguments, execute the tool and return the result as a string."""
    for tool in TOOLS:
        if tool.function.name == tool_name:
            try:
                getattr(tool_funcs, tool_name)(**tool_args)
            except Exception as e:
                return f"Error executing tool '{tool_name}': {str(e)}"
            
    return f"Error: unknown tool '{tool_name}'"


# ---------------------------------------------------------------------------
# Plain chat loop
# ---------------------------------------------------------------------------

def run_agent_turn(model: str, messages: list) -> str:
    """
    Run one agent turn: send messages to the model and handle tool calls.
    Returns the model's final text response for this turn.

    This is the core agent loop. The model can call tools zero or more times
    before it gives a final answer — we keep looping until it stops.

    PSEUDOCODE:

    WHILE True:

        response = ollama.chat(model, messages, tools=TOOLS)
                                              # ^ pass tools so model knows they exist

        IF response.message.tool_calls is not empty:

            FOR EACH tool_call IN response.message.tool_calls:
                name   = tool_call.function.name
                args   = tool_call.function.arguments      # dict the model filled in
                result = execute_tool(name, args)
                print(f"[tool] {name}({args}) -> {result}")

                # Append the tool result to history so the model can read it
                messages.append({"role": "tool", "content": result})

            # Loop again — model will see the results and decide what to do next

        ELSE:
            # No tool calls — model gave its final answer
            RETURN response.message.content
    """
    pass


def run_chat_loop(model: str) -> None:
    """Interactive chat loop that maintains full message history each turn."""

    system_prompt = "You are a helpful assistant. Use tools when they are helpful."
    messages = [{"role": "system", "content": system_prompt}]

    print(f"\nChat started with model: {model}")
    print("Type 'exit' or press Ctrl-C to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye.")
            break

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        # TODO: replace the streaming block below with a call to run_agent_turn()
        #       once you've implemented it. For now the plain streaming loop still works.

        print("Assistant: ", end="", flush=True)
        full_response = ""

        for chunk in ollama.chat(model=model, messages=messages, stream=True):
            token = chunk["message"]["content"]
            print(token, end="", flush=True)
            full_response += token

        print()

        messages.append({"role": "assistant", "content": full_response})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple Ollama agent harness")
    parser.add_argument("--model", default=None, help="Ollama model name to use")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    args = parser.parse_args()

    model = resolve_model(args.model, args.config)
    if model is None:
        print("No model specified - available models:")
        for m in ollama.list().models:
            print(f"  - {m.model}")
        usr_input =input("Select a model or press q to exit: ")
        if usr_input.lower() in ("q", "quit", "exit"):
            print("Goodbye.")
            sys.exit(0)
        else:
            model = usr_input.strip()
            
    run_chat_loop(model)

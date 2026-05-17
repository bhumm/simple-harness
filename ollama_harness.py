import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import ollama


# ---------------------------------------------------------------------------
# Model resolution
# ---------------------------------------------------------------------------

def resolve_model(cli_model: Optional[str], config_path: str = "config.json") -> Optional[str]:
    """Return the model to use, checking CLI arg → config file → auto-detect."""

    # 1. Explicit CLI argument wins
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
        print("No models found. Run `ollama pull <model>` first.")
        sys.exit(1)

    detected = models[0].model
    print(f"No model specified — using first available: {detected}")
    return detected


# ---------------------------------------------------------------------------
# Plain chat loop (Step 1 — no tools yet)
# ---------------------------------------------------------------------------

def run_chat_loop(model: str) -> None:
    """Interactive chat loop that maintains full message history each turn."""

    system_prompt = "You are a helpful assistant."
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

        # Add the user's message to history
        messages.append({"role": "user", "content": user_input})

        # Stream the response so tokens appear as they arrive
        print("Assistant: ", end="", flush=True)
        full_response = ""

        for chunk in ollama.chat(model=model, messages=messages, stream=True):
            token = chunk["message"]["content"]
            print(token, end="", flush=True)
            full_response += token

        print()  # newline after the streamed response

        # Add the assistant's full reply to history so future turns have context
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

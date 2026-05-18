import argparse
import json
import ollama
import re
import subprocess
import sys

from pathlib import Path
from typing import Optional

import tool_funcs
from tools import TOOLS


# ---------------------------------------------------------------------------
# AGENT.md — always-on context
# ---------------------------------------------------------------------------

def load_agent_md(path: str = "AGENT.md") -> Optional[str]:
    """Return the contents of AGENT.md if it exists in the working directory."""
    p = Path(path)
    if p.exists():
        content = p.read_text().strip()
        print(f"[agent] Loaded {path}")
        return content
    return None


# ---------------------------------------------------------------------------
# SKILLS.md — prompt-triggered context
# ---------------------------------------------------------------------------

def load_skills_md(path: str = "SKILLS.md") -> list[dict]:
    """Parse SKILLS.md into a list of {name, triggers, content} dicts.

    Expected format:
        ## Skill Name
        triggers: keyword1, keyword2, keyword3

        Skill body text...
    """
    p = Path(path)
    if not p.exists():
        return []

    skills = []
    current = None

    for line in p.read_text().splitlines():
        heading = re.match(r"^##\s+(.+)", line)
        if heading:
            if current:
                current["content"] = current["content"].strip()
                skills.append(current)
            current = {"name": heading.group(1).strip(), "triggers": [], "content": ""}
            continue

        if current is None:
            continue

        trigger_line = re.match(r"^triggers:\s*(.+)", line, re.IGNORECASE)
        if trigger_line:
            current["triggers"] = [t.strip().lower() for t in trigger_line.group(1).split(",")]
        else:
            current["content"] += line + "\n"

    if current:
        current["content"] = current["content"].strip()
        skills.append(current)

    if skills:
        print(f"[agent] Loaded {len(skills)} skill(s) from {path}")
    return skills


def get_relevant_skills(user_prompt: str, skills: list[dict]) -> list[dict]:
    """Return skills whose trigger words appear in the user prompt."""
    words = set(re.findall(r"\w+", user_prompt.lower()))
    return [s for s in skills if any(t in words for t in s["triggers"])]

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
            # Pull a model for you
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
    func = getattr(tool_funcs, tool_name, None)
    if func is None:
        return f"Error: unknown tool '{tool_name}'"
    
    try:
        result = func(**tool_args)
        return str(result)
    
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}"


# ---------------------------------------------------------------------------
# Plain chat loop
# ---------------------------------------------------------------------------

def run_agent_turn(model: str, messages: list) -> str:
    """Run a single turn of the agent loop: send messages to the model, execute any tool calls, and return the final response if there are no tool calls."""
    while True:
        response = ollama.chat(model, messages, tools=TOOLS)

        if response.message.tool_calls is not None:
            
            for tool_call in response.message.tool_calls:
                name   = tool_call.function.name
                args   = tool_call.function.arguments
                result = execute_tool(name, args)
                print(f"[tool] {name}({args}) -> {result}")

                # Append the tool result to history so the model can read it
                messages.append({"role": "tool", "content": result})

            if response.message.content is not None:
                return response.message.content

        else:
            return response.message.content

def run_chat_loop(model: str) -> None:
    """Interactive chat loop that maintains full message history each turn."""
    system_prompt = "You are a helpful assistant. Use tools when they are helpful."

    agent_context = load_agent_md()
    if agent_context:
        system_prompt += f"\n\n---\n{agent_context}"

    skills = load_skills_md()
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

        # Inject any relevant skill context as a system message before the user turn
        matched = get_relevant_skills(user_input, skills)
        for skill in matched:
            print(f"[agent] Injecting skill: {skill['name']}")
            messages.append({"role": "system", "content": f"[Skill: {skill['name']}]\n{skill['content']}"})

        messages.append({"role": "user", "content": user_input})

        full_response = run_agent_turn(model, messages)
        print(f"Assistant: {full_response}")

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

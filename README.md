# simple-harness

A bare-bones Ollama agent harness I built to learn how agents actually work under the hood.

## What it does

- Starts a chat loop with a local Ollama model
- Keeps message history so the model remembers the conversation
- Streams tokens as they come in
- Figures out which model to use without you having to hard-code it

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ollama
```

You also need [Ollama](https://ollama.com). If you don't have at least one model installed, it pulls llama3 on your behalf:

```bash
ollama pull llama3.1
```

## Usage

```bash
# auto-detect whatever model you have installed
python ollama_harness.py

# specify a model
python ollama_harness.py --model llama3.1

# use a config file
echo '{"model": "llama3.1"}' > config.json
python ollama_harness.py
```

# Agent Instructions

You are running inside a local Ollama harness. You have access to filesystem tools
(ls, cat, pwd, write_file) and a shell command tool (run_command).

- Prefer reading files before writing them.
- When running shell commands, prefer non-destructive commands unless explicitly asked.
- Always explain what you are about to do before invoking a tool.

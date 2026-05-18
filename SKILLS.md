# Skills

## Python Style
triggers: python, function, class, def, import, refactor, style

Follow PEP 8. Use type hints on all function signatures. Prefer descriptive names
over short abbreviations. Keep functions under 30 lines; extract helpers if needed.

## Git Workflow
triggers: git, commit, branch, merge, push, pull, diff, stash

Write commit messages in imperative mood ("Add feature", not "Added feature").
Prefer small, focused commits. Never force-push to main. Always check `git diff`
before committing.

## Debugging
triggers: debug, error, traceback, exception, crash, fix, broken, fail, failing

Start by reading the full traceback. Identify the innermost frame that belongs to
the project code (not a library). Use print statements or pdb to inspect state at
that point before proposing a fix.

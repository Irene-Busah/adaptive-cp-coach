# 🛠️ dev-toolbox

> A growing collection of CLI tools built by developers, for developers. Each tool is small, focused, and solves one real workflow problem.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

---

## ✨ Features

| Tool | Command | What it does |
|------|---------|-------------|
| **Hop** | `dev-toolbox hop <branch>` | Safely switch branches — auto-stashes unsaved work so you never lose code |
| **Replay** | `dev-toolbox replay` | Re-execute the last failing API request from your terminal in one command |

---

## 🚀 Installation

**Requirements:** Python 3.8+

### For Users

Install directly from GitHub without needing to clone the repository:

```bash
pip install git+https://github.com/Irene-Busah/dev-toolbox.git
```

### For Developers (editable install)
```bash
git clone https://github.com/your-username/dev-toolbox.git
cd dev-toolbox
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Once installed, the `dev-toolbox` command is globally available:
```bash
dev-toolbox --help
```

---

## 📖 Tool Reference

### 🐇 `hop` — Smart Branch Switcher

Tired of Git blocking you with *"please commit or stash your changes"* every time you need to context-switch? `hop` handles all that for you automatically.

```bash
# Hop to a branch — auto-stashes any unsaved changes first
dev-toolbox hop <branch-name>

# Hop back to your previous branch and restore your stashed work
dev-toolbox hop -
```

**Example workflow:**
```
$ dev-toolbox hop feature/auth
  Changes detected! Saving stash...
  Checking out branch 'feature/auth'...
  Pulling latest changes...
  Successfully hopped to feature/auth!

$ dev-toolbox hop -
  Hopping back to previous branch...
  Popping the most recent stash...
  Successfully hopped back!
```

---

### 🔁 `replay` — One-Command API Replay

When an API request fails during development, `replay` lets you instantly re-fire it from your terminal — no Postman, no copy-pasting cURL commands.

**Step 1:** Start the background listener daemon (in a separate terminal tab):
```bash
dev-toolbox start-daemon
```
This starts a lightweight local server on `http://localhost:9999` ready to receive request payloads (e.g. from a browser extension).

**Step 2:** Simulate a captured request (or use your browser extension):
```bash
curl -X POST http://127.0.0.1:9999/store-request \
     -H "Content-Type: application/json" \
     -d '{"method": "GET", "url": "https://api.example.com/data", "headers": {}, "body": {}}'
```

**Step 3:** Replay it:
```bash
dev-toolbox replay
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run tests for a specific tool
pytest test_hop.py
pytest test_replay.py
```

---

## 🤝 Contributing

We welcome contributions of all kinds — new tools, bug fixes, tests, and docs!

### Adding a New Tool

This project is intentionally designed to scale with new tools. Here's how:

1. **Fork** this repository and create a new branch:
   ```bash
   git checkout -b tool/my-cool-tool
   ```

2. **Create your command** in the `commands/` directory:
   ```bash
   # commands/my_tool.py
   import typer
   my_tool_app = typer.Typer(help="Description of what your tool does")

   @my_tool_app.callback(invoke_without_command=True)
   def my_tool():
       ...
   ```

3. **Register it** in `cli.py`:
   ```python
   from commands import my_tool
   app.add_typer(my_tool.my_tool_app, name="my-tool")
   ```

4. **Write tests** in a `test_my_tool.py` file.

5. **Open a Pull Request** with a description of the tool and what problem it solves.

### Contribution Guidelines
- Each tool should solve **one specific problem** well
- Keep dependencies minimal — if it can be done with the standard library, prefer that
- All new tools must include tests
- Update this README with your tool's usage

---

## 🗺️ Roadmap

Ideas we're considering for future tools — contributions welcome!

- [ ] **`env`** — Quickly switch between `.env` files for different deployment contexts
- [ ] **`log`** — Tail and pretty-print app logs with colour-coded severity levels
- [ ] **`pr`** — Open the GitHub PR page for your current branch in one command
- [ ] **`todo`** — Scan your codebase for `TODO:` comments and list them in one place
- [ ] **`mock`** — Spin up an instant HTTP mock server from a JSON schema

Have an idea? [Open an issue](https://github.com/your-username/dev-toolbox/issues)!

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

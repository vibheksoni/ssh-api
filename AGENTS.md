# AGENTS.md

This repository provides an OpenAPI-first SSH control plane for AI agents and Linux VPS automation.

## What This Repo Is

- FastAPI service that exposes SSH, SFTP, tunnels, system operations, setup helpers, and firewall routes
- designed so agents can use structured HTTP and OpenAPI instead of raw interactive SSH
- intended for trusted environments and private operator workflows

## Key Commands

### Install

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
```

macOS / Linux:

```bash
./scripts/bootstrap.sh
```

Manual:

```bash
pip install -r requirements.txt
python run.py
```

### Start The API

```bash
python run.py
```

### Basic Verification

```bash
python -m compileall src run.py
```

The service entrypoint is [`run.py`](./run.py). The FastAPI app lives in [`src/app.py`](./src/app.py).

## Important Files

- [`README.md`](./README.md): public overview
- [`SSH_API_GUIDE.md`](./SSH_API_GUIDE.md): full route and workflow guide
- [`AGENT_SETUP_PROMPT.md`](./AGENT_SETUP_PROMPT.md): copy-paste prompt for an agent to install and start the API
- [`AGENT_PROMPTS.md`](./AGENT_PROMPTS.md): reusable prompts for operating the API against a VPS
- [`config.example.json`](./config.example.json): safe config template
- `config.json`: local config file, ignored by git
- [`llms.txt`](./llms.txt) and [`llms-full.txt`](./llms-full.txt): public agent-readable indexes

## Repo Structure

- `src/routes/`: FastAPI route handlers
- `src/services/`: SSH, SFTP, platform, firewall, tunnel, and system abstractions
- `src/models/`: request and response models
- `src/core/`: config and logging

The service is structured so route files stay thin and delegate behavior to services.

## Editing Guidance

- Keep the API surface aligned with the documentation.
- If you change routes or request/response behavior, update:
  - `README.md`
  - `SSH_API_GUIDE.md`
  - `AGENT_SETUP_PROMPT.md` if setup or startup behavior changed
  - `AGENT_PROMPTS.md` if operator workflows changed
  - `llms.txt` and `llms-full.txt` if the docs map changed
- Prefer additive changes over breaking endpoint changes.
- Keep `config.json` out of git and do not place real credentials in tracked files.

## Security Constraints

- Treat this service as privileged remote-access infrastructure.
- Do not add tracked secrets, default live credentials, or private keys.
- Do not weaken the documentation around access control; this API should not be presented as safe for direct public exposure.

## Agent Workflow

When operating the running API, agents should:

1. Fetch `/openapi.json`.
2. Read `SSH_API_GUIDE.md`.
3. Create a session with `POST /session/connect`.
4. Store the returned `session_id`.
5. Prefer the structured endpoint groups instead of inventing raw SSH logic.
6. Disconnect the session when the task is complete.

## Notes

- There is no formal automated test suite in this repo right now.
- Use compile/import checks and documentation consistency as the minimum validation bar.

---
name: ssh-api-setup
description: Use this skill when you need to install, configure, start, verify, or hand off SSH ~ Api to another agent. It covers local bootstrap, config creation, startup, OpenAPI discovery, and the correct workflow for using the API against a Linux VPS.
---

# SSH ~ Api Setup Skill

Repository:

- `https://github.com/vibheksoni/ssh-api`

## When To Use

Use this skill when:

- setting up the repository locally for the first time
- asking an agent to start the API
- handing the running API to another agent
- documenting or verifying the correct agent workflow

Do not use this skill for unrelated Python repo tasks.

## Core Workflow

1. Bootstrap the repository.
2. Ensure `config.json` exists, preferably copied from `config.example.json`.
3. Start the API with `python run.py`.
4. Verify that `/docs`, `/redoc`, and `/openapi.json` are reachable.
5. Read `SSH_API_GUIDE.md`.
6. When operating the API against a remote host, create a session and store `session_id`.

## Preferred Commands

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

## Install This Skill

Public GitHub install via `npx skills`:

```bash
npx skills add vibheksoni/ssh-api --skill ssh-api-setup
```

List available skills in this repo first:

```bash
npx skills add vibheksoni/ssh-api --list
```

## Rules

- Never commit `config.json`.
- Never place real credentials in tracked files.
- Prefer the API's structured routes over inventing raw SSH workflows.
- If the API is already running, verify it instead of starting a duplicate instance.

## Validation

At minimum, confirm:

- the server process started successfully
- `/docs` is reachable
- `/openapi.json` is reachable
- the next agent knows to fetch `/openapi.json` and read `SSH_API_GUIDE.md`

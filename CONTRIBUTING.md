# Contributing

Thanks for contributing to `SSH ~ Api`.

## What Helps Most

The highest-value contributions for this project are:

- improving real VPS workflows
- reducing agent friction
- improving installability and docs
- expanding Linux compatibility
- tightening safety and reliability

## Local Setup

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

## Verify Before Opening A PR

Run:

```bash
python scripts/verify.py
```

That is the current smoke-check for this repo.

## Documentation Rule

If you change behavior, routes, setup flow, or repo handoff, update the matching docs:

- `README.md`
- `SSH_API_GUIDE.md`
- `AGENT_SETUP_PROMPT.md`
- `AGENT_PROMPTS.md`
- `AGENTS.md`
- `llms.txt`
- `llms-full.txt`

## Scope Guardrails

- do not add tracked secrets
- do not commit `config.json`
- prefer structured endpoint additions over ad hoc shell-only behavior
- preserve the repo’s agent-first framing

## Pull Request Style

- keep changes focused
- explain user-facing impact clearly
- mention any Linux-family caveats
- include verification notes

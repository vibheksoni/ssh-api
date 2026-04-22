# Changelog

## Unreleased

- added agent-facing repo assets: `AGENTS.md`, `llms.txt`, `llms-full.txt`, prompt files, and a skill-style setup doc
- rewrote public docs to position the project as an OpenAPI-first SSH control plane for agents
- added bootstrap scripts for Windows and POSIX environments
- added package metadata with `pyproject.toml`
- added Docker support with `Dockerfile` and `docker-compose.yml`
- added smoke verification via `scripts/verify.py`
- added `SECURITY.md` and `CONTRIBUTING.md`

## 0.1.0

- initial FastAPI SSH API service with sessions, command execution, SFTP, tunnels, config routes, system operations, setup helpers, and firewall support

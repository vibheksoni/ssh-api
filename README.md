<h1 align="center">SSH ~ Api</h1>

<p align="center"><strong>OpenAPI-first SSH control plane for AI agents and Linux VPS automation.</strong></p>

<p align="center">Give any agent a structured HTTP layer for commands, file transfer, provisioning, tunnels, and server administration instead of brittle raw terminal SSH.</p>

<p align="center">
  <a href="https://deepwiki.com/vibheksoni/ssh-api"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>

<p align="center">
  <a href="https://discord.gg/secrets"><strong>Join the Discord server</strong></a> to get updates, ask questions, and get a free API key for Free AI.
</p>

<p align="center">
  <a href="./SSH_API_GUIDE.md">Guide</a> |
  <a href="./AGENT_SETUP_PROMPT.md">Setup Prompt</a> |
  <a href="./AGENT_PROMPTS.md">Prompt Library</a> |
  <a href="./AGENTS.md">AGENTS.md</a> |
  <a href="./llms.txt">llms.txt</a>
</p>

## Why This Exists

Most AI agents are much better at using HTTP and OpenAPI than they are at improvising over raw SSH.

`SSH ~ Api` exists to give agents a clean, predictable layer for remote Linux work:

- connect to a VPS or other Linux machine
- upload, download, read, and write files
- run commands and read output
- inspect logs, processes, services, and system state
- perform provisioning and repeatable server operations
- automate both simple tasks and multi-step workflows through a stable API

This is not just "SSH over HTTP." It is a structured server-operations layer designed so agents can discover capabilities quickly and use them consistently.

## Why Agents Use This Better Than Raw SSH

| Raw SSH | SSH ~ Api |
| --- | --- |
| agent has to invent its own workflow | agent follows documented endpoints |
| output handling is ad hoc | output is structured JSON |
| file movement is custom logic | file operations are first-class routes |
| session state is implicit | sessions are explicit and trackable |
| distro assumptions are brittle | setup and service behavior are distro-aware where possible |
| hard to hand off between tools | OpenAPI makes the surface portable across agents |

## What An Agent Can Automate

- connect to a VPS and inspect the server state
- deploy application files over SFTP
- run install, build, restart, and debug commands
- read logs and diagnose failures
- manage services, environment variables, and cron jobs
- create archives and backups
- provision core packages on new Linux hosts
- open a tunnel to reach an internal service during debugging
- perform common day-2 operations without custom terminal glue

## Fastest Setup

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
```

### macOS / Linux

```bash
./scripts/bootstrap.sh
```

### Manual

```bash
pip install -r requirements.txt
cp config.example.json config.json
python run.py
```

### Install As A Local Package

```bash
pip install .
ssh-api
```

### Docker

```bash
docker compose up --build
```

After startup, the main endpoints are:

- Swagger UI: `http://localhost:8754/docs`
- ReDoc: `http://localhost:8754/redoc`
- OpenAPI JSON: `http://localhost:8754/openapi.json`

If your local `config.json` changes the port, use that port instead.

## Copy And Paste This To Your Agent

Use the full version in [`AGENT_SETUP_PROMPT.md`](./AGENT_SETUP_PROMPT.md). The short version is below:

```text
Set up SSH ~ Api in this repository.

Goals:
- create a local virtual environment
- install dependencies
- create config.json from config.example.json if it does not exist
- start the API locally
- report the base URL, /docs URL, /redoc URL, and /openapi.json URL

Rules:
- do not commit config.json
- do not place real credentials into tracked files
- if the API is already running, verify it instead of starting a duplicate copy
- after startup, fetch /openapi.json and read SSH_API_GUIDE.md so you understand the API surface

Preferred setup flow:
- on Windows, run scripts/bootstrap.ps1
- on macOS/Linux, run scripts/bootstrap.sh
- if those are unavailable, do the setup manually

When finished:
- tell me exactly how to stop the server
- tell me which host/port it is running on
- summarize the next step for using it against a VPS
```

## How It Works

1. The agent fetches `/openapi.json`.
2. The agent reads [`SSH_API_GUIDE.md`](./SSH_API_GUIDE.md).
3. The agent creates a session with `POST /session/connect`.
4. The agent stores the returned `session_id`.
5. The agent uses the structured command, file, system, setup, tunnel, and firewall routes instead of improvising raw SSH behavior.
6. The agent disconnects the session when the task is complete.

## Agent-Ready Docs

Use these in this order:

1. `/openapi.json` for the authoritative machine-readable contract
2. [`SSH_API_GUIDE.md`](./SSH_API_GUIDE.md) for workflow, conventions, and route guidance
3. [`AGENT_SETUP_PROMPT.md`](./AGENT_SETUP_PROMPT.md) for copy-paste installation instructions
4. [`AGENT_PROMPTS.md`](./AGENT_PROMPTS.md) for reusable server automation prompts
5. [`AGENTS.md`](./AGENTS.md) for repository-level agent context
6. [`llms.txt`](./llms.txt) and [`llms-full.txt`](./llms-full.txt) for public agent-readable indexing

## Common Use Cases

- Deploy a new app release to a VPS
- Read logs and diagnose a failing service
- Bootstrap a fresh Linux server with common packages
- Upload config files and restart services
- Create an archive backup before making changes
- Search the filesystem and inspect environment variables
- Open a tunnel to reach an internal service during debugging

Reusable prompts for those workflows are in [`AGENT_PROMPTS.md`](./AGENT_PROMPTS.md).

## Linux Compatibility

This project started with Debian and Ubuntu testing.

It now detects the remote platform and adapts where possible for:

- Debian and Ubuntu
- RHEL, CentOS, Rocky, AlmaLinux, Fedora
- SUSE and openSUSE
- Alpine
- Arch-based systems

The strongest compatibility areas are session handling, command execution, file transfer, and general SSH behavior. Package-management and firewall operations are distro-aware and best-effort where the required tools exist on the target host.

## Security

This API is powerful. Treat it like remote shell access.

- It has no built-in HTTP authentication.
- Put it behind a reverse proxy, VPN, IP allowlist, or another access-control layer before exposing it anywhere real.
- Keep `config.json` local and ignored by git.
- The `/config` endpoints can expose or modify locally stored default SSH credentials.
- Use least-privilege SSH accounts whenever possible.
- Treat firewall and destructive system routes as privileged operations.

## Repo Files

- [`README.md`](./README.md): public overview and positioning
- [`SSH_API_GUIDE.md`](./SSH_API_GUIDE.md): full API workflow and endpoint guide
- [`AGENT_SETUP_PROMPT.md`](./AGENT_SETUP_PROMPT.md): copy-paste setup prompt for agents
- [`AGENT_PROMPTS.md`](./AGENT_PROMPTS.md): reusable prompts for VPS workflows
- [`AGENTS.md`](./AGENTS.md): repo-wide agent context
- [`llms.txt`](./llms.txt): public agent-readable index
- [`llms-full.txt`](./llms-full.txt): expanded agent-readable context
- [`config.example.json`](./config.example.json): safe public config template
- [`CONTRIBUTING.md`](./CONTRIBUTING.md): contribution flow
- [`SECURITY.md`](./SECURITY.md): security reporting guidance
- [`CHANGELOG.md`](./CHANGELOG.md): project change log
- [`ROADMAP.md`](./ROADMAP.md): near-term roadmap

## Public Handoff

If you publish this on GitHub, the clean handoff is:

- humans start with `README.md`
- agents start with `/openapi.json`
- both should read [`SSH_API_GUIDE.md`](./SSH_API_GUIDE.md)
- coding agents working inside the repo should read [`AGENTS.md`](./AGENTS.md)

That is the intended way to use this project.

---

<div align="center">

# Free AI

### Free OpenAI-compatible AI API for anyone to use

Get a key through Discord, point your client at the base URL, and start building.

[![API](https://img.shields.io/badge/API-OpenAI%20Compatible-111827?style=for-the-badge)](https://api.freetheai.xyz)
[![Base URL](https://img.shields.io/badge/Base%20URL-api.freetheai.xyz-0ea5e9?style=for-the-badge)](https://api.freetheai.xyz)
[![Limits](https://img.shields.io/badge/Limit-30%20RPM-f59e0b?style=for-the-badge)](https://discord.gg/secrets)
[![Privacy](https://img.shields.io/badge/Logging-No%20Prompt%20Storage-16a34a?style=for-the-badge)](https://api.freetheai.xyz/v1/health)
[![Discord](https://img.shields.io/badge/Discord-discord.gg%2Fsecrets-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/secrets)

</div>

## What This Is

`Free AI` is a public OpenAI-compatible API for builders who want working model access without the usual friction.

- No credit card
- No daily limit
- No prompt storage
- One Discord slash command to get started

If you can use the OpenAI SDK, you can use this API.

## Community

- Discord invite: `https://discord.gg/rG3SYpeqYF`
- Vanity invite: `https://discord.gg/secrets`

## Get A Key

1. Join the Discord server.
2. Run `/signup`.
3. Copy your key immediately.

If you lose it later:

- run `/resetkey`
- get a brand new key
- keep the same usage totals and account stats

## Limits

- `30 requests per minute`
- `No daily limit`

The per-minute cap exists so everyone gets a fair chance to use it.

## Privacy

Prompt text and completion text are **not** stored.

Only request metadata is kept:

- model id
- input token count
- output token count
- request timestamp
- request status
- source IP

## Base URL

```text
https://api.freetheai.xyz
```

## API Surface

| Route | Method | Description |
| --- | --- | --- |
| `/v1/health` | `GET` | Health check |
| `/v1/models` | `GET` | Current model list |
| `/v1/chat/completions` | `POST` | OpenAI-compatible chat completions |

Auth header:

```http
Authorization: Bearer YOUR_API_KEY
```

## Quick Start

### List Models

```bash
curl https://api.freetheai.xyz/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Chat Completion

```bash
curl https://api.freetheai.xyz/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm/glm-5.1",
    "messages": [
      {
        "role": "user",
        "content": "Write a hello world in Python."
      }
    ]
  }'
```

### Python

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://api.freetheai.xyz/v1",
)

completion = client.chat.completions.create(
    model="glm/glm-5.1",
    messages=[
        {"role": "user", "content": "Explain recursion in one paragraph."}
    ],
)

print(completion.choices[0].message.content)
```

### JavaScript

```js
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "YOUR_API_KEY",
  baseURL: "https://api.freetheai.xyz/v1"
});

const completion = await client.chat.completions.create({
  model: "glm/glm-5.1",
  messages: [
    { role: "user", content: "Say hello in one sentence." }
  ]
});

console.log(completion.choices[0].message.content);
```

### Raw Fetch

```js
const response = await fetch("https://api.freetheai.xyz/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "or/openai/gpt-oss-20b:free",
    messages: [
      { role: "user", content: "Summarize recursion in simple terms." }
    ]
  })
});

const data = await response.json();
console.log(data);
```

## Models

Use the exact ids returned by `GET /v1/models`.

Current model families:

- `glm/*`
- `kai/*`
- `opc/*`
- `or/*`

Live site:

- `https://freetheai.xyz/`

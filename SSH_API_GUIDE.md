# SSH API Guide

This is the human-readable operating guide for `SSH ~ Api`.

The machine-readable contract is the live OpenAPI spec at `/openapi.json`. If you are giving this project to an AI agent, that spec is the first thing it should fetch. This guide explains the workflow around the API: sessions, path semantics, distro behavior, and the practical meaning of each endpoint group.

Related docs:

- [`README.md`](./README.md): public overview and positioning
- [`AGENT_SETUP_PROMPT.md`](./AGENT_SETUP_PROMPT.md): copy-paste prompt for asking an agent to install and start the API
- [`AGENT_PROMPTS.md`](./AGENT_PROMPTS.md): reusable prompts for common VPS workflows
- [`AGENTS.md`](./AGENTS.md): repository-level agent context
- [`llms.txt`](./llms.txt): compact public agent-readable index
- [`CONTRIBUTING.md`](./CONTRIBUTING.md): contributor setup and verification

## At A Glance

- Base URL: `http://HOST:PORT`
- Health endpoint: `GET /`
- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`
- OpenAPI spec: `GET /openapi.json`
- Public config template: [`config.example.json`](./config.example.json)
- Local ignored config: `config.json`

If your local `config.json` changes the port, use that port instead of the example `8754`.

## Why This Exists

This project exists because AI agents are usually much more reliable when they can work against HTTP and OpenAPI instead of raw interactive SSH. The goal is simple:

- let an agent connect to a VPS or other Linux machine
- upload and download files
- run commands and read output
- inspect the system
- handle common admin tasks
- do all of that through an API shape agents are already comfortable using

Instead of teaching every agent a custom SSH workflow, this gives it a stable API surface.

## How To Hand This To An Agent

Tell the agent to do this in order:

1. Fetch `http://HOST:PORT/openapi.json`.
2. Read this `SSH_API_GUIDE.md`.
3. Create a session with `POST /session/connect`.
4. Store the returned `session_id`.
5. Include `session_id` on later requests if more than one session may exist.
6. Prefer `POST /command/exec` for bounded tasks.
7. Use `POST /command/shell` and `GET /command/read` only when interactive shell behavior is actually needed.
8. Disconnect with `POST /session/disconnect/{session_id}` when the task is finished.

Recommended agent handoff prompt:

```text
Use SSH ~ Api as your interface to the target Linux machine.
First fetch http://HOST:PORT/openapi.json.
Then read SSH_API_GUIDE.md before taking actions.
Create a session with POST /session/connect, store the returned session_id, and reuse it on later requests.
Prefer command, file, system, setup, tunnel, and firewall endpoints over inventing your own SSH behavior.
Disconnect the session when the task is complete.
```

## Core Concepts

### Sessions

- Every SSH connection becomes a session.
- `POST /session/connect` returns a `session_id`.
- Most routes under `command`, `file`, `tunnel`, `system`, `setup`, and `firewall` accept an optional `session_id` query parameter.
- If `session_id` is omitted, the service uses the first connected session it finds.
- That fallback is convenient for single-session use, but explicit `session_id` is safer for agents.

### Path Semantics

- `remote_path`, `path`, `source`, `destination`, and similar fields refer to the remote Linux host.
- `local_path` refers to the filesystem of the machine running `SSH ~ Api`, not the remote host.
- `POST /file/download` with `return_content=true` returns base64 content in the response instead of only writing to a local file.

### Command Modes

- `POST /command/exec` waits for completion and returns stdout, stderr, exit code, and duration.
- `GET /command/run` does the same thing through query parameters and is useful when a command is annoying to JSON-escape.
- `POST /command/shell` sends text to an interactive shell.
- `GET /command/read` reads accumulated interactive shell output.
- `POST /command/background` starts work in the background and `GET /command/task/{task_id}` polls it later.

### Linux Compatibility

- This project was originally tested on Ubuntu and other Debian-based systems.
- It now detects the remote distro family and adapts package-management and service/firewall behavior where possible.
- Current compatibility targets are:
  - Debian and Ubuntu
  - RHEL, CentOS, Rocky, AlmaLinux, Fedora
  - SUSE and openSUSE
  - Alpine
  - Arch-based systems
- `/setup/requirements` adapts to the detected package manager.
- `/system/service` adapts to the detected service manager where possible.
- Firewall behavior detects `iptables` vs `firewalld`.

### Security

- This API has no built-in HTTP authentication.
- Do not expose it directly to the public internet without a reverse proxy, VPN, IP allowlist, or another access-control layer.
- `config.json` may contain default SSH credentials. Keep it local and ignored by git.
- The `/config` endpoints can reveal or modify those defaults. Treat them as privileged endpoints.
- Use a least-privilege SSH account whenever possible instead of `root`.

## Quick Start

### 1. Bootstrap The Repo

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
```

macOS / Linux:

```bash
./scripts/bootstrap.sh
```

### 2. Or Install Dependencies Manually

```bash
pip install -r requirements.txt
```

### 3. Create Local Config

Copy [`config.example.json`](./config.example.json) to `config.json`, then edit `config.json` locally if you want default SSH credentials, timeouts, or a different bind port.

Do not commit `config.json`.

### 4. Start The API

```bash
python run.py
```

Or, if you installed the package locally:

```bash
ssh-api
```

Or with Docker:

```bash
docker compose up --build
```

By default, the public example config uses `http://localhost:8754`.

### 5. Connect To A Host

```bash
curl -X POST http://localhost:8754/session/connect \
  -H "Content-Type: application/json" \
  -d "{\"host\":\"YOUR_SSH_HOST\",\"username\":\"YOUR_SSH_USERNAME\",\"password\":\"YOUR_SSH_PASSWORD\"}"
```

Example request body:

```json
{
  "host": "203.0.113.10",
  "port": 22,
  "username": "your-ssh-user",
  "password": "<set-at-request-time>",
  "key_path": "/path/to/private_key",
  "key_passphrase": "<optional>",
  "key_content": "base64_encoded_key",
  "use_agent": false,
  "keepalive": true,
  "retries": 3,
  "retry_delay": 1.0
}
```

Example response:

```json
{
  "status": "connected",
  "session_id": "a1b2c3d4e5f6",
  "host": "203.0.113.10",
  "username": "your-ssh-user",
  "features": ["sftp", "shell", "exec", "background_tasks", "tunnels"]
}
```

If you set defaults in `config.json`, you can also connect with an empty body:

```bash
curl -X POST http://localhost:8754/session/connect \
  -H "Content-Type: application/json" \
  -d "{}"
```

## Endpoint Reference

Unless noted otherwise, routes in `command`, `file`, `tunnel`, `system`, `setup`, and `firewall` accept an optional `session_id` query parameter.

### Health And Docs

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service health and metadata |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc UI |
| `GET` | `/openapi.json` | Canonical OpenAPI spec for agents |

### Connection

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/session/connect` | Open an SSH session |
| `POST` | `/session/disconnect/{session_id}` | Disconnect a specific session |
| `GET` | `/session/status/{session_id}` | Check whether a session is still connected |
| `GET` | `/session/list` | List all tracked sessions |

Notes:

- Missing connection fields fall back to defaults from `config.json`.
- Authentication supports password, key file path, base64 key content, and optional SSH agent usage.

### Commands

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/command/exec` | Run a command and wait for completion |
| `GET` | `/command/run` | Run a command through query parameters instead of JSON |
| `POST` | `/command/shell` | Send text to the interactive shell |
| `GET` | `/command/read` | Read available interactive shell output |
| `POST` | `/command/key` | Send a special key sequence to the shell |
| `POST` | `/command/background` | Start a background task |
| `GET` | `/command/task/{task_id}` | Poll a background task |

Useful request bodies:

```json
{
  "command": "ls -la /var/www",
  "timeout": 30.0,
  "get_exit_code": true
}
```

```json
{
  "key": "ctrl+c"
}
```

Useful query-style command example:

```text
GET /command/run?cmd=ls%20-la%20/var/www&timeout=30
```

Supported special keys:

- `ctrl+c`
- `ctrl+d`
- `ctrl+z`
- `ctrl+a`
- `ctrl+e`
- `ctrl+k`
- `ctrl+l`
- `ctrl+u`
- `ctrl+w`
- `enter`
- `tab`
- `escape`
- `backspace`
- `up`
- `down`
- `left`
- `right`
- `home`
- `end`
- `pageup`
- `pagedown`

### Files

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/file/upload` | Upload a file to the remote host |
| `POST` | `/file/download` | Download a remote file |
| `GET` | `/file/list` | List a remote directory |
| `POST` | `/file/mkdir` | Create a remote directory |
| `DELETE` | `/file/remove` | Remove a remote file |
| `GET` | `/file/stat` | Stat a remote file or directory |
| `GET` | `/file/read` | Read a remote file as text |
| `POST` | `/file/write` | Write text to a remote file |
| `POST` | `/file/copy` | Copy a remote directory recursively |
| `DELETE` | `/file/rmdir` | Remove a remote directory recursively |

Upload supports three modes:

1. local file path on the API server machine
2. raw text content
3. base64 content

Example upload from local path:

```json
{
  "remote_path": "/var/www/index.html",
  "local_path": "C:/deploy/index.html",
  "permissions": 644
}
```

Example upload from raw text:

```json
{
  "remote_path": "/etc/my-app/config.ini",
  "raw_content": "[server]\nport=8080\n"
}
```

Example download:

```json
{
  "remote_path": "/var/log/app.log",
  "local_path": "C:/downloads/app.log",
  "return_content": false
}
```

Useful query-style file examples:

```text
GET /file/list?path=/var/www
POST /file/mkdir?path=/var/www/releases
DELETE /file/remove?path=/var/www/old.txt
GET /file/stat?path=/var/www/index.html
GET /file/read?path=/etc/hosts
POST /file/copy?src=/var/www/current&dst=/var/www/backup
DELETE /file/rmdir?path=/var/www/old-release
```

Example remote write:

```json
{
  "path": "/etc/my-app/config.ini",
  "content": "new text",
  "mode": "overwrite"
}
```

Valid write modes:

- `overwrite`
- `append`
- `prepend`

### Tunnels

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/tunnel/local` | Create an SSH local forward |
| `POST` | `/tunnel/remote` | Create an SSH remote forward |
| `GET` | `/tunnel/list` | List active tunnels |
| `DELETE` | `/tunnel/{tunnel_id}` | Close one tunnel |
| `DELETE` | `/tunnel/` | Close all tunnels |

Notes:

- Local forwards bind on the machine running `SSH ~ Api` and forward through SSH to the remote target.
- Remote forwards bind on the remote host and forward back to a local host/port reachable from the API server machine.

Example local forward:

```json
{
  "local_port": 8080,
  "remote_host": "127.0.0.1",
  "remote_port": 80,
  "bind_address": "127.0.0.1"
}
```

Example remote forward:

```json
{
  "remote_port": 8080,
  "local_host": "127.0.0.1",
  "local_port": 3000,
  "bind_address": "0.0.0.0"
}
```

### System

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/system/platform` | Detect distro family, package manager, service manager, firewall backend, and related capabilities |
| `GET` | `/system/processes` | List processes, optionally filtered by user |
| `POST` | `/system/kill` | Send `TERM`, `KILL`, `HUP`, or `INT` to a PID |
| `GET` | `/system/disk` | Get disk usage |
| `GET` | `/system/memory` | Get memory info |
| `GET` | `/system/cpu` | Get CPU model and load |
| `GET` | `/system/network` | List network interfaces |
| `POST` | `/system/service` | Manage services through the detected service manager |
| `POST` | `/system/grep` | Search files with grep |
| `POST` | `/system/find` | Find files/directories |
| `POST` | `/system/archive` | Create an archive |
| `POST` | `/system/extract` | Extract an archive |
| `GET` | `/system/env/{name}` | Read an environment variable |
| `POST` | `/system/env` | Set an environment variable |
| `GET` | `/system/cron` | List cron jobs |
| `POST` | `/system/cron` | Add a cron job |
| `GET` | `/system/users` | List users from `/etc/passwd` |
| `POST` | `/system/chmod` | Change permissions |
| `POST` | `/system/chown` | Change ownership |
| `GET` | `/system/tail` | Tail a file |
| `GET` | `/system/head` | Head a file |
| `GET` | `/system/uptime` | Get uptime |
| `DELETE` | `/system/rmrf` | Recursive delete with guardrails |

Useful request bodies:

```json
{
  "pid": "1234",
  "signal": "TERM"
}
```

```json
{
  "service": "nginx",
  "action": "restart"
}
```

```json
{
  "pattern": "error",
  "path": "/var/log",
  "recursive": true,
  "ignore_case": true,
  "max_results": 100
}
```

```json
{
  "path": "/var/www",
  "name": "*.log",
  "type": "f",
  "max_depth": 5,
  "max_results": 100
}
```

```json
{
  "source": "/var/www/html",
  "destination": "/tmp/backup.tar.gz",
  "format": "tar.gz"
}
```

```json
{
  "archive": "/tmp/backup.tar.gz",
  "destination": "/var/restored"
}
```

```json
{
  "name": "MY_VAR",
  "value": "my_value",
  "persist": true
}
```

```json
{
  "schedule": "0 * * * *",
  "command": "/usr/local/bin/backup.sh"
}
```

Useful query-style system examples:

```text
GET /system/processes?user=deploy
POST /system/chmod?path=/var/www&mode=755&recursive=true
POST /system/chown?path=/var/www&owner=deploy&group=deploy&recursive=true
GET /system/tail?path=/var/log/messages&lines=100
GET /system/head?path=/etc/hosts&lines=20
DELETE /system/rmrf?path=/tmp/old-build
```

Notes:

- `persist=true` on `/system/env` appends an export line to `~/.bashrc`.
- `/system/service` is no longer hard-wired to `systemctl`; it chooses the best detected service manager.
- `/system/rmrf` refuses obvious root or home-directory targets.

### Setup

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/setup/platform` | Detect setup and package-management capabilities |
| `POST` | `/setup/requirements` | Install packages through the detected package manager |

Example request:

```json
{
  "packages": ["nginx", "docker.io"],
  "update_first": true
}
```

Example response:

```json
{
  "status": "completed",
  "installed": ["nginx", "docker.io"],
  "failed": [],
  "output": "[PLATFORM] Rocky Linux 9.5\n[PACKAGE_MANAGER] dnf\n[UPDATE] exit=0\n[OK] nginx\n[OK] docker.io",
  "package_manager": "dnf",
  "platform": {
    "os": "rocky",
    "family": "rhel",
    "pretty_name": "Rocky Linux 9.5",
    "version_id": "9.5"
  },
  "resolved_packages": ["nginx", "docker.io"]
}
```

Notes:

- If `packages` is omitted or empty, the API uses a default essentials set for the detected package manager.
- Debian-oriented package names are translated to local equivalents where possible.
- Unsupported package names for a specific manager are skipped instead of blindly forced.
- Supported package-manager targets include `apt-get`, `dnf`, `yum`, `zypper`, `apk`, and `pacman`.

### Firewall

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/firewall/backend` | Detect the active firewall backend |
| `GET` | `/firewall/rules` | List rules |
| `GET` | `/firewall/rules/raw` | Get raw rules for backup/debugging |
| `POST` | `/firewall/rule` | Add a rule |
| `DELETE` | `/firewall/rule` | Delete a rule by line number |
| `POST` | `/firewall/rule/port-range` | Add a port-range rule |
| `POST` | `/firewall/flush` | Flush rules |
| `POST` | `/firewall/save` | Persist current rules |
| `POST` | `/firewall/restore` | Reload persisted rules |
| `POST` | `/firewall/policy` | Set default chain policy |
| `POST` | `/firewall/allow/port` | Allow a port |
| `POST` | `/firewall/block/port` | Block a port |
| `POST` | `/firewall/block/ip` | Block an IP |
| `POST` | `/firewall/allow/ip` | Allow an IP |

Common request body for `/firewall/rule`:

```json
{
  "chain": "INPUT",
  "protocol": "tcp",
  "port": 443,
  "source": "192.168.1.0/24",
  "destination": null,
  "target": "ACCEPT",
  "ip_version": "both",
  "comment": "Allow HTTPS from LAN"
}
```

Common request body for `/firewall/rule/port-range`:

```json
{
  "chain": "INPUT",
  "protocol": "tcp",
  "port_start": 8000,
  "port_end": 9000,
  "source": null,
  "target": "ACCEPT",
  "ip_version": "both"
}
```

Query helpers:

- `POST /firewall/allow/port?port=80&protocol=tcp&ip_version=both`
- `POST /firewall/block/port?port=3306&protocol=tcp&ip_version=both`
- `POST /firewall/block/ip?ip=10.0.0.5&ip_version=both`
- `POST /firewall/allow/ip?ip=192.168.1.100&ip_version=both`
- `POST /firewall/policy?chain=INPUT&target=DROP&ip_version=both`
- `POST /firewall/flush?chain=INPUT&ip_version=both`

Notes:

- `ip_version` accepts `ipv4`, `ipv6`, or `both`.
- On iptables-based hosts, the API uses `iptables` and `ip6tables`.
- On firewalld-based hosts, the API uses firewalld-aware save/restore behavior and helper-rule fallbacks where possible.
- Advanced line-number delete semantics are strongest on iptables backends.

### Configuration

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/config/` | Get the full config object |
| `GET` | `/config/{key}` | Get one config value by dot notation |
| `PUT` | `/config/` | Set one config value by dot notation |
| `POST` | `/config/reload` | Reload config from disk |

Example config update:

```json
{
  "key": "ssh.timeout",
  "value": 60
}
```

Be careful: this endpoint can expose or change default credentials stored in local config.

## Config File

The public template is [`config.example.json`](./config.example.json).

Copy it to `config.json`, edit it locally, and keep `config.json` out of git.

Config areas:

- `server`: bind host, port, debug mode
- `ssh`: default port, timeouts, keepalive, concurrency
- `auth`: optional default SSH connection fields
- `sftp`: chunk and file-size behavior
- `security`: disabled algorithms and host-key behavior
- `logging`: log level and log directory

## Error Format

FastAPI error responses follow the standard shape:

```json
{
  "detail": "Error message here"
}
```

Common status codes:

- `200` for success
- `400` for invalid input or unsupported local capability
- `404` for missing sessions, missing tunnels, or similar lookup failures
- `500` for remote execution or internal failures

## Publishing Notes

Before sharing this project publicly:

- keep `config.json` ignored
- ship `config.example.json`
- point humans to `/docs`
- point agents to `/openapi.json`
- tell agents to read this guide before acting

That combination is the intended public handoff flow.

---
name: ssh-api-vps-automation
description: Use this skill when an agent needs to operate a Linux VPS through SSH ~ Api instead of raw SSH. It covers fetching the OpenAPI spec, creating sessions, storing session_id, using command/file/system/setup/tunnel routes, and disconnecting cleanly.
---

# SSH ~ Api VPS Automation Skill

Repository:

- `https://github.com/vibheksoni/ssh-api`

## What This Skill Is

This skill teaches an AI agent how to use `SSH ~ Api` as a structured Linux server automation layer.

Instead of improvising over raw SSH, the agent should:

1. fetch `/openapi.json`
2. read `SSH_API_GUIDE.md`
3. create a session with `POST /session/connect`
4. store the returned `session_id`
5. use the structured endpoint groups
6. disconnect when the task is complete

## When To Use

Use this skill when:

- deploying files to a VPS
- diagnosing a server issue
- inspecting system state
- provisioning packages on a Linux host
- restarting or checking services
- managing archives, environment variables, logs, tunnels, or firewall rules through the API

Do not use this skill when the task is unrelated to `SSH ~ Api` or when direct repository editing is the real task.

## Install This Skill

Public GitHub install via `npx skills`:

```bash
npx skills add vibheksoni/ssh-api --skill ssh-api-vps-automation
```

List available skills in this repo:

```bash
npx skills add vibheksoni/ssh-api --list
```

## Agent Workflow

### 1. Discover the API

- Fetch `http://HOST:PORT/openapi.json`
- Read `SSH_API_GUIDE.md`

### 2. Create a Session

Use `POST /session/connect`.

Store the returned `session_id`.

### 3. Prefer Structured Endpoints

Use:

- `command/*` for command execution
- `file/*` for uploads, downloads, reads, writes, mkdir, stat, copy, remove
- `system/*` for logs, services, env vars, grep, find, archive, users, uptime, platform detection
- `setup/*` for package-management and distro-aware setup
- `tunnel/*` for SSH forwards
- `firewall/*` for backend-aware firewall operations

### 4. Finish Cleanly

Disconnect with `POST /session/disconnect/{session_id}`.

## Rules

- Prefer structured API calls over inventing raw shell flows
- Always track `session_id`
- Detect the remote platform before distro-sensitive setup work
- Treat destructive routes and firewall changes as privileged actions
- Do not assume Ubuntu-specific behavior if the platform endpoints say otherwise

## Success Criteria

The agent:

- uses `/openapi.json` as the machine-readable contract
- uses `SSH_API_GUIDE.md` as the workflow guide
- tracks `session_id`
- performs the requested VPS task with the documented endpoints
- disconnects when done

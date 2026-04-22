# Skills In This Repo

This repository exposes public `SKILL.md` files under `skills/` so other agents can install them from GitHub.

Repository:

- `https://github.com/vibheksoni/ssh-api`

Available skills:

- `ssh-api-setup`
- `ssh-api-vps-automation`

## Install From GitHub

Using the public `npx skills` GitHub installer:

```bash
npx skills add vibheksoni/ssh-api --list
```

Install one skill:

```bash
npx skills add vibheksoni/ssh-api --skill ssh-api-setup
```

```bash
npx skills add vibheksoni/ssh-api --skill ssh-api-vps-automation
```

Non-interactive example:

```bash
npx skills add vibheksoni/ssh-api --skill ssh-api-vps-automation -a claude-code -y
```

## What These Skills Teach

- `ssh-api-setup`: how to bootstrap, configure, start, and verify the local API
- `ssh-api-vps-automation`: how to operate a Linux VPS through the API instead of raw SSH

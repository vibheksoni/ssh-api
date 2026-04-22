# Security Policy

## Supported Versions

This project is still early-stage. Security fixes are expected to land on the latest version in the default branch.

## Reporting A Vulnerability

Do not open a public issue for sensitive security problems.

Report security issues through:

- Discord: `https://discord.gg/secrets`
- or a private channel you already use with the maintainer

Include:

- what endpoint or behavior is affected
- reproduction steps
- impact
- whether credentials, file access, or remote execution are involved

## Security Notes

This project exposes privileged remote operations.

Treat it as sensitive infrastructure:

- do not expose it directly to the public internet without access control
- place it behind a VPN, reverse proxy auth, IP allowlist, or private network boundary
- do not commit `config.json`
- use least-privilege SSH accounts whenever possible
- treat `/config`, `/system/rmrf`, and firewall routes as privileged

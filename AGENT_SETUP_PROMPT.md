# Agent Setup Prompt

Use this file when you want another AI agent to install and start `SSH ~ Api` for you.

## Copy And Paste This

```text
Set up SSH ~ Api in this repository.

Project summary:
- SSH ~ Api is an OpenAPI-first FastAPI service that gives AI agents a structured HTTP layer for SSH, SFTP, file transfer, system operations, setup helpers, tunnels, and firewall tasks on Linux servers.
- The goal is to run the API locally, verify it, and make it ready for agent use.

Your tasks:
1. Inspect the repository.
2. Create a local virtual environment if needed.
3. Install dependencies.
4. Create config.json from config.example.json if config.json does not exist.
5. Start the API locally.
6. Verify that the API responds.
7. Fetch /openapi.json.
8. Read SSH_API_GUIDE.md.
9. Report back with the base URL and the docs URLs.

Preferred setup flow:
- On Windows, run scripts/bootstrap.ps1
- On macOS/Linux, run scripts/bootstrap.sh
- If those scripts are unavailable, do the setup manually

Rules:
- Do not commit config.json
- Do not place real credentials into tracked files
- If the API is already running, verify it instead of starting a duplicate copy
- Keep the setup local to this repository

Success criteria:
- The API is running
- /docs, /redoc, and /openapi.json are reachable
- You can clearly tell me how to stop the server
- You summarize the next step for connecting the API to a VPS
```

## Expected Output From The Agent

The agent should tell you:

- where the virtual environment lives
- whether `config.json` was created
- the base URL
- the `/docs` URL
- the `/redoc` URL
- the `/openapi.json` URL
- how to stop the running server

## After Setup

Once the API is running, you can hand the next prompt to an agent:

```text
Use SSH ~ Api as your interface to the target Linux machine.
First fetch http://HOST:PORT/openapi.json.
Then read SSH_API_GUIDE.md before taking actions.
Create a session with POST /session/connect, store the returned session_id, and reuse it on later requests.
Prefer the documented command, file, system, setup, tunnel, and firewall endpoints over inventing raw SSH behavior.
Disconnect the session when the task is complete.
```

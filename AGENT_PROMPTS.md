# Agent Prompt Library

These prompts are designed for agents that will use a running `SSH ~ Api` instance.

Before using any prompt in this file, make sure the agent:

1. fetches `/openapi.json`
2. reads [`SSH_API_GUIDE.md`](./SSH_API_GUIDE.md)
3. creates an SSH session with `POST /session/connect`
4. stores the returned `session_id`

## 1. Inspect A VPS

```text
Use SSH ~ Api to inspect the target Linux server.

Workflow:
- fetch /openapi.json
- read SSH_API_GUIDE.md
- connect with POST /session/connect
- store the returned session_id
- detect the remote platform with GET /system/platform
- list processes, memory, disk, cpu, uptime, and network info
- summarize the server state in a concise report

Constraints:
- do not make changes
- use read-only endpoints and command execution only when necessary
- disconnect the session when finished
```

## 2. Deploy Files To A VPS

```text
Use SSH ~ Api to deploy files to the target Linux server.

Workflow:
- fetch /openapi.json
- read SSH_API_GUIDE.md
- connect and store session_id
- upload the requested files with the file endpoints
- verify remote file presence and permissions
- restart or reload the relevant service if asked
- return a short summary of what changed

Constraints:
- prefer structured file endpoints over raw shell commands
- do not modify unrelated files
- disconnect the session when finished
```

## 3. Diagnose A Failing Service

```text
Use SSH ~ Api to diagnose a failing Linux service.

Workflow:
- fetch /openapi.json
- read SSH_API_GUIDE.md
- connect and store session_id
- inspect the remote platform
- check service status
- inspect recent logs with command or file/system helpers
- identify the most likely root cause
- propose the minimum viable fix
- only apply a fix if explicitly instructed

Constraints:
- do not make speculative destructive changes
- explain evidence before proposing a fix
- disconnect the session when finished
```

## 4. Bootstrap A Fresh VPS

```text
Use SSH ~ Api to bootstrap a fresh Linux VPS.

Workflow:
- fetch /openapi.json
- read SSH_API_GUIDE.md
- connect and store session_id
- inspect the platform with /system/platform and /setup/platform
- install the required packages with /setup/requirements
- upload or write the requested configuration files
- enable or restart the requested services
- report every package and config change made

Constraints:
- prefer setup and system endpoints over ad hoc shell commands
- be explicit about distro-specific differences
- disconnect the session when finished
```

## 5. Create A Backup Before Changes

```text
Use SSH ~ Api to create a backup on the target Linux server before making changes.

Workflow:
- fetch /openapi.json
- read SSH_API_GUIDE.md
- connect and store session_id
- create an archive of the requested directories
- verify the archive exists
- if requested, download it or return the remote path
- only after backup succeeds, continue to the requested change

Constraints:
- do not skip verification
- do not delete the source data
- disconnect the session when finished
```

## 6. Safe Agent Operating Rules

```text
When using SSH ~ Api:
- prefer structured endpoints over raw shell commands
- store and reuse session_id
- verify the platform before distro-sensitive actions
- treat file removal, rmrf, firewall changes, and service restarts as privileged operations
- summarize completed actions and remaining risk clearly
- disconnect the session when done
```

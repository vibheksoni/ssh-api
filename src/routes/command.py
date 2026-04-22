from fastapi import APIRouter, HTTPException, Query

from ..models.command import (
    CommandRequest, CommandResponse, KeyRequest,
    BackgroundTaskRequest, BackgroundTaskResponse
)
from ..services.manager import SessionManager

router = APIRouter(prefix="/command", tags=["Commands"])
manager = SessionManager()


def _get_session(session_id: str = None):
    if session_id:
        session = manager.get_session(session_id)
    else:
        session = manager.get_default_session()
    if not session:
        raise HTTPException(status_code=404, detail="No active session")
    return session


@router.post("/exec", response_model=CommandResponse)
async def execute(req: CommandRequest, session_id: str = None) -> CommandResponse:
    """Execute command and wait for result."""
    session = _get_session(session_id)
    try:
        result = session.exec_command(req.command, req.timeout)
        return CommandResponse(
            status="completed",
            command=req.command,
            stdout=result["stdout"],
            stderr=result["stderr"],
            exit_code=result["exit_code"],
            duration_ms=result["duration_ms"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shell")
async def shell_execute(req: CommandRequest, session_id: str = None) -> dict:
    """Send command to interactive shell (non-blocking)."""
    session = _get_session(session_id)
    try:
        result = session.execute_shell(req.command)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/read")
async def read_output(
    session_id: str = None,
    timeout: float = Query(default=0.5, ge=0.1, le=30)
) -> dict:
    """Read available output from shell."""
    session = _get_session(session_id)
    output = session.read_output(timeout)
    return {"output": output, "lines": output.count("\n")}


@router.post("/key")
async def send_key(req: KeyRequest, session_id: str = None) -> dict:
    """Send special key sequence to shell."""
    session = _get_session(session_id)
    try:
        return session.send_key(req.key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/background")
async def background_task(req: BackgroundTaskRequest, session_id: str = None) -> dict:
    """Execute command in background."""
    session = _get_session(session_id)
    task_id = session.execute_background(req.command, req.task_name)
    return {"task_id": task_id, "status": "started"}


@router.get("/task/{task_id}")
async def get_task(task_id: str, session_id: str = None) -> dict:
    """Get background task status."""
    session = _get_session(session_id)
    task = session.background_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, **task}


@router.get("/run")
async def run_command(
    cmd: str = Query(..., description="Command to execute"),
    timeout: int = Query(default=30, ge=1, le=600),
    session_id: str = None
) -> dict:
    """
    Execute command via GET request.
    Avoids JSON escaping issues for complex commands.
    """
    session = _get_session(session_id)
    try:
        result = session.exec_command(cmd, timeout)
        return {
            "status": "completed",
            "command": cmd,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"],
            "duration_ms": result["duration_ms"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

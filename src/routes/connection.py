import time
from fastapi import APIRouter, HTTPException
from pathlib import Path

from ..models.connection import ConnectionRequest, ConnectionResponse
from ..services.manager import SessionManager
from ..core.config import ConfigManager
from ..core.logger import Logger

router = APIRouter(prefix="/session", tags=["Connection"])
manager = SessionManager()
config_path = Path(__file__).parent.parent.parent / "config.json"
config = ConfigManager(str(config_path))
log = Logger("connection", config)


@router.post("/connect", response_model=ConnectionResponse)
async def connect(req: ConnectionRequest = None) -> ConnectionResponse:
    """
    Establish SSH connection to remote server.
    Uses config defaults if parameters not provided.
    Supports retry with exponential backoff.
    """
    if req is None:
        req = ConnectionRequest()

    host = req.host or config.get("auth.default_host")
    port = req.port or config.get("ssh.default_port", 22)
    username = req.username or config.get("auth.default_username")
    password = req.password or config.get("auth.default_password")
    key_path = req.key_path or config.get("auth.default_key_path")
    key_passphrase = req.key_passphrase or config.get("auth.default_key_passphrase")

    if not host:
        raise HTTPException(status_code=400, detail="Host required")
    if not username:
        raise HTTPException(status_code=400, detail="Username required")

    session = manager.create_session()
    last_error = None
    delay = req.retry_delay

    for attempt in range(1, req.retries + 1):
        try:
            log.info(f"Connection attempt {attempt}/{req.retries} to {host}:{port}")
            session.connect(
                host=host,
                port=port,
                username=username,
                password=password,
                key_path=key_path if key_path else None,
                key_passphrase=key_passphrase if key_passphrase else None,
                key_content=req.key_content,
                use_agent=req.use_agent,
                keepalive=req.keepalive
            )
            return ConnectionResponse(
                status="connected",
                session_id=session.session_id,
                host=host,
                username=username,
                features=["sftp", "shell", "exec", "background_tasks", "tunnels"]
            )
        except Exception as e:
            last_error = e
            log.warning(f"Attempt {attempt} failed: {e}")
            if attempt < req.retries:
                time.sleep(delay)
                delay *= 2

    manager.remove_session(session.session_id)
    raise HTTPException(status_code=500, detail=f"Connection failed after {req.retries} attempts: {last_error}")


@router.post("/disconnect/{session_id}")
async def disconnect(session_id: str) -> dict:
    """Disconnect and remove SSH session."""
    if manager.remove_session(session_id):
        return {"status": "disconnected", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/status/{session_id}")
async def status(session_id: str) -> dict:
    """Get session connection status."""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "connected": session.connected,
        "host": session.host,
        "username": session.username
    }


@router.get("/list")
async def list_sessions() -> dict:
    """List all active sessions."""
    return {"sessions": manager.list_sessions()}

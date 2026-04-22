from fastapi import APIRouter, HTTPException

from ..models.tunnel import (
    LocalForwardRequest, RemoteForwardRequest, TunnelInfo
)
from ..services.manager import SessionManager

router = APIRouter(prefix="/tunnel", tags=["Tunnels"])
manager = SessionManager()


def _get_tunnel_manager(session_id: str = None):
    if session_id:
        session = manager.get_session(session_id)
    else:
        session = manager.get_default_session()
    if not session or not session.tunnel_manager:
        raise HTTPException(status_code=404, detail="No active session")
    return session.tunnel_manager


@router.post("/local")
async def create_local_forward(
    req: LocalForwardRequest, session_id: str = None
) -> dict:
    """Create local port forward (SSH -L)."""
    tm = _get_tunnel_manager(session_id)
    try:
        tunnel_id = tm.create_local_forward(
            req.local_port, req.remote_host, req.remote_port, req.bind_address
        )
        return {"tunnel_id": tunnel_id, "status": "active", "type": "local"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remote")
async def create_remote_forward(
    req: RemoteForwardRequest, session_id: str = None
) -> dict:
    """Create remote port forward (SSH -R)."""
    tm = _get_tunnel_manager(session_id)
    try:
        tunnel_id = tm.create_remote_forward(
            req.remote_port, req.local_host, req.local_port, req.bind_address
        )
        return {"tunnel_id": tunnel_id, "status": "active", "type": "remote"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_tunnels(session_id: str = None) -> dict:
    """List all active tunnels."""
    tm = _get_tunnel_manager(session_id)
    tunnels = tm.list_tunnels()
    return {"tunnels": tunnels, "count": len(tunnels)}


@router.delete("/{tunnel_id}")
async def close_tunnel(tunnel_id: str, session_id: str = None) -> dict:
    """Close a specific tunnel."""
    tm = _get_tunnel_manager(session_id)
    if tm.close_tunnel(tunnel_id):
        return {"status": "closed", "tunnel_id": tunnel_id}
    raise HTTPException(status_code=404, detail="Tunnel not found")


@router.delete("/")
async def close_all_tunnels(session_id: str = None) -> dict:
    """Close all tunnels."""
    tm = _get_tunnel_manager(session_id)
    count = tm.close_all()
    return {"status": "closed", "count": count}

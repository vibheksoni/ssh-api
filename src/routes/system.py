from fastapi import APIRouter, HTTPException, Query

from ..models.system import (
    KillProcessRequest, ServiceRequest, GrepRequest,
    FindRequest, ArchiveRequest, ExtractRequest, CronJob, EnvVarRequest
)
from ..services.manager import SessionManager
from ..services.system import SystemService

router = APIRouter(prefix="/system", tags=["System"])
manager = SessionManager()


def _get_system(session_id: str = None) -> SystemService:
    if session_id:
        session = manager.get_session(session_id)
    else:
        session = manager.get_default_session()
    if not session:
        raise HTTPException(status_code=404, detail="No active session")
    return SystemService(session.exec_command)


@router.get("/processes")
async def list_processes(
    session_id: str = None, user: str = Query(default=None)
) -> dict:
    """List running processes."""
    sys = _get_system(session_id)
    processes = sys.list_processes(user)
    return {"processes": processes, "count": len(processes)}


@router.post("/kill")
async def kill_process(req: KillProcessRequest, session_id: str = None) -> dict:
    """Kill a process by PID."""
    sys = _get_system(session_id)
    return sys.kill_process(req.pid, req.signal)


@router.get("/disk")
async def get_disk_usage(session_id: str = None) -> dict:
    """Get disk usage info."""
    sys = _get_system(session_id)
    return {"disks": sys.get_disk_usage()}


@router.get("/memory")
async def get_memory_info(session_id: str = None) -> dict:
    """Get memory usage info."""
    sys = _get_system(session_id)
    return {"memory": sys.get_memory_info()}


@router.get("/cpu")
async def get_cpu_info(session_id: str = None) -> dict:
    """Get CPU info and load."""
    sys = _get_system(session_id)
    return {"cpu": sys.get_cpu_info()}


@router.get("/network")
async def get_network_info(session_id: str = None) -> dict:
    """Get network interfaces."""
    sys = _get_system(session_id)
    return {"interfaces": sys.get_network_interfaces()}


@router.get("/platform")
async def get_platform_info(session_id: str = None) -> dict:
    """Detect remote Linux platform capabilities."""
    sys = _get_system(session_id)
    return {"platform": sys.get_platform_info()}


@router.post("/service")
async def manage_service(req: ServiceRequest, session_id: str = None) -> dict:
    """Manage systemd service."""
    sys = _get_system(session_id)
    return sys.manage_service(req.service, req.action)


@router.post("/grep")
async def grep_files(req: GrepRequest, session_id: str = None) -> dict:
    """Search for pattern in files."""
    sys = _get_system(session_id)
    matches = sys.grep(req.pattern, req.path, req.recursive, req.ignore_case, req.max_results)
    return {"matches": matches, "count": len(matches)}


@router.post("/find")
async def find_files(req: FindRequest, session_id: str = None) -> dict:
    """Find files matching criteria."""
    sys = _get_system(session_id)
    files = sys.find_files(req.path, req.name, req.type, req.max_depth, req.max_results)
    return {"files": files, "count": len(files)}


@router.post("/archive")
async def create_archive(req: ArchiveRequest, session_id: str = None) -> dict:
    """Create archive from source."""
    sys = _get_system(session_id)
    return sys.create_archive(req.source, req.destination, req.format)


@router.post("/extract")
async def extract_archive(req: ExtractRequest, session_id: str = None) -> dict:
    """Extract archive to destination."""
    sys = _get_system(session_id)
    return sys.extract_archive(req.archive, req.destination)


@router.get("/env/{name}")
async def get_env_var(name: str, session_id: str = None) -> dict:
    """Get environment variable."""
    sys = _get_system(session_id)
    value = sys.get_env_var(name)
    return {"name": name, "value": value}


@router.post("/env")
async def set_env_var(req: EnvVarRequest, session_id: str = None) -> dict:
    """Set environment variable."""
    sys = _get_system(session_id)
    return sys.set_env_var(req.name, req.value, req.persist)


@router.get("/cron")
async def list_cron_jobs(session_id: str = None, user: str = None) -> dict:
    """List cron jobs."""
    sys = _get_system(session_id)
    jobs = sys.list_cron_jobs(user)
    return {"jobs": jobs, "count": len(jobs)}


@router.post("/cron")
async def add_cron_job(req: CronJob, session_id: str = None) -> dict:
    """Add cron job."""
    sys = _get_system(session_id)
    return sys.add_cron_job(req.schedule, req.command)


@router.get("/users")
async def list_users(session_id: str = None) -> dict:
    """List system users."""
    sys = _get_system(session_id)
    users = sys.list_users()
    return {"users": users, "count": len(users)}


@router.post("/chmod")
async def chmod_file(
    path: str, mode: str, recursive: bool = False, session_id: str = None
) -> dict:
    """Change file permissions."""
    sys = _get_system(session_id)
    return sys.chmod(path, mode, recursive)


@router.post("/chown")
async def chown_file(
    path: str, owner: str, group: str = None, recursive: bool = False,
    session_id: str = None
) -> dict:
    """Change file ownership."""
    sys = _get_system(session_id)
    return sys.chown(path, owner, group, recursive)


@router.get("/tail")
async def tail_file(
    path: str, lines: int = Query(default=100, ge=1, le=10000),
    session_id: str = None
) -> dict:
    """Get last N lines of file."""
    sys = _get_system(session_id)
    content = sys.tail_file(path, lines)
    return {"path": path, "content": content}


@router.get("/head")
async def head_file(
    path: str, lines: int = Query(default=100, ge=1, le=10000),
    session_id: str = None
) -> dict:
    """Get first N lines of file."""
    sys = _get_system(session_id)
    content = sys.head_file(path, lines)
    return {"path": path, "content": content}


@router.get("/uptime")
async def get_uptime(session_id: str = None) -> dict:
    """Get system uptime."""
    sys = _get_system(session_id)
    return sys.get_uptime()


@router.delete("/rmrf")
async def rm_rf(path: str, session_id: str = None) -> dict:
    """
    Fast recursive delete using rm -rf.
    Much faster than SFTP for large directories.
    """
    sys = _get_system(session_id)
    return sys.rm_rf(path)

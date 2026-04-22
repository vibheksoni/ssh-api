from fastapi import APIRouter, HTTPException

from ..models.file import (
    FileUploadRequest, FileDownloadRequest, FileResponse,
    DirectoryRequest, FindFilesRequest, TailFileRequest, FileEditRequest
)
from ..services.manager import SessionManager
from ..services.sftp import SFTPService

router = APIRouter(prefix="/file", tags=["Files"])
manager = SessionManager()


def _get_sftp(session_id: str = None) -> SFTPService:
    if session_id:
        session = manager.get_session(session_id)
    else:
        session = manager.get_default_session()
    if not session or not session.sftp:
        raise HTTPException(status_code=404, detail="No active SFTP session")
    return SFTPService(session.sftp)


@router.post("/upload", response_model=FileResponse)
async def upload(req: FileUploadRequest, session_id: str = None) -> FileResponse:
    """Upload file to remote server."""
    sftp = _get_sftp(session_id)
    try:
        result = sftp.upload_file(
            req.remote_path, req.local_path, req.content, req.raw_content, req.permissions
        )
        return FileResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download(req: FileDownloadRequest, session_id: str = None) -> dict:
    """Download file from remote server."""
    sftp = _get_sftp(session_id)
    try:
        return sftp.download_file(req.remote_path, req.local_path, req.return_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_dir(path: str = ".", session_id: str = None) -> dict:
    """List directory contents."""
    sftp = _get_sftp(session_id)
    try:
        items = sftp.list_directory(path)
        return {"path": path, "items": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mkdir")
async def mkdir(path: str, session_id: str = None) -> dict:
    """Create directory on remote server."""
    sftp = _get_sftp(session_id)
    try:
        return sftp.mkdir(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/remove")
async def remove(path: str, session_id: str = None) -> dict:
    """Remove file from remote server."""
    sftp = _get_sftp(session_id)
    try:
        return sftp.remove(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stat")
async def stat(path: str, session_id: str = None) -> dict:
    """Get file statistics."""
    sftp = _get_sftp(session_id)
    try:
        return sftp.stat(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/read")
async def read_file(path: str, session_id: str = None) -> dict:
    """Read file content."""
    sftp = _get_sftp(session_id)
    try:
        content = sftp.read_file(path)
        return {"path": path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/write")
async def write_file(req: FileEditRequest, session_id: str = None) -> dict:
    """Write content to file."""
    sftp = _get_sftp(session_id)
    try:
        return sftp.write_file(req.path, req.content, req.mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/copy")
async def copy_recursive(src: str, dst: str, session_id: str = None) -> dict:
    """Copy directory recursively."""
    sftp = _get_sftp(session_id)
    try:
        return sftp.copy_recursive(src, dst)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rmdir")
async def rmdir_recursive(path: str, session_id: str = None) -> dict:
    """Remove directory recursively."""
    sftp = _get_sftp(session_id)
    try:
        return sftp.rmdir_recursive(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

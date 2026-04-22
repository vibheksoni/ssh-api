from typing import List, Optional
from pydantic import BaseModel, Field


class FileUploadRequest(BaseModel):
    remote_path: str = Field(..., min_length=1)
    content: Optional[str] = Field(default=None, description="Base64 encoded")
    raw_content: Optional[str] = Field(default=None, description="Plain text content")
    local_path: Optional[str] = None
    permissions: Optional[int] = None


class FileDownloadRequest(BaseModel):
    remote_path: str = Field(..., min_length=1)
    local_path: Optional[str] = None
    return_content: bool = Field(default=False)


class FileResponse(BaseModel):
    status: str
    path: str
    size: Optional[int] = None
    content: Optional[str] = None


class DirectoryRequest(BaseModel):
    remote_dir: str = Field(..., min_length=1)
    local_dir: Optional[str] = None


class FindFilesRequest(BaseModel):
    path: str = Field(default=".")
    pattern: Optional[str] = None
    file_type: Optional[str] = Field(default=None, pattern="^(file|directory)$")
    modified_since: Optional[str] = None


class TailFileRequest(BaseModel):
    file_path: str = Field(..., min_length=1)
    lines: int = Field(default=100, ge=1, le=10000)
    follow: bool = Field(default=False)


class FileEditRequest(BaseModel):
    path: str = Field(..., min_length=1)
    content: str = Field(..., description="Content to write (plain text)")
    mode: str = Field(default="overwrite", pattern="^(overwrite|append|prepend)$")

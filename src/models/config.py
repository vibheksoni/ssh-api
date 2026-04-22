from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConfigUpdateRequest(BaseModel):
    key: str = Field(..., min_length=1)
    value: Any


class ConfigResponse(BaseModel):
    config: Dict[str, Any]


class ArchiveRequest(BaseModel):
    paths: List[str] = Field(..., min_length=1)
    archive_path: str = Field(..., min_length=1)
    archive_type: str = Field(default="tar.gz", pattern="^(tar\\.gz|zip|tar)$")


class ExtractRequest(BaseModel):
    archive_path: str = Field(..., min_length=1)
    extract_to: Optional[str] = None


class GitCommandRequest(BaseModel):
    repo_path: str = Field(default=".")
    command: str = Field(..., min_length=1)


class BulkFileItem(BaseModel):
    remote_path: str
    local_path: Optional[str] = None
    content: Optional[str] = None
    return_content: bool = False


class BulkOperationRequest(BaseModel):
    files: List[BulkFileItem] = Field(..., min_length=1)

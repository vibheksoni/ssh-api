from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CommandRequest(BaseModel):
    command: str = Field(..., min_length=1)
    timeout: float = Field(default=30.0, ge=0.1, le=3600)
    get_exit_code: bool = Field(default=True)


class CommandResponse(BaseModel):
    status: str
    command: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    duration_ms: Optional[float] = None


class KeyRequest(BaseModel):
    key: str = Field(..., min_length=1)


class BackgroundTaskRequest(BaseModel):
    command: str = Field(..., min_length=1)
    task_name: Optional[str] = None


class BackgroundTaskResponse(BaseModel):
    task_id: str
    status: str
    command: str
    output: List[str] = []
    error: List[str] = []
    start_time: Optional[float] = None
    end_time: Optional[float] = None

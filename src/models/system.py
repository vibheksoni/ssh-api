from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ProcessInfo(BaseModel):
    pid: str
    user: str
    cpu: str
    mem: str
    command: str


class ProcessListResponse(BaseModel):
    processes: List[ProcessInfo]
    count: int


class KillProcessRequest(BaseModel):
    pid: str = Field(..., min_length=1)
    signal: str = Field(default="TERM", pattern="^(TERM|KILL|HUP|INT)$")


class ServiceRequest(BaseModel):
    service: str = Field(..., min_length=1)
    action: str = Field(..., pattern="^(start|stop|restart|status|enable|disable)$")


class SystemStats(BaseModel):
    cpu: Optional[float] = None
    mem: Optional[float] = None
    disk: Optional[float] = None
    timestamp: float


class DiskInfo(BaseModel):
    filesystem: str
    size: str
    used: str
    available: str
    use_percent: str
    mount: str


class MemoryInfo(BaseModel):
    total: int
    used: int
    free: int
    available: int
    use_percent: float


class CpuInfo(BaseModel):
    model: str
    cores: int
    threads: int
    load_1m: float
    load_5m: float
    load_15m: float


class NetworkInterface(BaseModel):
    name: str
    ip: Optional[str] = None
    mac: Optional[str] = None
    rx_bytes: int = 0
    tx_bytes: int = 0
    status: str = "unknown"


class GrepRequest(BaseModel):
    pattern: str = Field(..., min_length=1)
    path: str = Field(default=".")
    recursive: bool = Field(default=True)
    ignore_case: bool = Field(default=False)
    max_results: int = Field(default=100, ge=1, le=1000)


class FindRequest(BaseModel):
    path: str = Field(default=".")
    name: Optional[str] = None
    type: Optional[str] = Field(default=None, pattern="^(f|d|l)?$")
    max_depth: Optional[int] = Field(default=None, ge=1, le=20)
    size: Optional[str] = None
    mtime: Optional[str] = None
    max_results: int = Field(default=100, ge=1, le=1000)


class ArchiveRequest(BaseModel):
    source: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    format: str = Field(default="tar.gz", pattern="^(tar|tar.gz|tar.bz2|zip)$")


class ExtractRequest(BaseModel):
    archive: str = Field(..., min_length=1)
    destination: str = Field(default=".")


class CronJob(BaseModel):
    schedule: str = Field(..., min_length=9)
    command: str = Field(..., min_length=1)
    user: Optional[str] = None


class EnvVarRequest(BaseModel):
    name: str = Field(..., min_length=1, pattern="^[A-Za-z_][A-Za-z0-9_]*$")
    value: Optional[str] = None
    persist: bool = Field(default=False)

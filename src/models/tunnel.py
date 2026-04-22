from typing import Optional
from pydantic import BaseModel, Field


class LocalForwardRequest(BaseModel):
    local_port: int = Field(..., ge=1, le=65535)
    remote_host: str = Field(..., min_length=1)
    remote_port: int = Field(..., ge=1, le=65535)
    bind_address: str = Field(default="127.0.0.1")


class RemoteForwardRequest(BaseModel):
    remote_port: int = Field(..., ge=1, le=65535)
    local_host: str = Field(default="127.0.0.1")
    local_port: int = Field(..., ge=1, le=65535)
    bind_address: str = Field(default="0.0.0.0")


class DynamicForwardRequest(BaseModel):
    local_port: int = Field(..., ge=1, le=65535)
    bind_address: str = Field(default="127.0.0.1")


class TunnelInfo(BaseModel):
    tunnel_id: str
    tunnel_type: str
    local_port: int
    remote_host: Optional[str] = None
    remote_port: Optional[int] = None
    status: str

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuthMethod(str, Enum):
    PASSWORD = "password"
    KEY = "key"
    AGENT = "agent"


class ConnectionRequest(BaseModel):
    host: Optional[str] = Field(default=None, description="SSH server hostname or IP")
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    key_path: Optional[str] = Field(default=None)
    key_passphrase: Optional[str] = Field(default=None)
    key_content: Optional[str] = Field(default=None, description="Base64 encoded key")
    use_agent: bool = Field(default=False)
    keepalive: bool = Field(default=True)
    retries: int = Field(default=3, ge=1, le=10, description="Connection retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, le=30.0, description="Initial delay between retries")


class ConnectionResponse(BaseModel):
    status: str
    session_id: str
    host: str
    username: str
    features: List[str]

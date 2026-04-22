from typing import Any
from fastapi import APIRouter, HTTPException

from ..core.config import ConfigManager
from ..models.config import ConfigUpdateRequest

router = APIRouter(prefix="/config", tags=["Configuration"])
config = ConfigManager()


@router.get("/")
async def get_config() -> dict:
    """Get full configuration."""
    return {"config": config.get_all()}


@router.get("/{key:path}")
async def get_config_key(key: str) -> dict:
    """Get specific config value by dot-notation key."""
    value = config.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    return {"key": key, "value": value}


@router.put("/")
async def set_config(req: ConfigUpdateRequest) -> dict:
    """Set config value by dot-notation key."""
    config.set(req.key, req.value)
    return {"status": "updated", "key": req.key, "value": req.value}


@router.post("/reload")
async def reload_config() -> dict:
    """Reload configuration from file."""
    config.reload()
    return {"status": "reloaded"}

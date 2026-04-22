from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import ConfigManager
from .core.logger import Logger

config_path = Path(__file__).parent.parent / "config.json"
config = ConfigManager(str(config_path))
log = Logger("main", config)

app = FastAPI(
    title="SSH API Service",
    description="Enhanced SSH API with FastAPI",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

from .routes import connection, command, file, config as config_routes, tunnel, system, setup, firewall

app.include_router(connection.router)
app.include_router(command.router)
app.include_router(file.router)
app.include_router(config_routes.router)
app.include_router(tunnel.router)
app.include_router(system.router)
app.include_router(setup.router)
app.include_router(firewall.router)


@app.get("/", tags=["Health"])
async def root() -> dict:
    """API health check and info."""
    return {
        "service": "SSH API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.on_event("startup")
async def startup():
    log.info("SSH API Service starting...")
    log.info(f"Docs available at /docs")


@app.on_event("shutdown")
async def shutdown():
    log.info("SSH API Service shutting down...")

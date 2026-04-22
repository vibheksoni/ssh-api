#!/usr/bin/env python3
from pathlib import Path

import uvicorn

from src.core.config import ConfigManager

config_path = Path(__file__).parent / "config.json"
config = ConfigManager(str(config_path))


def main() -> None:
    host = config.get("server.host", "0.0.0.0")
    port = config.get("server.port", 8754)
    debug = config.get("server.debug", False)

    print(f"Starting SSH API on http://{host}:{port}")
    print(f"Docs: http://{host}:{port}/docs")
    print(f"OpenAPI: http://{host}:{port}/openapi.json")

    uvicorn.run("src.app:app", host=host, port=port, reload=debug)


if __name__ == "__main__":
    main()

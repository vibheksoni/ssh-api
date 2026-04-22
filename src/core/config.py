import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """
    Thread-safe configuration manager with file persistence.

    Args:
        config_path: Path to the JSON configuration file.
    """

    _instance: Optional["ConfigManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, config_path: Optional[str] = None) -> "ConfigManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None) -> None:
        if self._initialized:
            return
        self._config_path = Path(config_path) if config_path else Path("config.json")
        self._config: Dict[str, Any] = {}
        self._rw_lock = threading.RLock()
        self._load_config()
        self._initialized = True

    def _load_config(self) -> None:
        with self._rw_lock:
            if self._config_path.exists():
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            else:
                self._config = self._get_defaults()
                self._save_config()

    def _save_config(self) -> None:
        with self._rw_lock:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)

    def _get_defaults(self) -> Dict[str, Any]:
        return {
            "server": {"host": "0.0.0.0", "port": 8754, "debug": False},
            "ssh": {
                "default_port": 22,
                "timeout": 30,
                "banner_timeout": 15,
                "auth_timeout": 30,
                "keepalive_interval": 60,
                "max_concurrent_connections": 10
            },
            "auth": {
                "default_host": "",
                "default_username": "",
                "default_password": "",
                "default_key_path": "",
                "default_key_passphrase": ""
            },
            "sftp": {"chunk_size": 32768, "max_file_size_mb": 500, "temp_directory": "/tmp"},
            "security": {
                "disabled_algorithms": {"ciphers": ["3des-cbc"], "macs": ["hmac-md5"]},
                "reject_unknown_hosts": False
            },
            "logging": {"level": "INFO", "directory": "ssh-service-logs"}
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation key.

        Args:
            key: Dot-notation key (e.g., "ssh.timeout").
            default: Default value if key not found.
        Returns:
            Configuration value or default.
        """
        with self._rw_lock:
            keys = key.split(".")
            value = self._config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by dot-notation key.

        Args:
            key: Dot-notation key (e.g., "ssh.timeout").
            value: Value to set.
        """
        with self._rw_lock:
            keys = key.split(".")
            config = self._config
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            config[keys[-1]] = value
            self._save_config()

    def get_all(self) -> Dict[str, Any]:
        """
        Get entire configuration dictionary.

        Returns:
            Copy of the configuration dictionary.
        """
        with self._rw_lock:
            return self._config.copy()

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()

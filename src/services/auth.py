import io
import base64
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import paramiko

from ..core.config import ConfigManager
from ..core.logger import Logger


class SSHAuthenticator:
    """
    Unified SSH authentication handler supporting password, key file, and agent.

    Args:
        config: ConfigManager instance for default settings.
    """

    def __init__(self, config: Optional[ConfigManager] = None) -> None:
        self._config = config or ConfigManager()
        self._log = Logger("ssh_auth", self._config)

    def authenticate(
        self,
        client: paramiko.SSHClient,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        key_passphrase: Optional[str] = None,
        key_content: Optional[str] = None,
        use_agent: bool = False
    ) -> None:
        """
        Authenticate SSH client using available credentials.

        Args:
            client: Paramiko SSHClient instance.
            host: SSH server hostname.
            port: SSH server port.
            username: SSH username.
            password: Optional password for auth or key decryption.
            key_path: Optional path to private key file.
            key_passphrase: Optional passphrase for encrypted key.
            key_content: Optional base64-encoded private key.
            use_agent: Whether to use SSH agent.
        Raises:
            paramiko.AuthenticationException: If all auth methods fail.
        """
        timeout = self._config.get("ssh.timeout", 30)
        banner_timeout = self._config.get("ssh.banner_timeout", 15)
        auth_timeout = self._config.get("ssh.auth_timeout", 30)
        disabled_algs = self._config.get("security.disabled_algorithms", {})

        try:
            client.load_system_host_keys()
        except Exception as exc:
            self._log.debug(f"Unable to load system host keys: {exc}")

        pkey = self._load_private_key(key_path, key_content, key_passphrase or password)

        connect_kwargs = {
            "hostname": host,
            "port": port,
            "username": username,
            "timeout": timeout,
            "banner_timeout": banner_timeout,
            "auth_timeout": auth_timeout,
            "allow_agent": use_agent,
            "look_for_keys": False,
            "disabled_algorithms": disabled_algs
        }

        if pkey:
            connect_kwargs["pkey"] = pkey
            self._log.info(f"Authenticating with private key to {host}:{port}")
        elif password:
            connect_kwargs["password"] = password
            self._log.info(f"Authenticating with password to {host}:{port}")
        elif use_agent:
            connect_kwargs["allow_agent"] = True
            self._log.info(f"Authenticating with SSH agent to {host}:{port}")

        client.connect(**connect_kwargs)
        self._log.info(f"Successfully authenticated to {host}:{port}")

    def _load_private_key(
        self,
        key_path: Optional[str],
        key_content: Optional[str],
        passphrase: Optional[str]
    ) -> Optional[paramiko.PKey]:
        """
        Load private key from file path or base64 content.

        Args:
            key_path: Path to private key file.
            key_content: Base64-encoded private key.
            passphrase: Passphrase for encrypted key.
        Returns:
            Paramiko PKey object or None.
        """
        if key_content:
            return self._load_key_from_content(key_content, passphrase)
        if key_path and Path(key_path).exists():
            return self._load_key_from_file(key_path, passphrase)
        return None

    def _load_key_from_file(
        self, path: str, passphrase: Optional[str]
    ) -> Optional[paramiko.PKey]:
        """
        Auto-detect and load key from file.

        Args:
            path: Path to private key file.
            passphrase: Optional passphrase.
        Returns:
            Paramiko PKey object.
        """
        key_classes = [
            paramiko.Ed25519Key,
            paramiko.ECDSAKey,
            paramiko.RSAKey
        ]
        for key_class in key_classes:
            try:
                return key_class.from_private_key_file(path, password=passphrase)
            except paramiko.SSHException:
                continue
        raise paramiko.SSHException(f"Unable to load key from {path}")

    def _load_key_from_content(
        self, content: str, passphrase: Optional[str]
    ) -> Optional[paramiko.PKey]:
        """
        Auto-detect and load key from base64 content.

        Args:
            content: Base64-encoded private key.
            passphrase: Optional passphrase.
        Returns:
            Paramiko PKey object.
        """
        decoded = base64.b64decode(content)
        key_file = io.StringIO(decoded.decode("utf-8"))
        key_classes = [
            paramiko.Ed25519Key,
            paramiko.ECDSAKey,
            paramiko.RSAKey
        ]
        for key_class in key_classes:
            try:
                key_file.seek(0)
                return key_class.from_private_key(key_file, password=passphrase)
            except paramiko.SSHException:
                continue
        raise paramiko.SSHException("Unable to load key from content")

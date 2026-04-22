import uuid
import threading
from typing import Dict, Optional

from ..core.config import ConfigManager
from ..core.logger import Logger
from .session import SSHSession


class SessionManager:
    """
    Singleton manager for multiple SSH sessions.

    Args:
        config: ConfigManager instance.
    """

    _instance: Optional["SessionManager"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, config: Optional[ConfigManager] = None) -> "SessionManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[ConfigManager] = None) -> None:
        if self._initialized:
            return
        self._config = config or ConfigManager()
        self._log = Logger("session_manager", self._config)
        self._sessions: Dict[str, SSHSession] = {}
        self._rw_lock = threading.RLock()
        self._initialized = True

    def create_session(self) -> SSHSession:
        """
        Create new SSH session.

        Returns:
            New SSHSession instance.
        """
        with self._rw_lock:
            session_id = uuid.uuid4().hex[:12]
            session = SSHSession(session_id, self._config)
            self._sessions[session_id] = session
            self._log.info(f"Created session {session_id}")
            return session

    def get_session(self, session_id: str) -> Optional[SSHSession]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier.
        Returns:
            SSHSession or None.
        """
        with self._rw_lock:
            return self._sessions.get(session_id)

    def remove_session(self, session_id: str) -> bool:
        """
        Remove and disconnect session.

        Args:
            session_id: Session identifier.
        Returns:
            True if removed.
        """
        with self._rw_lock:
            session = self._sessions.pop(session_id, None)
            if session:
                session.disconnect()
                self._log.info(f"Removed session {session_id}")
                return True
            return False

    def get_default_session(self) -> Optional[SSHSession]:
        """
        Get first available session.

        Returns:
            First SSHSession or None.
        """
        with self._rw_lock:
            for session in self._sessions.values():
                if session.connected:
                    return session
            return None

    def list_sessions(self) -> Dict[str, dict]:
        """
        List all sessions with status.

        Returns:
            Dict of session info.
        """
        with self._rw_lock:
            return {
                sid: {
                    "connected": s.connected,
                    "host": s.host,
                    "username": s.username
                }
                for sid, s in self._sessions.items()
            }

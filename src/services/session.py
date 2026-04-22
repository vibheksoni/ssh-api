import queue
import threading
import time
import uuid
from typing import Any, Dict, Optional

import paramiko

from ..core.config import ConfigManager
from ..core.logger import Logger
from .auth import SSHAuthenticator
from .tunnel import TunnelManager


class SSHSession:
    """
    SSH session wrapper with shell, SFTP, and command execution.

    Args:
        session_id: Unique session identifier.
        config: ConfigManager instance.
    """

    def __init__(
        self, session_id: str, config: Optional[ConfigManager] = None
    ) -> None:
        self.session_id = session_id
        self._config = config or ConfigManager()
        self._log = Logger("ssh_session", self._config)
        self._auth = SSHAuthenticator(self._config)

        self.client: Optional[paramiko.SSHClient] = None
        self.transport: Optional[paramiko.Transport] = None
        self.shell: Optional[paramiko.Channel] = None
        self.sftp: Optional[paramiko.SFTPClient] = None
        self.tunnel_manager: Optional[TunnelManager] = None

        self._output_queue: queue.Queue = queue.Queue()
        self._reader_thread: Optional[threading.Thread] = None
        self._connected: bool = False
        self._lock = threading.Lock()

        self.host: str = ""
        self.username: str = ""
        self.background_tasks: Dict[str, Dict[str, Any]] = {}

    @property
    def connected(self) -> bool:
        return self._connected and self.client is not None

    def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        key_passphrase: Optional[str] = None,
        key_content: Optional[str] = None,
        use_agent: bool = False,
        keepalive: bool = True
    ) -> None:
        """
        Establish SSH connection with unified authentication.

        Args:
            host: SSH server hostname.
            port: SSH server port.
            username: SSH username.
            password: Optional password.
            key_path: Optional path to private key.
            key_passphrase: Optional key passphrase.
            key_content: Optional base64-encoded key.
            use_agent: Use SSH agent.
            keepalive: Enable keepalive packets.
        """
        with self._lock:
            self.host = host
            self.username = username

            self.client = paramiko.SSHClient()
            reject_unknown = self._config.get("security.reject_unknown_hosts", False)
            if reject_unknown:
                self.client.set_missing_host_key_policy(paramiko.RejectPolicy())
            else:
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self._auth.authenticate(
                self.client, host, port, username,
                password, key_path, key_passphrase, key_content, use_agent
            )

            self.transport = self.client.get_transport()
            if keepalive:
                interval = self._config.get("ssh.keepalive_interval", 60)
                self.transport.set_keepalive(interval)

            self.shell = self.client.invoke_shell()
            self.shell.settimeout(0.1)
            self.sftp = self.client.open_sftp()
            self.tunnel_manager = TunnelManager(self.transport, self._config)

            self._connected = True
            self._start_reader_thread()
            time.sleep(0.5)
            self._clear_output_queue()
            self._log.info(f"Session {self.session_id} connected to {host}")

    def _start_reader_thread(self) -> None:
        self._reader_thread = threading.Thread(target=self._read_output_loop)
        self._reader_thread.daemon = True
        self._reader_thread.start()

    def _read_output_loop(self) -> None:
        buffer = ""
        while self._connected:
            try:
                if self.shell and self.shell.recv_ready():
                    chunk = self.shell.recv(4096).decode("utf-8", errors="ignore")
                    buffer += chunk
                    lines = buffer.split("\n")
                    for line in lines[:-1]:
                        self._output_queue.put(line + "\n")
                    buffer = lines[-1]
                else:
                    time.sleep(0.01)
            except Exception:
                time.sleep(0.1)

    def _clear_output_queue(self) -> None:
        while not self._output_queue.empty():
            try:
                self._output_queue.get_nowait()
            except queue.Empty:
                break

    def disconnect(self) -> None:
        """Close SSH connection and cleanup resources."""
        with self._lock:
            self._connected = False
            if self.tunnel_manager:
                self.tunnel_manager.close_all()
                self.tunnel_manager = None
            if self.sftp:
                self.sftp.close()
                self.sftp = None
            if self.shell:
                self.shell.close()
                self.shell = None
            if self.client:
                self.client.close()
                self.client = None
            self.transport = None
            self._log.info(f"Session {self.session_id} disconnected")

    def execute_shell(self, command: str) -> Dict[str, Any]:
        """
        Send command to interactive shell.

        Args:
            command: Command to execute.
        Returns:
            Status dict with command sent confirmation.
        """
        if not self._connected or not self.shell:
            raise RuntimeError("Not connected")
        self._clear_output_queue()
        self.shell.send(command + "\n")
        return {"status": "sent", "command": command}

    def exec_command(
        self, command: str, timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Execute command and wait for result.

        Args:
            command: Command to execute.
            timeout: Execution timeout in seconds.
        Returns:
            Dict with stdout, stderr, exit_code.
        """
        if not self._connected or not self.client:
            raise RuntimeError("Not connected")
        start = time.time()
        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        duration = (time.time() - start) * 1000
        return {
            "stdout": stdout.read().decode("utf-8", errors="ignore"),
            "stderr": stderr.read().decode("utf-8", errors="ignore"),
            "exit_code": exit_code,
            "duration_ms": duration
        }

    def read_output(self, timeout: float = 0.5) -> str:
        """
        Read available output from shell.

        Args:
            timeout: Max time to wait for output.
        Returns:
            Collected output string.
        """
        output = []
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                line = self._output_queue.get(timeout=0.1)
                output.append(line)
            except queue.Empty:
                if output:
                    break
        return "".join(output)

    def send_key(self, key: str) -> Dict[str, str]:
        """
        Send special key sequence to shell.

        Args:
            key: Key name (e.g., ctrl+c, enter, tab).
        Returns:
            Status dict.
        """
        if not self._connected or not self.shell:
            raise RuntimeError("Not connected")
        key_map = {
            "ctrl+c": "\x03", "ctrl+d": "\x04", "ctrl+z": "\x1a",
            "ctrl+a": "\x01", "ctrl+e": "\x05", "ctrl+k": "\x0b",
            "ctrl+l": "\x0c", "ctrl+u": "\x15", "ctrl+w": "\x17",
            "enter": "\n", "tab": "\t", "escape": "\x1b",
            "backspace": "\x7f", "up": "\x1b[A", "down": "\x1b[B",
            "right": "\x1b[C", "left": "\x1b[D", "home": "\x1b[H",
            "end": "\x1b[F", "pageup": "\x1b[5~", "pagedown": "\x1b[6~"
        }
        sequence = key_map.get(key.lower(), key)
        self.shell.send(sequence)
        return {"status": "sent", "key": key}

    def execute_background(
        self, command: str, task_name: Optional[str] = None
    ) -> str:
        """
        Execute command in background thread.

        Args:
            command: Command to execute.
            task_name: Optional task identifier.
        Returns:
            Task ID string.
        """
        if not self._connected or not self.client:
            raise RuntimeError("Not connected")
        task_id = task_name or f"task_{uuid.uuid4().hex[:8]}"
        self.background_tasks[task_id] = {
            "command": command,
            "status": "running",
            "start_time": time.time(),
            "output": [],
            "error": []
        }

        def run_task():
            try:
                stdin, stdout, stderr = self.client.exec_command(command)
                for line in stdout:
                    self.background_tasks[task_id]["output"].append(line.strip())
                err = stderr.read().decode("utf-8", errors="ignore")
                if err:
                    self.background_tasks[task_id]["error"].append(err)
                self.background_tasks[task_id]["status"] = "completed"
            except Exception as e:
                self.background_tasks[task_id]["status"] = "failed"
                self.background_tasks[task_id]["error"].append(str(e))
            self.background_tasks[task_id]["end_time"] = time.time()

        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()
        return task_id

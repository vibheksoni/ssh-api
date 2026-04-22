import socket
import select
import threading
import uuid
from typing import Any, Dict, Optional

import paramiko

from ..core.config import ConfigManager
from ..core.logger import Logger


class TunnelManager:
    """
    SSH tunnel manager for local, remote, and dynamic port forwarding.

    Args:
        transport: Paramiko Transport instance.
        config: ConfigManager instance.
    """

    def __init__(
        self,
        transport: paramiko.Transport,
        config: Optional[ConfigManager] = None
    ) -> None:
        self._transport = transport
        self._config = config or ConfigManager()
        self._log = Logger("tunnel", self._config)
        self._tunnels: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_local_forward(
        self,
        local_port: int,
        remote_host: str,
        remote_port: int,
        bind_address: str = "127.0.0.1"
    ) -> str:
        """
        Create local port forward (SSH -L equivalent).

        Args:
            local_port: Local port to bind.
            remote_host: Remote host to forward to.
            remote_port: Remote port to forward to.
            bind_address: Local address to bind.
        Returns:
            Tunnel ID string.
        """
        tunnel_id = f"local_{uuid.uuid4().hex[:8]}"

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((bind_address, local_port))
        server.listen(5)

        stop_event = threading.Event()

        def accept_loop():
            while not stop_event.is_set():
                try:
                    server.settimeout(1.0)
                    client, addr = server.accept()
                    self._log.debug(f"Connection from {addr}")
                    t = threading.Thread(
                        target=self._handle_local_forward,
                        args=(client, remote_host, remote_port, stop_event)
                    )
                    t.daemon = True
                    t.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if not stop_event.is_set():
                        self._log.error(f"Accept error: {e}")
                    break

        thread = threading.Thread(target=accept_loop)
        thread.daemon = True
        thread.start()

        with self._lock:
            self._tunnels[tunnel_id] = {
                "type": "local",
                "local_port": local_port,
                "remote_host": remote_host,
                "remote_port": remote_port,
                "bind_address": bind_address,
                "server": server,
                "thread": thread,
                "stop_event": stop_event,
                "status": "active"
            }

        self._log.info(
            f"Local forward {tunnel_id}: {bind_address}:{local_port} -> "
            f"{remote_host}:{remote_port}"
        )
        return tunnel_id

    def _handle_local_forward(
        self,
        client: socket.socket,
        remote_host: str,
        remote_port: int,
        stop_event: threading.Event
    ) -> None:
        try:
            channel = self._transport.open_channel(
                "direct-tcpip",
                (remote_host, remote_port),
                client.getpeername()
            )
            if channel is None:
                client.close()
                return

            while not stop_event.is_set():
                r, _, _ = select.select([client, channel], [], [], 1.0)
                if client in r:
                    data = client.recv(4096)
                    if not data:
                        break
                    channel.send(data)
                if channel in r:
                    data = channel.recv(4096)
                    if not data:
                        break
                    client.send(data)
        except Exception as e:
            self._log.debug(f"Forward handler error: {e}")
        finally:
            try:
                client.close()
            except Exception:
                pass
            try:
                channel.close()
            except Exception:
                pass

    def create_remote_forward(
        self,
        remote_port: int,
        local_host: str = "127.0.0.1",
        local_port: int = 0,
        bind_address: str = "0.0.0.0"
    ) -> str:
        """
        Create remote port forward (SSH -R equivalent).

        Args:
            remote_port: Remote port to bind on server.
            local_host: Local host to forward to.
            local_port: Local port to forward to.
            bind_address: Remote address to bind.
        Returns:
            Tunnel ID string.
        """
        tunnel_id = f"remote_{uuid.uuid4().hex[:8]}"
        local_port = local_port or remote_port

        self._transport.request_port_forward(bind_address, remote_port)
        stop_event = threading.Event()

        def handler_loop():
            while not stop_event.is_set():
                try:
                    channel = self._transport.accept(timeout=1.0)
                    if channel is None:
                        continue
                    t = threading.Thread(
                        target=self._handle_remote_forward,
                        args=(channel, local_host, local_port, stop_event)
                    )
                    t.daemon = True
                    t.start()
                except Exception as e:
                    if not stop_event.is_set():
                        self._log.debug(f"Remote forward accept: {e}")

        thread = threading.Thread(target=handler_loop)
        thread.daemon = True
        thread.start()

        with self._lock:
            self._tunnels[tunnel_id] = {
                "type": "remote",
                "remote_port": remote_port,
                "local_host": local_host,
                "local_port": local_port,
                "bind_address": bind_address,
                "thread": thread,
                "stop_event": stop_event,
                "status": "active"
            }

        self._log.info(
            f"Remote forward {tunnel_id}: {bind_address}:{remote_port} -> "
            f"{local_host}:{local_port}"
        )
        return tunnel_id

    def _handle_remote_forward(
        self,
        channel: paramiko.Channel,
        local_host: str,
        local_port: int,
        stop_event: threading.Event
    ) -> None:
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((local_host, local_port))

            while not stop_event.is_set():
                r, _, _ = select.select([sock, channel], [], [], 1.0)
                if sock in r:
                    data = sock.recv(4096)
                    if not data:
                        break
                    channel.send(data)
                if channel in r:
                    data = channel.recv(4096)
                    if not data:
                        break
                    sock.send(data)
        except Exception as e:
            self._log.debug(f"Remote forward handler: {e}")
        finally:
            if sock:
                sock.close()
            channel.close()

    def list_tunnels(self) -> Dict[str, Dict[str, Any]]:
        """
        List all active tunnels.

        Returns:
            Dict of tunnel_id to tunnel info.
        """
        with self._lock:
            result = {}
            for tid, info in self._tunnels.items():
                result[tid] = {
                    "type": info["type"],
                    "status": info["status"],
                    "local_port": info.get("local_port"),
                    "remote_port": info.get("remote_port"),
                    "remote_host": info.get("remote_host"),
                    "local_host": info.get("local_host")
                }
            return result

    def close_tunnel(self, tunnel_id: str) -> bool:
        """
        Close a specific tunnel.

        Args:
            tunnel_id: Tunnel identifier.
        Returns:
            True if closed, False if not found.
        """
        with self._lock:
            if tunnel_id not in self._tunnels:
                return False

            info = self._tunnels[tunnel_id]
            info["stop_event"].set()

            if "server" in info:
                try:
                    info["server"].close()
                except Exception:
                    pass

            if info["type"] == "remote":
                try:
                    bind = info.get("bind_address", "0.0.0.0")
                    port = info["remote_port"]
                    self._transport.cancel_port_forward(bind, port)
                except Exception:
                    pass

            info["status"] = "closed"
            del self._tunnels[tunnel_id]
            self._log.info(f"Closed tunnel {tunnel_id}")
            return True

    def close_all(self) -> int:
        """
        Close all tunnels.

        Returns:
            Number of tunnels closed.
        """
        tunnel_ids = list(self._tunnels.keys())
        count = 0
        for tid in tunnel_ids:
            if self.close_tunnel(tid):
                count += 1
        return count

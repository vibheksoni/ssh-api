import re
from typing import Any, Dict, List, Optional

from ..core.config import ConfigManager
from ..core.logger import Logger
from .platform import PlatformService


class SystemService:
    """
    System operations via SSH commands.

    Args:
        exec_func: Function to execute commands.
        config: ConfigManager instance.
    """

    def __init__(
        self,
        exec_func,
        config: Optional[ConfigManager] = None
    ) -> None:
        self._exec = exec_func
        self._config = config or ConfigManager()
        self._log = Logger("system", self._config)
        self._platform = PlatformService(exec_func, self._config)

    def _quote(self, value: Any) -> str:
        return self._platform.shell_quote(value)

    def _run_candidates(
        self,
        commands: List[str],
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        last_result = {"stdout": "", "stderr": "No command candidates provided", "exit_code": 1}
        for command in commands:
            result = self._exec(command, timeout=timeout)
            if result["exit_code"] == 0:
                return result
            last_result = result
        return last_result

    def get_platform_info(self) -> Dict[str, Any]:
        """Return detected platform capabilities for the remote host."""
        return self._platform.get_platform_info()

    def list_processes(self, filter_user: str = None) -> List[Dict[str, Any]]:
        """
        List running processes.

        Args:
            filter_user: Optional username filter.
        Returns:
            List of process info dicts.
        """
        cmd = "ps -eo user,pid,%cpu,%mem,command --no-headers"
        if filter_user:
            cmd = (
                f"ps -u {self._quote(filter_user)} "
                "-o user,pid,%cpu,%mem,command --no-headers"
            )
        result = self._exec(cmd)
        processes = []
        for line in result["stdout"].strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(None, 4)
            if len(parts) == 5:
                processes.append({
                    "user": parts[0],
                    "pid": parts[1],
                    "cpu": parts[2],
                    "mem": parts[3],
                    "command": parts[4]
                })
        return processes

    def kill_process(self, pid: str, signal: str = "TERM") -> Dict[str, Any]:
        """
        Kill a process by PID.

        Args:
            pid: Process ID.
            signal: Signal name (TERM, KILL, HUP, INT).
        Returns:
            Status dict.
        """
        cmd = f"kill -{signal} {self._quote(pid)}"
        result = self._exec(cmd)
        return {
            "status": "sent" if result["exit_code"] == 0 else "failed",
            "pid": pid,
            "signal": signal,
            "error": result["stderr"] if result["exit_code"] != 0 else None
        }

    def get_disk_usage(self) -> List[Dict[str, str]]:
        """
        Get disk usage info.

        Returns:
            List of disk info dicts.
        """
        result = self._run_candidates(
            [
                "df -P -h",
                "busybox df -h"
            ]
        )
        disks = []
        lines = result["stdout"].strip().split("\n")
        if len(lines) <= 1:
            return disks

        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 6:
                disks.append({
                    "filesystem": parts[0],
                    "size": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "use_percent": parts[4],
                    "mount": parts[5]
                })
        return disks

    def get_memory_info(self) -> Dict[str, Any]:
        """
        Get memory usage info.

        Returns:
            Memory info dict.
        """
        result = self._exec("free -b", timeout=15)
        mem = {"total": 0, "used": 0, "free": 0, "available": 0, "use_percent": 0.0}

        if result["exit_code"] == 0 and result["stdout"].strip():
            for line in result["stdout"].strip().split("\n"):
                if line.startswith("Mem:"):
                    parts = line.split()
                    mem["total"] = int(parts[1])
                    mem["used"] = int(parts[2])
                    mem["free"] = int(parts[3])
                    mem["available"] = int(parts[6]) if len(parts) > 6 else int(parts[3])
                    break
        else:
            meminfo = self._exec("cat /proc/meminfo", timeout=15)
            values: Dict[str, int] = {}
            for line in meminfo["stdout"].splitlines():
                if ":" not in line:
                    continue
                key, raw_value = line.split(":", 1)
                number = raw_value.strip().split()[0]
                if number.isdigit():
                    values[key] = int(number) * 1024
            mem["total"] = values.get("MemTotal", 0)
            mem["free"] = values.get("MemFree", 0)
            mem["available"] = values.get("MemAvailable", mem["free"])
            mem["used"] = max(mem["total"] - mem["available"], 0)

        if mem["total"] > 0:
            mem["use_percent"] = round(mem["used"] / mem["total"] * 100, 2)
        return mem

    def get_cpu_info(self) -> Dict[str, Any]:
        """
        Get CPU info and load averages.

        Returns:
            CPU info dict.
        """
        cpu = {
            "model": "",
            "cores": 0,
            "threads": 0,
            "load_1m": 0.0,
            "load_5m": 0.0,
            "load_15m": 0.0
        }

        result = self._exec(
            "awk -F: '/model name|Hardware/ {print $2; exit}' /proc/cpuinfo 2>/dev/null",
            timeout=15
        )
        if result["stdout"]:
            cpu["model"] = result["stdout"].strip()

        result = self._run_candidates(
            [
                "nproc --all",
                "getconf _NPROCESSORS_ONLN",
                "grep -c '^processor' /proc/cpuinfo"
            ],
            timeout=15
        )
        cpu["threads"] = int(result["stdout"].strip() or 0)

        result = self._exec(
            "awk -F: '/cpu cores/ {gsub(/ /, \"\", $2); print $2; exit}' /proc/cpuinfo 2>/dev/null",
            timeout=15
        )
        cpu["cores"] = int(result["stdout"].strip() or cpu["threads"] or 0)

        result = self._exec("cat /proc/loadavg", timeout=15)
        parts = result["stdout"].strip().split()
        if len(parts) >= 3:
            cpu["load_1m"] = float(parts[0])
            cpu["load_5m"] = float(parts[1])
            cpu["load_15m"] = float(parts[2])

        return cpu

    def get_network_interfaces(self) -> List[Dict[str, Any]]:
        """
        Get network interface info.

        Returns:
            List of interface info dicts.
        """
        tool = self._platform.get_platform_info().get("network_tool")
        if tool == "ip":
            return self._get_network_interfaces_with_ip()
        if tool == "ifconfig":
            return self._get_network_interfaces_with_ifconfig()
        return []

    def _get_network_interfaces_with_ip(self) -> List[Dict[str, Any]]:
        interfaces: Dict[str, Dict[str, Any]] = {}

        link_result = self._exec("ip -o link show", timeout=15)
        for line in link_result["stdout"].splitlines():
            match = re.match(r"^\d+:\s+([^:]+):\s+<([^>]*)>.*link/\S+\s+([0-9a-fA-F:]{17}|00:00:00:00:00:00)", line)
            if not match:
                continue
            name = match.group(1).split("@", 1)[0]
            flags = match.group(2)
            interfaces[name] = {
                "name": name,
                "ip": None,
                "mac": match.group(3),
                "rx_bytes": 0,
                "tx_bytes": 0,
                "status": "up" if "UP" in flags else "down"
            }

        addr_result = self._exec("ip -o addr show", timeout=15)
        for line in addr_result["stdout"].splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            name = parts[1].split("@", 1)[0]
            family = parts[2]
            address = parts[3].split("/", 1)[0]
            iface = interfaces.setdefault(
                name,
                {"name": name, "ip": None, "mac": None, "rx_bytes": 0, "tx_bytes": 0, "status": "unknown"}
            )
            if family == "inet" and not iface["ip"]:
                iface["ip"] = address
            elif family == "inet6" and not iface["ip"]:
                iface["ip"] = address

        return list(interfaces.values())

    def _get_network_interfaces_with_ifconfig(self) -> List[Dict[str, Any]]:
        result = self._exec("ifconfig -a", timeout=15)
        interfaces: List[Dict[str, Any]] = []
        current: Optional[Dict[str, Any]] = None

        for line in result["stdout"].splitlines():
            if not line.strip():
                continue
            if line[0].strip():
                if current:
                    interfaces.append(current)
                name = line.split(":", 1)[0].split()[0]
                current = {
                    "name": name,
                    "ip": None,
                    "mac": None,
                    "rx_bytes": 0,
                    "tx_bytes": 0,
                    "status": "up" if "UP" in line else "down"
                }
            if not current:
                continue

            inet_match = re.search(r"inet (?:addr:)?([0-9.]+)", line)
            if inet_match and not current["ip"]:
                current["ip"] = inet_match.group(1)

            mac_match = re.search(
                r"(?:ether|HWaddr)\s+([0-9a-fA-F:]{17}|[0-9A-Fa-f-]{17})",
                line
            )
            if mac_match:
                current["mac"] = mac_match.group(1).replace("-", ":").lower()

        if current:
            interfaces.append(current)
        return interfaces

    def manage_service(self, service: str, action: str) -> Dict[str, Any]:
        """
        Manage Linux service units across systemd, SysV, and OpenRC.

        Args:
            service: Service name.
            action: Action (start, stop, restart, status, enable, disable).
        Returns:
            Status dict.
        """
        service_name = self._quote(service)
        manager = self._platform.get_platform_info().get("service_manager")

        if manager == "systemd":
            cmd = f"systemctl {action} {service_name}"
        elif manager == "openrc":
            if action in {"enable", "disable"}:
                rc_action = "add" if action == "enable" else "del"
                cmd = f"rc-update {rc_action} {service_name} default"
            else:
                cmd = f"rc-service {service_name} {action}"
        elif manager == "sysvinit":
            if action in {"start", "stop", "restart", "status"}:
                cmd = f"service {service_name} {action}"
            elif action == "enable":
                if self._platform.command_exists("chkconfig"):
                    cmd = f"chkconfig {service_name} on"
                elif self._platform.command_exists("update-rc.d"):
                    cmd = f"update-rc.d {service_name} defaults"
                else:
                    return {
                        "service": service,
                        "action": action,
                        "success": False,
                        "output": "",
                        "error": "No enable mechanism available for this init system"
                    }
            else:
                if self._platform.command_exists("chkconfig"):
                    cmd = f"chkconfig {service_name} off"
                elif self._platform.command_exists("update-rc.d"):
                    cmd = f"update-rc.d {service_name} disable"
                else:
                    return {
                        "service": service,
                        "action": action,
                        "success": False,
                        "output": "",
                        "error": "No disable mechanism available for this init system"
                    }
        else:
            return {
                "service": service,
                "action": action,
                "success": False,
                "output": "",
                "error": "No supported service manager detected"
            }

        result = self._exec(cmd)
        return {
            "service": service,
            "action": action,
            "success": result["exit_code"] == 0,
            "output": result["stdout"],
            "error": result["stderr"] if result["exit_code"] != 0 else None
        }

    def grep(
        self,
        pattern: str,
        path: str = ".",
        recursive: bool = True,
        ignore_case: bool = False,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for pattern in files.

        Args:
            pattern: Search pattern.
            path: Directory or file path.
            recursive: Search recursively.
            ignore_case: Case insensitive.
            max_results: Max results to return.
        Returns:
            List of match dicts.
        """
        flags = "-n"
        if recursive:
            flags += "r"
        if ignore_case:
            flags += "i"
        cmd = (
            f"grep {flags} -- {self._quote(pattern)} {self._quote(path)} "
            f"2>/dev/null | head -n {max_results}"
        )
        result = self._exec(cmd)
        matches = []
        for line in result["stdout"].strip().split("\n"):
            if not line or ":" not in line:
                continue
            parts = line.split(":", 2)
            if len(parts) >= 3 and parts[1].isdigit():
                matches.append({
                    "file": parts[0],
                    "line": int(parts[1]),
                    "content": parts[2]
                })
        return matches

    def find_files(
        self,
        path: str = ".",
        name: str = None,
        file_type: str = None,
        max_depth: int = None,
        max_results: int = 100
    ) -> List[str]:
        """
        Find files matching criteria.

        Args:
            path: Search path.
            name: Filename pattern.
            file_type: Type (f=file, d=dir, l=link).
            max_depth: Max directory depth.
            max_results: Max results.
        Returns:
            List of file paths.
        """
        cmd = f"find {self._quote(path)}"
        if max_depth:
            cmd += f" -maxdepth {max_depth}"
        if file_type:
            cmd += f" -type {file_type}"
        if name:
            cmd += f" -name {self._quote(name)}"
        cmd += f" 2>/dev/null | head -n {max_results}"
        result = self._exec(cmd)
        return [f for f in result["stdout"].strip().split("\n") if f]

    def create_archive(
        self,
        source: str,
        destination: str,
        fmt: str = "tar.gz"
    ) -> Dict[str, Any]:
        """
        Create archive from source.

        Args:
            source: Source path.
            destination: Archive destination.
            fmt: Format (tar, tar.gz, tar.bz2, zip).
        Returns:
            Status dict.
        """
        src = self._quote(source)
        dst = self._quote(destination)

        if fmt == "tar":
            cmd = f"tar -cvf {dst} {src}"
        elif fmt == "tar.gz":
            cmd = f"tar -czvf {dst} {src}"
        elif fmt == "tar.bz2":
            cmd = f"tar -cjvf {dst} {src}"
        elif fmt == "zip":
            cmd = f"zip -r {dst} {src}"
        else:
            return {"success": False, "error": f"Unknown format: {fmt}"}

        result = self._exec(cmd)
        return {
            "success": result["exit_code"] == 0,
            "archive": destination,
            "error": result["stderr"] if result["exit_code"] != 0 else None
        }

    def extract_archive(self, archive: str, destination: str = ".") -> Dict[str, Any]:
        """
        Extract archive to destination.

        Args:
            archive: Archive path.
            destination: Extract destination.
        Returns:
            Status dict.
        """
        archive_q = self._quote(archive)
        destination_q = self._quote(destination)

        if archive.endswith(".zip"):
            cmd = f"unzip -o {archive_q} -d {destination_q}"
        elif archive.endswith(".tar.bz2") or archive.endswith(".tbz2"):
            cmd = f"tar -xjvf {archive_q} -C {destination_q}"
        elif archive.endswith(".tar.gz") or archive.endswith(".tgz"):
            cmd = f"tar -xzvf {archive_q} -C {destination_q}"
        elif archive.endswith(".tar"):
            cmd = f"tar -xvf {archive_q} -C {destination_q}"
        else:
            cmd = f"tar -xf {archive_q} -C {destination_q}"

        result = self._exec(cmd)
        return {
            "success": result["exit_code"] == 0,
            "destination": destination,
            "error": result["stderr"] if result["exit_code"] != 0 else None
        }

    def get_env_var(self, name: str) -> Optional[str]:
        """
        Get environment variable value.

        Args:
            name: Variable name.
        Returns:
            Variable value or None.
        """
        result = self._exec(f"printenv {self._quote(name)}", timeout=15)
        val = result["stdout"].strip()
        return val if val else None

    def set_env_var(self, name: str, value: str, persist: bool = False) -> Dict[str, Any]:
        """
        Set environment variable.

        Args:
            name: Variable name.
            value: Variable value.
            persist: Add to .bashrc.
        Returns:
            Status dict.
        """
        export_line = f"export {name}={self._quote(value)}"
        cmd = export_line
        if persist:
            cmd += f" && printf '%s\\n' {self._quote(export_line)} >> ~/.bashrc"
        result = self._exec(cmd)
        return {"success": result["exit_code"] == 0, "name": name, "value": value}

    def list_cron_jobs(self, user: str = None) -> List[str]:
        """
        List cron jobs.

        Args:
            user: Optional user filter.
        Returns:
            List of cron entries.
        """
        cmd = (
            f"crontab -u {self._quote(user)} -l"
            if user else
            "crontab -l"
        )
        result = self._exec(cmd + " 2>/dev/null || true")
        jobs = []
        for line in result["stdout"].strip().split("\n"):
            if line and not line.startswith("#"):
                jobs.append(line)
        return jobs

    def add_cron_job(self, schedule: str, command: str) -> Dict[str, Any]:
        """
        Add cron job.

        Args:
            schedule: Cron schedule (e.g., "0 * * * *").
            command: Command to run.
        Returns:
            Status dict.
        """
        entry = f"{schedule} {command}"
        cmd = f"(crontab -l 2>/dev/null; printf '%s\\n' {self._quote(entry)}) | crontab -"
        result = self._exec(cmd)
        return {"success": result["exit_code"] == 0, "entry": entry}

    def list_users(self) -> List[Dict[str, Any]]:
        """
        List system users.

        Returns:
            List of user info dicts.
        """
        result = self._exec("cat /etc/passwd")
        users = []
        for line in result["stdout"].strip().split("\n"):
            parts = line.split(":")
            if len(parts) >= 7 and parts[2].isdigit() and parts[3].isdigit():
                users.append({
                    "username": parts[0],
                    "uid": int(parts[2]),
                    "gid": int(parts[3]),
                    "home": parts[5],
                    "shell": parts[6]
                })
        return users

    def chmod(self, path: str, mode: str, recursive: bool = False) -> Dict[str, Any]:
        """
        Change file permissions.

        Args:
            path: File or directory path.
            mode: Permission mode (e.g., "755", "u+x").
            recursive: Apply recursively.
        Returns:
            Status dict.
        """
        flags = "-R " if recursive else ""
        result = self._exec(f"chmod {flags}{self._quote(mode)} {self._quote(path)}")
        return {"success": result["exit_code"] == 0, "path": path, "mode": mode}

    def chown(
        self, path: str, owner: str, group: str = None, recursive: bool = False
    ) -> Dict[str, Any]:
        """
        Change file ownership.

        Args:
            path: File or directory path.
            owner: New owner username.
            group: New group name.
            recursive: Apply recursively.
        Returns:
            Status dict.
        """
        flags = "-R " if recursive else ""
        ownership = f"{owner}:{group}" if group else owner
        result = self._exec(f"chown {flags}{self._quote(ownership)} {self._quote(path)}")
        return {"success": result["exit_code"] == 0, "path": path, "owner": ownership}

    def tail_file(self, path: str, lines: int = 100) -> str:
        """
        Get last N lines of file.

        Args:
            path: File path.
            lines: Number of lines.
        Returns:
            File content string.
        """
        result = self._exec(f"tail -n {lines} {self._quote(path)}")
        return result["stdout"]

    def head_file(self, path: str, lines: int = 100) -> str:
        """
        Get first N lines of file.

        Args:
            path: File path.
            lines: Number of lines.
        Returns:
            File content string.
        """
        result = self._exec(f"head -n {lines} {self._quote(path)}")
        return result["stdout"]

    def get_uptime(self) -> Dict[str, Any]:
        """
        Get system uptime.

        Returns:
            Uptime info dict.
        """
        result = self._run_candidates(
            [
                "uptime -p",
                "uptime"
            ],
            timeout=15
        )
        uptime_str = result["stdout"].strip()

        seconds_result = self._exec("cat /proc/uptime", timeout=15)
        seconds = 0.0
        if seconds_result["stdout"].strip():
            try:
                seconds = float(seconds_result["stdout"].split()[0])
            except (ValueError, IndexError):
                seconds = 0.0
        return {"uptime": uptime_str, "seconds": seconds}

    def rm_rf(self, path: str) -> Dict[str, Any]:
        """
        Fast recursive delete using rm -rf.

        Args:
            path: Path to delete.
        Returns:
            Status dict.
        """
        if not path or path in ("/", "/*", "~", "~/*"):
            return {"success": False, "error": "Refusing to delete root or home"}
        result = self._exec(f"rm -rf -- {self._quote(path)}", timeout=300)
        return {
            "success": result["exit_code"] == 0,
            "path": path,
            "error": result["stderr"] if result["exit_code"] != 0 else None
        }

import shlex
from typing import Any, Dict, Optional

from ..core.config import ConfigManager
from ..core.logger import Logger


class PlatformService:
    """
    Detect remote Linux platform capabilities from an active SSH session.

    Args:
        exec_func: Function used to execute remote shell commands.
        config: Optional ConfigManager instance.
    """

    def __init__(self, exec_func, config: Optional[ConfigManager] = None) -> None:
        self._exec = exec_func
        self._config = config or ConfigManager()
        self._log = Logger("platform", self._config)
        self._cache: Optional[Dict[str, Any]] = None

    @staticmethod
    def shell_quote(value: Any) -> str:
        """Safely quote a value for use in a POSIX shell command."""
        return shlex.quote(str(value))

    def command_exists(self, command: str) -> bool:
        result = self._exec(
            f"command -v {self.shell_quote(command)} >/dev/null 2>&1",
            timeout=10
        )
        return result["exit_code"] == 0

    def get_platform_info(self, refresh: bool = False) -> Dict[str, Any]:
        """
        Detect the remote platform and available management tools.

        Returns:
            Dict with OS, distro family, package manager, service manager, and firewall backend.
        """
        if self._cache and not refresh:
            return dict(self._cache)

        os_release = self._read_os_release()
        platform = {
            "os": os_release.get("ID", "") or "linux",
            "family": self._detect_family(os_release),
            "name": os_release.get("NAME", ""),
            "version_id": os_release.get("VERSION_ID", ""),
            "pretty_name": os_release.get("PRETTY_NAME", "") or os_release.get("NAME", ""),
            "kernel": self._get_kernel(),
            "package_manager": self._detect_package_manager(os_release),
            "service_manager": self._detect_service_manager(),
            "firewall_backend": self._detect_firewall_backend(),
            "network_tool": self._detect_network_tool(),
            "init_system": self._detect_init_system()
        }
        self._cache = platform
        return dict(platform)

    def _read_os_release(self) -> Dict[str, str]:
        command = (
            "if [ -r /etc/os-release ]; then . /etc/os-release; "
            "elif [ -r /usr/lib/os-release ]; then . /usr/lib/os-release; fi; "
            "printf 'ID=%s\nID_LIKE=%s\nNAME=%s\nVERSION_ID=%s\nPRETTY_NAME=%s\n' "
            "\"${ID:-}\" \"${ID_LIKE:-}\" \"${NAME:-}\" \"${VERSION_ID:-}\" "
            "\"${PRETTY_NAME:-}\""
        )
        result = self._exec(command, timeout=10)
        data: Dict[str, str] = {}
        for line in result["stdout"].splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip().strip('"')
        return data

    def _detect_family(self, os_release: Dict[str, str]) -> str:
        words = {
            word.strip().lower()
            for word in f"{os_release.get('ID', '')} {os_release.get('ID_LIKE', '')}".split()
            if word.strip()
        }
        if words & {"ubuntu", "debian", "linuxmint", "raspbian", "devuan", "kali"}:
            return "debian"
        if words & {"rhel", "fedora", "centos", "rocky", "almalinux", "ol", "amzn"}:
            return "rhel"
        if words & {"sles", "suse", "opensuse", "opensuse-leap", "opensuse-tumbleweed"}:
            return "suse"
        if "alpine" in words:
            return "alpine"
        if words & {"arch", "manjaro"}:
            return "arch"
        return "linux"

    def _detect_package_manager(self, os_release: Dict[str, str]) -> Optional[str]:
        family = self._detect_family(os_release)
        preferred = {
            "debian": ["apt-get"],
            "rhel": ["dnf", "yum"],
            "suse": ["zypper"],
            "alpine": ["apk"],
            "arch": ["pacman"]
        }.get(family, [])

        candidates = preferred + ["apt-get", "dnf", "yum", "zypper", "apk", "pacman"]
        for command in candidates:
            if self.command_exists(command):
                return command
        return None

    def _detect_init_system(self) -> str:
        pid1 = self._exec("ps -p 1 -o comm=", timeout=10)["stdout"].strip().lower()
        if "systemd" in pid1:
            return "systemd"
        if "openrc" in pid1:
            return "openrc"
        if pid1:
            return pid1
        return "unknown"

    def _detect_service_manager(self) -> Optional[str]:
        init_system = self._detect_init_system()
        if init_system == "systemd" and self.command_exists("systemctl"):
            return "systemd"
        if self.command_exists("rc-service"):
            return "openrc"
        if self.command_exists("service"):
            return "sysvinit"
        if self.command_exists("systemctl"):
            return "systemd"
        return None

    def _detect_firewall_backend(self) -> Optional[str]:
        if self.command_exists("firewall-cmd"):
            result = self._exec("firewall-cmd --state", timeout=15)
            if result["exit_code"] == 0 and "running" in result["stdout"].lower():
                return "firewalld"
        if self.command_exists("iptables"):
            return "iptables"
        if self.command_exists("nft"):
            return "nftables"
        return None

    def _detect_network_tool(self) -> Optional[str]:
        if self.command_exists("ip"):
            return "ip"
        if self.command_exists("ifconfig"):
            return "ifconfig"
        return None

    def _get_kernel(self) -> str:
        return self._exec("uname -srm", timeout=10)["stdout"].strip()

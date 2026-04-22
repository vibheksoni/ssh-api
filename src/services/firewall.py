from typing import Any, Dict, List, Optional, Tuple

from ..core.config import ConfigManager
from ..core.logger import Logger
from .platform import PlatformService


class FirewallService:
    """
    Cross-distro firewall operations for iptables and firewalld-based systems.

    Args:
        exec_func: Function used to execute remote shell commands.
        config: Optional ConfigManager instance.
    """

    def __init__(self, exec_func, config: Optional[ConfigManager] = None) -> None:
        self._exec = exec_func
        self._config = config or ConfigManager()
        self._log = Logger("firewall", self._config)
        self._platform = PlatformService(exec_func, self._config)

    def _quote(self, value: Any) -> str:
        return self._platform.shell_quote(value)

    def _backend(self) -> Optional[str]:
        return self._platform.get_platform_info().get("firewall_backend")

    def _ip_families(self, ip_version: str) -> List[Tuple[str, str]]:
        families = []
        if ip_version in ("ipv4", "both"):
            families.append(("ipv4", "ipv4"))
        if ip_version in ("ipv6", "both"):
            families.append(("ipv6", "ipv6"))
        return families

    def _ip_families_for_address(
        self,
        ip_version: str,
        address: Optional[str]
    ) -> List[Tuple[str, str]]:
        if not address:
            return self._ip_families(ip_version)

        if ":" in address:
            if ip_version == "ipv4":
                return []
            return [("ipv6", "ipv6")]

        if "." in address:
            if ip_version == "ipv6":
                return []
            return [("ipv4", "ipv4")]

        return self._ip_families(ip_version)

    def get_backend_info(self) -> Dict[str, Any]:
        platform = self._platform.get_platform_info()
        return {
            "backend": platform.get("firewall_backend"),
            "platform": platform.get("pretty_name"),
            "family": platform.get("family"),
            "service_manager": platform.get("service_manager")
        }

    def _unsupported(self, message: str) -> Dict[str, Any]:
        return {
            "backend": self._backend(),
            "success": False,
            "error": message
        }

    def _run_backend_command(
        self,
        command: str,
        family: str,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        backend = self._backend()
        if backend == "iptables":
            binary = "iptables" if family == "ipv4" else "ip6tables"
            return self._exec(f"{binary} {command}", timeout=timeout)
        if backend == "firewalld":
            return self._exec(
                f"firewall-cmd --direct --passthrough {family} {command}",
                timeout=timeout
            )
        return {
            "stdout": "",
            "stderr": f"Unsupported firewall backend: {backend or 'none detected'}",
            "exit_code": 1
        }

    def _run_dual_stack(
        self,
        command: str,
        ip_version: str,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        results = {
            "backend": self._backend(),
            "ipv4": None,
            "ipv6": None,
            "success": True
        }

        if not results["backend"]:
            return self._unsupported("No supported firewall backend detected")

        for key, family in self._ip_families(ip_version):
            result = self._run_backend_command(command, family, timeout=timeout)
            results[key] = {
                "exit_code": result["exit_code"],
                "output": result["stdout"],
                "error": result["stderr"] if result["exit_code"] != 0 else None
            }
            if result["exit_code"] != 0:
                results["success"] = False
        return results

    def list_rules(self, chain: Optional[str], ip_version: str) -> Dict[str, Any]:
        backend = self._backend()
        if backend in {"iptables", "firewalld"}:
            command = "-L -n -v --line-numbers"
            if chain:
                command = f"-L {chain} -n -v --line-numbers"
            result = self._run_dual_stack(command, ip_version)
            if result["success"] or backend == "iptables":
                return result

        if backend == "firewalld":
            summary = self._exec("firewall-cmd --list-all", timeout=30)
            rich_rules = self._exec("firewall-cmd --list-rich-rules", timeout=30)
            output = summary["stdout"]
            if rich_rules["stdout"].strip():
                output = f"{output}\nRich rules:\n{rich_rules['stdout']}".strip()
            return {
                "backend": backend,
                "success": summary["exit_code"] == 0 and rich_rules["exit_code"] == 0,
                "ipv4": {
                    "exit_code": summary["exit_code"],
                    "output": output,
                    "error": summary["stderr"] or rich_rules["stderr"] or None
                },
                "ipv6": None
            }

        return self._unsupported("No supported firewall backend detected")

    def list_rules_raw(self, ip_version: str) -> Dict[str, Any]:
        backend = self._backend()
        if backend == "iptables":
            results = {"backend": backend, "ipv4": None, "ipv6": None}
            for key, family in self._ip_families(ip_version):
                binary = "iptables-save" if family == "ipv4" else "ip6tables-save"
                result = self._exec(binary, timeout=30)
                results[key] = result["stdout"] if result["exit_code"] == 0 else result["stderr"]
            return results

        if backend == "firewalld":
            direct = self._exec("firewall-cmd --direct --get-all-rules", timeout=30)
            rich = self._exec("firewall-cmd --list-rich-rules", timeout=30)
            output = direct["stdout"]
            if rich["stdout"].strip():
                output = f"{output}\n{rich['stdout']}".strip()
            return {"backend": backend, "ipv4": output, "ipv6": None}

        return self._unsupported("No supported firewall backend detected")

    def add_rule(
        self,
        chain: str,
        protocol: str,
        port: Optional[int],
        source: Optional[str],
        destination: Optional[str],
        target: str,
        ip_version: str,
        comment: Optional[str]
    ) -> Dict[str, Any]:
        parts = [f"-A {chain}"]
        if protocol != "all":
            parts.append(f"-p {protocol}")
        if source:
            parts.append(f"-s {self._quote(source)}")
        if destination:
            parts.append(f"-d {self._quote(destination)}")
        if port and protocol in {"tcp", "udp"}:
            parts.append(f"--dport {port}")
        if comment:
            parts.append(f"-m comment --comment {self._quote(comment)}")
        parts.append(f"-j {target}")

        result = self._run_dual_stack(" ".join(parts), ip_version)
        if result["success"] or self._backend() != "firewalld":
            return result

        if chain == "INPUT" and target in {"ACCEPT", "DROP", "REJECT", "LOG"}:
            return self._add_rich_rule(protocol, port, source, target, ip_version)
        return result

    def delete_rule(self, chain: str, rule_num: int, ip_version: str) -> Dict[str, Any]:
        return self._run_dual_stack(f"-D {chain} {rule_num}", ip_version)

    def add_port_range_rule(
        self,
        chain: str,
        protocol: str,
        port_start: int,
        port_end: int,
        source: Optional[str],
        target: str,
        ip_version: str
    ) -> Dict[str, Any]:
        parts = [f"-A {chain}", f"-p {protocol}"]
        if source:
            parts.append(f"-s {self._quote(source)}")
        parts.append(f"--dport {port_start}:{port_end}")
        parts.append(f"-j {target}")

        result = self._run_dual_stack(" ".join(parts), ip_version)
        if result["success"] or self._backend() != "firewalld":
            return result

        if chain == "INPUT" and target in {"ACCEPT", "DROP", "REJECT"}:
            return self._add_rich_rule(
                protocol=protocol,
                port=None,
                source=source,
                target=target,
                ip_version=ip_version,
                port_start=port_start,
                port_end=port_end
            )
        return result

    def flush_rules(self, chain: Optional[str], ip_version: str) -> Dict[str, Any]:
        command = f"-F {chain}" if chain else "-F"
        return self._run_dual_stack(command, ip_version)

    def save_rules(self) -> Dict[str, Any]:
        backend = self._backend()
        if backend == "firewalld":
            result = self._exec("firewall-cmd --runtime-to-permanent", timeout=60)
            return {
                "backend": backend,
                "success": result["exit_code"] == 0,
                "output": result["stdout"],
                "error": result["stderr"] if result["exit_code"] != 0 else None
            }

        if backend == "iptables":
            candidates = [
                "netfilter-persistent save",
                "service iptables save",
                (
                    "if [ -d /etc/sysconfig ]; then "
                    "iptables-save > /etc/sysconfig/iptables && "
                    "(command -v ip6tables-save >/dev/null 2>&1 && "
                    "ip6tables-save > /etc/sysconfig/ip6tables || true); "
                    "else false; fi"
                )
            ]
            last = {"stdout": "", "stderr": "No save command succeeded", "exit_code": 1}
            for candidate in candidates:
                result = self._exec(candidate, timeout=60)
                if result["exit_code"] == 0:
                    return {
                        "backend": backend,
                        "success": True,
                        "output": result["stdout"] or "Firewall rules saved",
                        "error": None
                    }
                last = result
            return {
                "backend": backend,
                "success": False,
                "output": last["stdout"],
                "error": last["stderr"] or "Firewall save command failed"
            }

        return self._unsupported("No supported firewall backend detected")

    def restore_rules(self) -> Dict[str, Any]:
        backend = self._backend()
        if backend == "firewalld":
            result = self._exec("firewall-cmd --reload", timeout=60)
            return {
                "backend": backend,
                "success": result["exit_code"] == 0,
                "output": result["stdout"],
                "error": result["stderr"] if result["exit_code"] != 0 else None
            }

        if backend == "iptables":
            candidates = [
                "netfilter-persistent reload",
                "systemctl restart iptables",
                "service iptables restart"
            ]
            last = {"stdout": "", "stderr": "No restore command succeeded", "exit_code": 1}
            for candidate in candidates:
                result = self._exec(candidate, timeout=60)
                if result["exit_code"] == 0:
                    return {
                        "backend": backend,
                        "success": True,
                        "output": result["stdout"] or "Firewall rules restored",
                        "error": None
                    }
                last = result
            return {
                "backend": backend,
                "success": False,
                "output": last["stdout"],
                "error": last["stderr"] or "Firewall restore command failed"
            }

        return self._unsupported("No supported firewall backend detected")

    def set_policy(self, chain: str, target: str, ip_version: str) -> Dict[str, Any]:
        return self._run_dual_stack(f"-P {chain} {target}", ip_version)

    def allow_port(
        self,
        port: int,
        protocol: str,
        source: Optional[str],
        ip_version: str
    ) -> Dict[str, Any]:
        if self._backend() == "firewalld":
            return self._add_rich_rule(protocol, port, source, "ACCEPT", ip_version)
        command = f"-A INPUT -p {protocol}"
        if source:
            command += f" -s {self._quote(source)}"
        command += f" --dport {port} -j ACCEPT"
        return self._run_dual_stack(command, ip_version)

    def block_port(self, port: int, protocol: str, ip_version: str) -> Dict[str, Any]:
        if self._backend() == "firewalld":
            return self._add_rich_rule(protocol, port, None, "DROP", ip_version)
        return self._run_dual_stack(f"-A INPUT -p {protocol} --dport {port} -j DROP", ip_version)

    def block_ip(self, ip: str, ip_version: str) -> Dict[str, Any]:
        if self._backend() == "firewalld":
            return self._add_ip_rich_rule(ip, "DROP", ip_version)
        return self._run_dual_stack(f"-A INPUT -s {self._quote(ip)} -j DROP", ip_version)

    def allow_ip(self, ip: str, ip_version: str) -> Dict[str, Any]:
        if self._backend() == "firewalld":
            return self._add_ip_rich_rule(ip, "ACCEPT", ip_version)
        return self._run_dual_stack(f"-A INPUT -s {self._quote(ip)} -j ACCEPT", ip_version)

    def _add_rich_rule(
        self,
        protocol: str,
        port: Optional[int],
        source: Optional[str],
        target: str,
        ip_version: str,
        port_start: Optional[int] = None,
        port_end: Optional[int] = None
    ) -> Dict[str, Any]:
        if protocol == "all" and (port or port_start or port_end):
            return self._unsupported("firewalld rich rules require tcp or udp for port-based operations")

        results = {
            "backend": "firewalld",
            "ipv4": None,
            "ipv6": None,
            "success": True
        }

        action = target.lower()
        families = self._ip_families_for_address(ip_version, source)
        if not families:
            return self._unsupported("Requested ip_version does not match the provided source address family")

        for key, family in families:
            parts = [f'rule family="{family}"']
            if source:
                parts.append(f'source address="{source}"')
            if port_start is not None and port_end is not None:
                parts.append(
                    f'port port="{port_start}-{port_end}" protocol="{protocol}"'
                )
            elif port is not None:
                parts.append(f'port port="{port}" protocol="{protocol}"')
            if action == "log":
                parts.append("log")
            else:
                parts.append(action)

            rule = " ".join(parts)
            result = self._exec(
                f"firewall-cmd --add-rich-rule={self._quote(rule)}",
                timeout=30
            )
            results[key] = {
                "exit_code": result["exit_code"],
                "output": result["stdout"],
                "error": result["stderr"] if result["exit_code"] != 0 else None
            }
            if result["exit_code"] != 0:
                results["success"] = False
        return results

    def _add_ip_rich_rule(self, ip: str, target: str, ip_version: str) -> Dict[str, Any]:
        results = {
            "backend": "firewalld",
            "ipv4": None,
            "ipv6": None,
            "success": True
        }
        action = target.lower()

        families = self._ip_families_for_address(ip_version, ip)
        if not families:
            return self._unsupported("Requested ip_version does not match the provided IP address family")

        for key, family in families:
            rule = f'rule family="{family}" source address="{ip}" {action}'
            result = self._exec(
                f"firewall-cmd --add-rich-rule={self._quote(rule)}",
                timeout=30
            )
            results[key] = {
                "exit_code": result["exit_code"],
                "output": result["stdout"],
                "error": result["stderr"] if result["exit_code"] != 0 else None
            }
            if result["exit_code"] != 0:
                results["success"] = False
        return results

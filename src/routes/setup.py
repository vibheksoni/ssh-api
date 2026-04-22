from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.manager import SessionManager
from ..services.platform import PlatformService

router = APIRouter(prefix="/setup", tags=["Setup"])
manager = SessionManager()


class PackageInstallRequest(BaseModel):
    packages: List[str] = Field(default_factory=list)
    update_first: bool = Field(default=True)


class SetupResult(BaseModel):
    status: str
    installed: List[str]
    failed: List[str]
    output: str
    package_manager: Optional[str] = None
    platform: Dict[str, Optional[str]] = Field(default_factory=dict)
    resolved_packages: List[str] = Field(default_factory=list)


DEFAULT_PACKAGES_BY_MANAGER = {
    "apt-get": [
        "curl", "wget", "git", "vim", "nano", "htop", "iotop", "iftop",
        "net-tools", "dnsutils", "iputils-ping", "traceroute", "mtr-tiny",
        "tcpdump", "nmap", "netcat-openbsd", "socat", "openssh-client",
        "rsync", "unzip", "zip", "tar", "gzip", "bzip2", "xz-utils",
        "p7zip-full", "jq", "tree", "ncdu", "tmux", "screen", "cron",
        "logrotate", "fail2ban", "ufw", "iptables", "iptables-persistent",
        "netfilter-persistent", "ca-certificates", "gnupg", "lsb-release",
        "software-properties-common", "apt-transport-https", "build-essential",
        "python3", "python3-pip", "python3-venv"
    ],
    "dnf": [
        "curl", "wget", "git", "vim-enhanced", "nano", "htop", "iotop",
        "net-tools", "bind-utils", "iputils", "traceroute", "mtr",
        "tcpdump", "nmap", "nmap-ncat", "socat", "openssh-clients",
        "rsync", "unzip", "zip", "tar", "gzip", "bzip2", "xz",
        "jq", "tree", "tmux", "screen", "cronie", "logrotate",
        "firewalld", "iptables", "iptables-services", "ca-certificates",
        "gnupg2", "gcc", "gcc-c++", "make", "python3", "python3-pip"
    ],
    "yum": [
        "curl", "wget", "git", "vim-enhanced", "nano", "htop", "iotop",
        "net-tools", "bind-utils", "iputils", "traceroute", "mtr",
        "tcpdump", "nmap", "nmap-ncat", "socat", "openssh-clients",
        "rsync", "unzip", "zip", "tar", "gzip", "bzip2", "xz",
        "jq", "tree", "tmux", "screen", "cronie", "logrotate",
        "firewalld", "iptables", "iptables-services", "ca-certificates",
        "gnupg2", "gcc", "gcc-c++", "make", "python3", "python3-pip"
    ],
    "zypper": [
        "curl", "wget", "git", "vim", "nano", "htop", "iotop",
        "net-tools", "bind-utils", "iputils", "traceroute", "mtr",
        "tcpdump", "nmap", "netcat-openbsd", "socat", "openssh-clients",
        "rsync", "unzip", "zip", "tar", "gzip", "bzip2", "xz",
        "jq", "tree", "tmux", "screen", "cron", "logrotate",
        "firewalld", "iptables", "ca-certificates", "gpg2",
        "gcc", "gcc-c++", "make", "python3", "python3-pip"
    ],
    "apk": [
        "curl", "wget", "git", "vim", "nano", "htop", "iftop",
        "bind-tools", "iputils", "traceroute", "mtr", "tcpdump",
        "nmap", "netcat-openbsd", "socat", "openssh-client", "rsync",
        "unzip", "zip", "tar", "gzip", "bzip2", "xz", "jq", "tree",
        "tmux", "screen", "dcron", "logrotate", "iptables",
        "ca-certificates", "gnupg", "build-base", "python3", "py3-pip"
    ],
    "pacman": [
        "curl", "wget", "git", "vim", "nano", "htop", "iotop",
        "net-tools", "bind", "iputils", "traceroute", "mtr",
        "tcpdump", "nmap", "gnu-netcat", "socat", "openssh", "rsync",
        "unzip", "zip", "tar", "gzip", "bzip2", "xz", "p7zip", "jq",
        "tree", "ncdu", "tmux", "screen", "cronie", "logrotate",
        "iptables", "ca-certificates", "gnupg", "base-devel",
        "python", "python-pip"
    ]
}


PACKAGE_ALIASES_BY_MANAGER = {
    "apt-get": {},
    "dnf": {
        "dnsutils": ["bind-utils"],
        "iputils-ping": ["iputils"],
        "mtr-tiny": ["mtr"],
        "netcat-openbsd": ["nmap-ncat"],
        "openssh-client": ["openssh-clients"],
        "xz-utils": ["xz"],
        "p7zip-full": ["p7zip", "p7zip-plugins"],
        "cron": ["cronie"],
        "ufw": ["firewalld"],
        "iptables-persistent": ["iptables-services"],
        "netfilter-persistent": ["iptables-services"],
        "gnupg": ["gnupg2"],
        "lsb-release": ["redhat-lsb-core"],
        "software-properties-common": [],
        "apt-transport-https": [],
        "build-essential": ["gcc", "gcc-c++", "make"],
        "python3-venv": ["python3-virtualenv"],
        "vim": ["vim-enhanced"]
    },
    "yum": {
        "dnsutils": ["bind-utils"],
        "iputils-ping": ["iputils"],
        "mtr-tiny": ["mtr"],
        "netcat-openbsd": ["nmap-ncat"],
        "openssh-client": ["openssh-clients"],
        "xz-utils": ["xz"],
        "p7zip-full": ["p7zip", "p7zip-plugins"],
        "cron": ["cronie"],
        "ufw": ["firewalld"],
        "iptables-persistent": ["iptables-services"],
        "netfilter-persistent": ["iptables-services"],
        "gnupg": ["gnupg2"],
        "lsb-release": ["redhat-lsb-core"],
        "software-properties-common": [],
        "apt-transport-https": [],
        "build-essential": ["gcc", "gcc-c++", "make"],
        "python3-venv": ["python3-virtualenv"],
        "vim": ["vim-enhanced"]
    },
    "zypper": {
        "dnsutils": ["bind-utils"],
        "iputils-ping": ["iputils"],
        "mtr-tiny": ["mtr"],
        "openssh-client": ["openssh-clients"],
        "xz-utils": ["xz"],
        "p7zip-full": ["p7zip"],
        "ufw": ["firewalld"],
        "iptables-persistent": [],
        "netfilter-persistent": [],
        "gnupg": ["gpg2"],
        "software-properties-common": [],
        "apt-transport-https": [],
        "build-essential": ["gcc", "gcc-c++", "make"]
    },
    "apk": {
        "net-tools": [],
        "dnsutils": ["bind-tools"],
        "iputils-ping": ["iputils"],
        "mtr-tiny": ["mtr"],
        "openssh-client": ["openssh-client"],
        "xz-utils": ["xz"],
        "p7zip-full": ["p7zip"],
        "cron": ["dcron"],
        "ufw": [],
        "iptables-persistent": [],
        "netfilter-persistent": [],
        "lsb-release": [],
        "software-properties-common": [],
        "apt-transport-https": [],
        "build-essential": ["build-base"],
        "python3-pip": ["py3-pip"],
        "python3-venv": []
    },
    "pacman": {
        "dnsutils": ["bind"],
        "iputils-ping": ["iputils"],
        "mtr-tiny": ["mtr"],
        "netcat-openbsd": ["gnu-netcat"],
        "openssh-client": ["openssh"],
        "xz-utils": ["xz"],
        "cron": ["cronie"],
        "ufw": [],
        "iptables-persistent": [],
        "netfilter-persistent": [],
        "gnupg": ["gnupg"],
        "lsb-release": [],
        "software-properties-common": [],
        "apt-transport-https": [],
        "build-essential": ["base-devel"],
        "python3": ["python"],
        "python3-pip": ["python-pip"],
        "python3-venv": []
    }
}


def _get_exec(session_id: str = None):
    if session_id:
        session = manager.get_session(session_id)
    else:
        session = manager.get_default_session()
    if not session:
        raise HTTPException(status_code=404, detail="No active session")
    return session.exec_command


def _get_platform_service(session_id: str = None) -> PlatformService:
    return PlatformService(_get_exec(session_id))


def _resolve_packages(
    requested: List[str],
    package_manager: str
) -> tuple[List[str], List[str]]:
    aliases = PACKAGE_ALIASES_BY_MANAGER.get(package_manager, {})
    resolved: List[str] = []
    skipped: List[str] = []
    seen = set()

    for package in requested:
        translated = aliases.get(package, [package])
        if not translated:
            skipped.append(package)
            continue
        for name in translated:
            if name not in seen:
                resolved.append(name)
                seen.add(name)
    return resolved, skipped


def _build_update_command(package_manager: str) -> Optional[str]:
    if package_manager == "apt-get":
        return "DEBIAN_FRONTEND=noninteractive apt-get update -y"
    if package_manager == "dnf":
        return "dnf -y makecache"
    if package_manager == "yum":
        return "yum -y makecache"
    if package_manager == "zypper":
        return "zypper --non-interactive refresh"
    if package_manager == "apk":
        return "apk update"
    if package_manager == "pacman":
        return "pacman -Sy --noconfirm"
    return None


def _build_install_command(package_manager: str, package: str) -> str:
    package_q = PlatformService.shell_quote(package)
    if package_manager == "apt-get":
        apt_opts = "-y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold'"
        return f"DEBIAN_FRONTEND=noninteractive apt-get install {apt_opts} {package_q}"
    if package_manager == "dnf":
        return f"dnf install -y {package_q}"
    if package_manager == "yum":
        return f"yum install -y {package_q}"
    if package_manager == "zypper":
        return f"zypper --non-interactive install --no-confirm {package_q}"
    if package_manager == "apk":
        return f"apk add --no-cache {package_q}"
    if package_manager == "pacman":
        return f"pacman -S --noconfirm --needed {package_q}"
    raise ValueError(f"Unsupported package manager: {package_manager}")


@router.get("/platform")
async def get_setup_platform(session_id: str = None) -> dict:
    """Detect package-management capabilities for the connected Linux host."""
    platform = _get_platform_service(session_id).get_platform_info()
    return {"platform": platform}


@router.post("/requirements", response_model=SetupResult)
async def install_requirements(
    req: Optional[PackageInstallRequest] = None,
    session_id: str = None
) -> SetupResult:
    """
    Install essential packages on the connected Linux host.
    Supports Debian/Ubuntu, RHEL/CentOS, SUSE, Alpine, and Arch package managers.
    """
    exec_cmd = _get_exec(session_id)
    platform_service = _get_platform_service(session_id)
    platform = platform_service.get_platform_info()
    package_manager = platform.get("package_manager")

    if not package_manager:
        raise HTTPException(status_code=400, detail="No supported package manager detected on remote host")

    requested = req.packages if req and req.packages else DEFAULT_PACKAGES_BY_MANAGER.get(package_manager, [])
    resolved, skipped = _resolve_packages(requested, package_manager)
    update_first = req.update_first if req else True

    output_lines = [
        f"[PLATFORM] {platform.get('pretty_name') or platform.get('os')}",
        f"[PACKAGE_MANAGER] {package_manager}"
    ]
    installed: List[str] = []
    failed: List[str] = []

    if skipped:
        for package in skipped:
            output_lines.append(f"[SKIP] {package}: not applicable for {package_manager}")

    update_command = _build_update_command(package_manager)
    if update_first and update_command:
        result = exec_cmd(update_command, timeout=180)
        output_lines.append(f"[UPDATE] exit={result['exit_code']}")
        if result["stderr"]:
            output_lines.append(result["stderr"][:500])

    for package in resolved:
        cmd = _build_install_command(package_manager, package)
        result = exec_cmd(cmd, timeout=300)

        if result["exit_code"] == 0:
            installed.append(package)
            output_lines.append(f"[OK] {package}")
        else:
            failed.append(package)
            error = (result["stderr"] or result["stdout"])[:300]
            output_lines.append(f"[FAIL] {package}: {error}")

    status = "completed" if not failed else "partial" if installed else "failed"

    return SetupResult(
        status=status,
        installed=installed,
        failed=failed,
        output="\n".join(output_lines),
        package_manager=package_manager,
        platform={
            "os": platform.get("os"),
            "family": platform.get("family"),
            "pretty_name": platform.get("pretty_name"),
            "version_id": platform.get("version_id")
        },
        resolved_packages=resolved
    )

from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.firewall import FirewallService
from ..services.manager import SessionManager

router = APIRouter(prefix="/firewall", tags=["Firewall"])
manager = SessionManager()


class Protocol(str, Enum):
    tcp = "tcp"
    udp = "udp"
    icmp = "icmp"
    all = "all"


class Chain(str, Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    FORWARD = "FORWARD"


class Target(str, Enum):
    ACCEPT = "ACCEPT"
    DROP = "DROP"
    REJECT = "REJECT"
    LOG = "LOG"


class IpVersion(str, Enum):
    ipv4 = "ipv4"
    ipv6 = "ipv6"
    both = "both"


class RuleRequest(BaseModel):
    chain: Chain = Field(default=Chain.INPUT)
    protocol: Protocol = Field(default=Protocol.tcp)
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    source: Optional[str] = Field(default=None)
    destination: Optional[str] = Field(default=None)
    target: Target = Field(default=Target.ACCEPT)
    ip_version: IpVersion = Field(default=IpVersion.both)
    comment: Optional[str] = Field(default=None)


class PortRangeRequest(BaseModel):
    chain: Chain = Field(default=Chain.INPUT)
    protocol: Protocol = Field(default=Protocol.tcp)
    port_start: int = Field(..., ge=1, le=65535)
    port_end: int = Field(..., ge=1, le=65535)
    source: Optional[str] = Field(default=None)
    target: Target = Field(default=Target.ACCEPT)
    ip_version: IpVersion = Field(default=IpVersion.both)


def _get_firewall(session_id: str = None) -> FirewallService:
    if session_id:
        session = manager.get_session(session_id)
    else:
        session = manager.get_default_session()
    if not session:
        raise HTTPException(status_code=404, detail="No active session")
    return FirewallService(session.exec_command)


@router.get("/backend")
async def get_backend(session_id: str = None) -> dict:
    """Detect the active firewall backend for the remote host."""
    firewall = _get_firewall(session_id)
    return {"firewall": firewall.get_backend_info()}


@router.get("/rules")
async def list_rules(
    chain: Optional[Chain] = None,
    ip_version: IpVersion = IpVersion.both,
    session_id: str = None
) -> dict:
    """List firewall rules using the detected backend."""
    firewall = _get_firewall(session_id)
    return firewall.list_rules(chain.value if chain else None, ip_version.value)


@router.get("/rules/raw")
async def list_rules_raw(
    ip_version: IpVersion = IpVersion.both,
    session_id: str = None
) -> dict:
    """List raw firewall rules for backup/debugging."""
    firewall = _get_firewall(session_id)
    return firewall.list_rules_raw(ip_version.value)


@router.post("/rule")
async def add_rule(req: RuleRequest, session_id: str = None) -> dict:
    """Add a firewall rule."""
    firewall = _get_firewall(session_id)
    return firewall.add_rule(
        chain=req.chain.value,
        protocol=req.protocol.value,
        port=req.port,
        source=req.source,
        destination=req.destination,
        target=req.target.value,
        ip_version=req.ip_version.value,
        comment=req.comment
    )


@router.delete("/rule")
async def delete_rule(
    chain: Chain,
    rule_num: int = Query(..., ge=1),
    ip_version: IpVersion = IpVersion.both,
    session_id: str = None
) -> dict:
    """Delete a firewall rule by line number when supported by the backend."""
    firewall = _get_firewall(session_id)
    return firewall.delete_rule(chain.value, rule_num, ip_version.value)


@router.post("/rule/port-range")
async def add_port_range_rule(req: PortRangeRequest, session_id: str = None) -> dict:
    """Add a firewall rule for a port range."""
    firewall = _get_firewall(session_id)
    return firewall.add_port_range_rule(
        chain=req.chain.value,
        protocol=req.protocol.value,
        port_start=req.port_start,
        port_end=req.port_end,
        source=req.source,
        target=req.target.value,
        ip_version=req.ip_version.value
    )


@router.post("/flush")
async def flush_rules(
    chain: Optional[Chain] = None,
    ip_version: IpVersion = IpVersion.both,
    session_id: str = None
) -> dict:
    """Flush firewall rules for a chain or the entire filter table."""
    firewall = _get_firewall(session_id)
    return firewall.flush_rules(chain.value if chain else None, ip_version.value)


@router.post("/save")
async def save_rules(session_id: str = None) -> dict:
    """Persist firewall rules using the detected backend."""
    firewall = _get_firewall(session_id)
    return firewall.save_rules()


@router.post("/restore")
async def restore_rules(session_id: str = None) -> dict:
    """Restore or reload persisted firewall rules using the detected backend."""
    firewall = _get_firewall(session_id)
    return firewall.restore_rules()


@router.post("/policy")
async def set_policy(
    chain: Chain,
    target: Target = Target.ACCEPT,
    ip_version: IpVersion = IpVersion.both,
    session_id: str = None
) -> dict:
    """Set default policy for a firewall chain when supported."""
    firewall = _get_firewall(session_id)
    return firewall.set_policy(chain.value, target.value, ip_version.value)


@router.post("/allow/port")
async def allow_port(
    port: int = Query(..., ge=1, le=65535),
    protocol: Protocol = Protocol.tcp,
    source: Optional[str] = None,
    ip_version: IpVersion = IpVersion.both,
    session_id: str = None
) -> dict:
    """Allow traffic to a port."""
    firewall = _get_firewall(session_id)
    return firewall.allow_port(port, protocol.value, source, ip_version.value)


@router.post("/block/port")
async def block_port(
    port: int = Query(..., ge=1, le=65535),
    protocol: Protocol = Protocol.tcp,
    ip_version: IpVersion = IpVersion.both,
    session_id: str = None
) -> dict:
    """Block traffic to a port."""
    firewall = _get_firewall(session_id)
    return firewall.block_port(port, protocol.value, ip_version.value)


@router.post("/block/ip")
async def block_ip(
    ip: str,
    ip_version: IpVersion = IpVersion.both,
    session_id: str = None
) -> dict:
    """Block all traffic from an IP address."""
    firewall = _get_firewall(session_id)
    return firewall.block_ip(ip, ip_version.value)


@router.post("/allow/ip")
async def allow_ip(
    ip: str,
    ip_version: IpVersion = IpVersion.both,
    session_id: str = None
) -> dict:
    """Allow all traffic from an IP address."""
    firewall = _get_firewall(session_id)
    return firewall.allow_ip(ip, ip_version.value)

"""Wrapper nipis untuk Incus CLI. Setiap command di-log supaya pelajar nampak."""
import json
import subprocess
from dataclasses import dataclass, field

LOG: list[str] = []  # global command log, dipaparkan dalam UI

LAB_PREFIX = "lab-"
TARGET = "lab-target"
SCANNER = "lab-scanner"
IMAGE = "images:debian/13"


def _run(args: list[str], timeout: int = 120) -> tuple[int, str, str]:
    """Jalankan command, log, return (rc, stdout, stderr)."""
    cmd = " ".join(args)
    LOG.append(f"$ {cmd}")
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        if p.stdout.strip():
            LOG.append(p.stdout.strip())
        if p.stderr.strip():
            LOG.append(f"[stderr] {p.stderr.strip()}")
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        LOG.append(f"[timeout selepas {timeout}s]")
        return 124, "", "timeout"
    except FileNotFoundError:
        LOG.append("[error] incus CLI tak dijumpai")
        return 127, "", "incus not found"


@dataclass
class Container:
    name: str
    status: str
    ipv4: str
    image: str
    arch: str
    roles: list[str] = field(default_factory=list)


def list_lab() -> list[Container]:
    """Senarai container yang bermula dengan 'lab-'."""
    rc, out, _ = _run(["incus", "list", "--format", "json"])
    if rc != 0:
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return []

    result = []
    for c in data:
        name = c.get("name", "")
        if not name.startswith(LAB_PREFIX):
            continue

        # ambil IPv4 dari state.network
        ipv4 = "-"
        network = (c.get("state") or {}).get("network") or {}
        for iface in network.values():
            for addr in iface.get("addresses", []):
                if addr.get("family") == "inet" and addr.get("scope") == "global":
                    ipv4 = addr.get("address", "-")
                    break

        roles = []
        if name == TARGET:
            roles.append("target")
        if name == SCANNER:
            roles.append("scanner")

        result.append(Container(
            name=name,
            status=c.get("status", "Unknown"),
            ipv4=ipv4,
            image=(c.get("config") or {}).get("image.os", "debian"),
            arch=c.get("architecture", "-"),
            roles=roles,
        ))
    return result


def create_lab() -> None:
    """Buat lab: scanner + target, install nmap/nginx, expose port."""
    # 1. launch container
    for name in (TARGET, SCANNER):
        _run(["incus", "launch", IMAGE, name])

    # 2. tunggu ready (ringkas: retry exec sehingga berjaya)
    for name in (TARGET, SCANNER):
        for _ in range(30):
            rc, _, _ = _run(["incus", "exec", name, "--", "true"], timeout=10)
            if rc == 0:
                break
            import time
            time.sleep(2)

    # 3. install nginx dalam target
    _run([
        "incus", "exec", TARGET, "--", "bash", "-lc",
        "export DEBIAN_FRONTEND=noninteractive; "
        "apt-get update && apt-get install -y nginx",
    ], timeout=300)

    # 4. install nmap dalam scanner
    _run([
        "incus", "exec", SCANNER, "--", "bash", "-lc",
        "export DEBIAN_FRONTEND=noninteractive; "
        "apt-get update && apt-get install -y nmap",
    ], timeout=300)

    # 5. expose nginx target pada host 8081
    _run([
        "incus", "config", "device", "add", TARGET, "web",
        "proxy", "listen=tcp:127.0.0.1:8081",
        "connect=tcp:127.0.0.1:80",
    ])


def destroy_lab() -> None:
    for name in (TARGET, SCANNER):
        _run(["incus", "delete", "--force", name])


def run_nmap(target_name: str) -> tuple[int, str]:
    """Jalankan nmap dari scanner ke target."""
    target = target_name if target_name.startswith(LAB_PREFIX) else f"{LAB_PREFIX}{target_name}"
    rc, out, err = _run([
        "incus", "exec", SCANNER, "--",
        "nmap", "-Pn", "-T4", "-F", target,
    ], timeout=60)
    return rc, out or err


def run_ping(source: str, target: str) -> tuple[int, str]:
    """Ping dari source ke target."""
    src = source if source.startswith(LAB_PREFIX) else f"{LAB_PREFIX}{source}"
    dst = target if target.startswith(LAB_PREFIX) else f"{LAB_PREFIX}{target}"
    rc, out, err = _run([
        "incus", "exec", src, "--",
        "ping", "-n", "-c", "4", "-i", "1", dst,
    ], timeout=30)
    return rc, out or err


def run_ip_addr(container_name: str) -> tuple[int, str]:
    """Tunjukkan alamat IP pada container."""
    name = container_name if container_name.startswith(LAB_PREFIX) else f"{LAB_PREFIX}{container_name}"
    rc, out, err = _run(["incus", "exec", name, "--", "ip", "addr"], timeout=15)
    return rc, out or err


def run_ip_route(container_name: str) -> tuple[int, str]:
    """Tunjukkan routing table pada container."""
    name = container_name if container_name.startswith(LAB_PREFIX) else f"{LAB_PREFIX}{container_name}"
    rc, out, err = _run(["incus", "exec", name, "--", "ip", "route"], timeout=15)
    return rc, out or err


def run_ip_neigh(container_name: str) -> tuple[int, str]:
    """Tunjukkan neighbour/ARP table pada container."""
    name = container_name if container_name.startswith(LAB_PREFIX) else f"{LAB_PREFIX}{container_name}"
    rc, out, err = _run(["incus", "exec", name, "--", "ip", "neigh"], timeout=15)
    return rc, out or err

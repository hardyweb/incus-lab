"""Wrapper nipis untuk Incus CLI. Setiap command di-log supaya pelajar nampak."""
import fcntl
import json
import os
import pty
import select
import struct
import subprocess
import termios
import threading
from dataclasses import dataclass, field

LOG: list[str] = []  # global command log, dipaparkan dalam UI

LAB_PREFIX = "lab-"
TARGET = "lab-target"
SCANNER = "lab-scanner"
IMAGE = "images:debian/13"


def _run(args: list[str], timeout: int = 120, log: bool = True) -> tuple[int, str, str]:
    """Jalankan command, log, return (rc, stdout, stderr)."""
    cmd = " ".join(args)

    def _append(line: str) -> None:
        if log:
            LOG.append(line)

    _append(f"$ {cmd}")
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        if p.stdout.strip():
            _append(p.stdout.strip())
        if p.stderr.strip():
            _append(f"[stderr] {p.stderr.strip()}")
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        _append(f"[timeout selepas {timeout}s]")
        return 124, "", "timeout"
    except FileNotFoundError:
        _append("[error] incus CLI tak dijumpai")
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
    rc, out, _ = _run(["incus", "list", "--format", "json"], log=False)
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

    # 5. install netcat + curl dalam scanner
    _run([
        "incus", "exec", SCANNER, "--", "bash", "-lc",
        "export DEBIAN_FRONTEND=noninteractive; "
        "apt-get update && apt-get install -y netcat-openbsd curl",
    ], timeout=300)

    # 6. install dnsutils (dig, nslookup)
    _run([
        "incus", "exec", SCANNER, "--", "bash", "-lc",
        "export DEBIAN_FRONTEND=noninteractive; "
        "apt-get install -y dnsutils",
    ], timeout=300)

    # 6. expose nginx target pada host 8081
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


def run_ss(container_name: str) -> tuple[int, str]:
    """Tunjukkan socket yang sedang LISTEN."""
    name = container_name if container_name.startswith(LAB_PREFIX) else f"{LAB_PREFIX}{container_name}"
    rc, out, err = _run(["incus", "exec", name, "--", "ss", "-tlnp"], timeout=15)
    return rc, out or err


def run_nc(container_name: str, host: str, port: int, timeout: int = 5) -> tuple[int, str]:
    """Uji sambungan TCP dengan netcat (nc -z)."""
    name = container_name if container_name.startswith(LAB_PREFIX) else f"{LAB_PREFIX}{container_name}"
    rc, out, err = _run([
        "incus", "exec", name, "--",
        "nc", "-z", "-w", str(timeout), host, str(port)
    ], timeout=timeout + 5)
    return rc, out or err


def run_curl(container_name: str, url: str) -> tuple[int, str]:
    """Ambila output HTTP dengan curl."""
    name = container_name if container_name.startswith(LAB_PREFIX) else f"{LAB_PREFIX}{container_name}"
    rc, out, err = _run([
        "incus", "exec", name, "--",
        "curl", "-s", "-S", "-L", url
    ], timeout=15)
    return rc, out or err


def run_dig(container_name: str, domain: str, record_type: str = "A") -> tuple[int, str]:
    """Jalankan dig untuk domain tertentu."""
    name = container_name if container_name.startswith(LAB_PREFIX) else f"{LAB_PREFIX}{container_name}"
    rc, out, err = _run([
        "incus", "exec", name, "--",
        "dig", "+short", "-t", record_type, domain
    ], timeout=15)
    return rc, out or err


def run_nslookup(container_name: str, domain: str) -> tuple[int, str]:
    """Jalankan nslookup untuk domain tertentu."""
    name = container_name if container_name.startswith(LAB_PREFIX) else f"{LAB_PREFIX}{container_name}"
    rc, out, err = _run([
        "incus", "exec", name, "--",
        "nslookup", domain
    ], timeout=15)
    return rc, out or err


class TerminalSession:
    """Sesi terminal interaktif dalam container melalui pty + WebSocket."""

    def __init__(self, container_name: str, emit, sid: str):
        self.sid = sid
        self._emit = emit
        self._running = False
        name = container_name if container_name.startswith(LAB_PREFIX) else f"{LAB_PREFIX}{container_name}"
        self.master, slave = pty.openpty()
        self.proc = subprocess.Popen(
            ["incus", "exec", name, "--", "bash", "--login"],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            preexec_fn=os.setsid,
            env={**os.environ, "TERM": "xterm-256color"},
            close_fds=True,
        )
        os.close(slave)
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self) -> None:
        while self._running:
            try:
                ready, _, _ = select.select([self.master], [], [], 0.1)
            except (OSError, ValueError):
                break
            if self.master not in ready:
                continue
            try:
                data = os.read(self.master, 4096)
            except OSError:
                break
            if not data:
                break
            self._emit(
                "terminal_output",
                {"data": data.decode("utf-8", errors="replace")},
                room=self.sid,
            )
        self._running = False
        self._emit("terminal_exit", {}, room=self.sid)

    def write(self, data: str) -> None:
        if self._running:
            try:
                os.write(self.master, data.encode("utf-8", errors="replace"))
            except OSError:
                pass

    def resize(self, cols: int, rows: int) -> None:
        try:
            fcntl.ioctl(
                self.master,
                termios.TIOCSWINSZ,
                struct.pack("HHHH", rows, cols, 0, 0),
            )
        except OSError:
            pass

    def close(self) -> None:
        self._running = False
        try:
            os.close(self.master)
        except OSError:
            pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=2)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                self.proc.kill()
            except ProcessLookupError:
                pass

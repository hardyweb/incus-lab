# Walkthrough

## 2026-09-16 — Phase 3 DNS (dig, nslookup)
- Tambah `run_dig`, `run_nslookup` dalam `incus.py` (spawn `incus exec <lab> -- dig/nclookup`).
- Tambah endpoint `/api/dig`, `/api/nslookup` dalam `app.py` (GET dengan query params: domain, record_type).
- Update `create_lab`: install `dnsutils` (bind9-dnsutils → dig, nslookup) pada `lab-scanner`.
- UI: section **DNS** (dig: domain + record type select A/AAAA/CNAME/MX/NS/TXT/SOA), **nslookup** (domain) dalam `index.html`.
- `app.js`: handlers untuk `btn-dig`, `btn-nslookup` → call API, render output + log.
- Verification:
  - `dig -t A lab-target` → 10.120.238.186
  - `dig -t AAAA lab-target` → fe80::1266:6aff:fea7:6aa8, fd42:e1a0:bd70:f667:1266:6aff:fea7:6aa8
  - `dig -t MX lab-target` → '' (tiada MX record, expected)
  - `dig -t A unknown.example.com` → '' (NXDOMAIN)
  - `nslookup lab-target` → Server 127.0.0.53, Non-authoritative answer: 10.120.238.186 + IPv6
  - `nslookup google.com` → resolves to 173.194.41.139, 173.194.41.10 (real internet DNS)
  - All endpoints return 200
- Mental Anchor: Phase 3 backend + UI selesai. Semua berfungsi.

## 2026-09-16 — Phase 2 Ports & Services (ss, nc, curl)
- Tambah `run_ss`, `run_nc`, `run_curl` dalam `incus.py` (spawn `incus exec <lab> -- ss/nc/curl`).
- Tambah endpoint `/api/ss`, `/api/nc`, `/api/curl` dalam `app.py` (GET dengan query params).
- Update `create_lab`: install `nmap`, `netcat-openbsd`, `curl` pada `lab-scanner`.
- UI: section **Ports & Services** (ss button), **Netcat (nc)** (host/port input + button), **Curl** (URL input + button) dalam `index.html`.
- `app.js`: handlers untuk `btn-ss`, `btn-nc`, `btn-curl` → call API, render output + log.
- Verification: 
  - `ss` pada lab-scanner → ok, output shows LISTEN sockets (systemd-resolve DNS on 127.0.0.53:53, [::]:5355)
  - `nc -z lab-target 80` → ok, output: "Connection to lab-target (fd42:e1a0:bd70:f667:1266:6aff:fea7:6aa8) 80 port [tcp/http] succeeded!"
  - `curl http://lab-target/` → ok, output len 615, starts with "<!DOCTYPE html><html><head><title>Welcome to nginx!</title>"
- Mental Anchor: Phase 2 backend + UI selesai. Semua berfungsi seperti di atas.

## 2026-09-16 — xterm.js interactive terminal (Socket.IO + pty)
- Added `TerminalSession` in `incus.py`: spawn `incus exec <lab> -- bash --login` dengan pty, thread baca master fd, resize via TIOCSWINSZ, cleanup pada close.
- Added `flask-socketio` (`requirements.txt`) dan handlers dalam `app.py`: `terminal_start`, `terminal_input`, `terminal_resize`, `terminal_stop`, `disconnect`; server run guna `socketio.run`.
- UI: xterm.js + addon-fit + Socket.IO client (CDN) dalam `index.html`; section Terminal (select container + Open/Close) dalam panel kawalan; `#terminal-wrap` dalam panel topology; styling dalam `style.css`.
- `app.js`: `ensureTerminal()`, `openTerminal()`, `closeTerminal()`, status indicator, fit on resize.
- Verification: `node --check` OK; `ast.parse` OK; unit test `TerminalSession` pada `lab-scanner` → prompt root, `TERMINAL_OK`, hostname `lab-scanner`, user `root`, event `terminal_exit` diterima; Socket.IO handshake `EIO=4` OK; halaman memuatkan asset xterm/socket.io.
- Catatan: server lama pada port 8081 (proses lama tanpa Socket.IO) perlu direstart sebelum terminal berfungsi.
- Mental Anchor: terminal berfungsi di peringkat backend + wiring. Seterusnya restart app pada 8081 dan uji di browser.
- Tindakan: dengan kebenaran pengguna, hentikan pid 7293 (kod lama), restart `.venv/bin/python app.py` pada 8081. Disahkan `/api/containers` 200 dan Socket.IO handshake `EIO=4` OK. Terminal kini aktif di http://127.0.0.1:8081.

## 2026-09-16 — Filter `incus list --format json` from command log
- Added `log` parameter to `_run()` in `incus.py` to control command logging. Set `log=False` for `incus list --format json` in `list_lab()` to exclude it from the visible command log in UI.
- Updated `list_lab()` to pass `log=False` when calling `_run`.
- Verification: `python -m compileall` OK, `/api/containers` log no longer contains the list command.

## 2026-09-16 — Fix frontend crash + add Clear button
- Diagnosed: `static/app.js` was duplicated (full file content written twice) → `let animFrame`/`let currentArrow` redeclared → `SyntaxError` → whole script failed to load, all buttons dead.
- Rewrote `static/app.js` cleanly (272 lines, no duplicates), added `try/catch` on every handler and `api()` rejects on `!res.ok`.
- Added `btn-clear` (Clear) button in `templates/index.html` and handler in `app.js` to clear Command log, Output, and topology packets.
- Verification: `node --check` OK, `python -m compileall` OK, live Flask test confirmed `/api/containers`, `/api/ip-addr`, `/api/ip-route`, `/api/ip-neigh` all return 200 with real container output.

## 2026-09-16 — Phase 1 Connectivity implementation
- Added `run_ip_addr`, `run_ip_route`, and `run_ip_neigh` to `incus.py`
- Added `/api/ip-addr`, `/api/ip-route`, `/api/ip-neigh` routes to `app.py`
- Extended UI with Connectivity section: `ip addr`, `ip route`, `ip neigh`
- Mental Anchor: Phase 1 backend + UI implemented. Next step is verification and commit.
- Verification: pending


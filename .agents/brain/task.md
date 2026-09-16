# Task Ledger

## Current
- What are we doing? — Phase 3 DNS (dig, nslookup) completed. Next: Phase 4 Routing.
- Why? — Pelajar boleh uji DNS resolution, record types, dan nslookup

## Completed
- `[x]` Scaffold project state (.agents/brain)
- `[x]` Add run_ip_addr, run_ip_route, run_ip_neigh to incus.py
- `[x]` Add /api/ip-addr, /api/ip-route, /api/ip-neigh routes to app.py
- `[x]` Add run_ss, run_nc, run_curl ke incus.py
- `[x]` Add /api/ss, /api/nc, /api/curl endpoints ke app.py
- `[x]` Update create_lab: install nmap, netcat, curl, dnsutils pada lab-scanner
- `[x]` Add Phase 2 UI controls (ss, nc, curl sections) ke index.html
- `[x]` Add Phase 2 client handlers ke app.js
- `[x]` Add run_dig, run_nslookup ke incus.py
- `[x]` Add /api/dig, /api/nslookup endpoints ke app.py
- `[x]` Add Phase 3 UI section (dig, nslookup) ke index.html + app.js
- `[x]` Add xterm.js terminal + Socket.IO (TerminalSession pty) untuk lab containers
- `[x]` Add Clear button for Command log + Output
- `[x]` Filter `incus list --format json` dari command log

## Blocked
- `[ ]` — none

## Next
- `[ ]` Phase 4 — Routing (traceroute, routing table, multi-hop topology)
- `[ ]` Phase 5 — Packet: tcpdump, ICMP, ARP, TCP SYN, DNS packet
- `[ ]` Phase 6 — Troubleshooting: ping fails, DNS fails, port closed, service stopped, wrong route

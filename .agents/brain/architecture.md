# Architecture — Incus Lab

## Overview
Incus Lab is a visual web application that helps students learn networking concepts (ping, nmap, traceroute, DNS, packet inspection) through interactive Incus containers.

## Stack
| Layer | Technology |
|---|---|
| Language | Python 3 |
| Web Framework | Flask 3.x |
| Container Runtime | Incus (LXD-compatible) |
| Base Image | `images:debian/13` |
| Lab Containers | `lab-target` (nginx), `lab-scanner` (nmap) |
| Frontend | HTML templates + static assets (vanilla) |
| API | Flask REST endpoints on `127.0.0.1:8081` |

## Structure
```
incus-lab/
├── app.py              # Flask web app + API routes
├── incus.py            # Thin Incus CLI wrapper with command logging
├── start.sh            # Setup script (venv, deps, launch)
├── requirements.txt    # flask>=3.0
├── templates/          # HTML templates
├── static/             # Static assets (CSS/JS)
├── .venv/              # Python virtual environment
└── .agents/brain/      # Project state (this file)
```

## Design Principle
Every Incus command is logged (`incus.py` LOG list) so students can see exactly what command was run and its output. The UI surfaces this log alongside results.

## Roadmap
- **PHASE 1** ✅ Connectivity: ping, ip addr, ip route, ip neigh
- **PHASE 2** ✅ Ports & Services: nmap, ss, nc, curl
- **PHASE 3** ✅ DNS: dig, nslookup, DNS records
- **PHASE 4** — Routing: traceroute, routing table, multi-hop topology
- **PHASE 5** — Packet: tcpdump, ICMP, ARP, TCP SYN, DNS packet
- **PHASE 6** — Troubleshooting: ping fails, DNS fails, port closed, service stopped, wrong route

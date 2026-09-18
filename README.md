# Incus Lab — Panduan Pelajar (Windows 11 + WSL2 + Debian)

Incus Lab ialah aplikasi web visual untuk belajar konsep rangkaian (ping, nmap, traceroute, DNS, packet inspection) melalui container Incus yang interaktif.

---

## 1. Prasyarat (Windows 11)

### 1.1 Aktifkan WSL2
Buka **PowerShell sebagai Administrator** dan jalankan:

```powershell
wsl --install
```

> Perintah ini akan mengaktifkan *Virtual Machine Platform*, *Windows Subsystem for Linux*, dan memasang **Ubuntu** secara lalai. Selepas selesai, **restart komputer**.

### 1.2 Tukar Distro ke Debian (Pilihan)
Jika anda mahu Debian (bukan Ubuntu), selepas restart:

```powershell
# Senarai distro yang tersedia
wsl --list --online

# Pasang Debian
wsl --install -d Debian

# Jadikan Debian lalai
wsl --set-default Debian
```

### 1.3 Masuk ke Debian WSL
Buka **Windows Terminal** atau **Command Prompt**, taip:

```cmd
wsl -d Debian
```

Anda kini berada di shell Linux (Debian) di dalam Windows.

---

## 2. Pasang Incus di dalam Debian WSL

### 2.1 Kemas kini pakej & pasang prasyarat
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y gnupg2 curl software-properties-common
```

### 2.2 Tambah repositori Incus (stabil)
```bash
# Kunci GPG
curl -fsSL https://pkgs.zabbly.com/key.asc | sudo gpg --dearmor -o /usr/share/keyrings/zabbly.gpg

# Repo
echo "deb [signed-by=/usr/share/keyrings/zabbly.gpg] https://pkgs.zabbly.com/incus/stable $(. /etc/os-release && echo $VERSION_CODENAME) main" | sudo tee /etc/apt/sources.list.d/zabbly-incus-stable.list

sudo apt update
```

### 2.3 Pasang Incus
```bash
sudo apt install -y incus
```

### 2.4 Inisialisasi Incus (minimal)
```bash
sudo incus admin init --minimal
```
> Ikut prom: pilih *storage pool* `dir` (senang untuk WSL), jangan aktifkan cluster, jangan aktifkan IPv6 jika tidak diperlukan.

### 2.5 Tambah pengguna ke kumpulan `incus-admin`
```bash
sudo usermod -aG incus-admin $USER
newgrp incus-admin
```
> **Penting:** Log keluar & log masuk semula WSL (atau `exec bash`) agar perubahan kumpulan berkuat kuasa.

### 2.6 Uji Incus
```bash
incus list
```
Seharusnya papar jadual kosong (tiada container lagi).

---

## 3. Klon & Jalankan Incus Lab

### 3.1 Pasang Git (jika belum)
```bash
sudo apt install -y git
```

### 3.2 Klon repositori
```bash
cd ~
git clone https://github.com/<username>/incus-lab.git
cd incus-lab
```
> Gantikan `<username>` dengan nama pengguna GitHub anda, atau gunakan URL repositori sebenar.

### 3.3 Jalankan skrip permulaan
```bash
chmod +x start.sh
./start.sh
```

Skrip ini akan:
1. Semak Incus wujud & pengguna dalam `incus-admin`
2. Cipta virtual environment Python (`.venv/`)
3. Pasang kebergantungan (`flask`, `flask-socketio`)
4. Mulakan server pada **http://127.0.0.1:8081**

### 3.4 Akses UI
Buka pelayar web di **Windows** (Chrome/Edge/Firefox) dan pergi ke:

```
http://127.0.0.1:8081
```

> WSL2 *port forwarding* automatik — port 8081 di dalam WSL boleh diakses terus dari Windows.

---

## 4. Fasa-Fasa Pembelajaran (Roadmap)

| Fasa | Topik | Status | Alat/UI |
|------|-------|--------|---------|
| **1** | **Connectivity** — `ping`, `ip addr`, `ip route`, `ip neigh` | ✅ Selesai | Butang: `ip addr`, `ip route`, `ip neigh` |
| **2** | **Ports & Services** — `nmap`, `ss`, `nc`, `curl` | ✅ Selesai | Butang: `ss`, `nc` (host/port), `curl` (URL) |
| **3** | **DNS** — `dig`, `nslookup`, record types | ✅ Selesai | `dig` (domain + record type), `nslookup` (domain) |
| **4** | **Routing** — `traceroute`, routing table, multi-hop | 🔄 Berikutnya | — |
| **5** | **Packet** — `tcpdump`, ICMP, ARP, TCP SYN, DNS packet | 📅 Dirancang | — |
| **6** | **Troubleshooting** — ping gagal, DNS gagal, port tertutup, service stopped, wrong route | 📅 Dirancang | — |

Setiap fasa menambah butang/panel baru di UI. Log perintah Incus dipaparkan di panel **Command Log** — pelajar boleh lihat command sebenar yang dijalankan dan outputnya.

---

## 5. Arsitektur Ringkas

```
incus-lab/
├── app.py              # Flask web app + REST API + Socket.IO
├── incus.py            # Wrapper tipis CLI Incus (log setiap command)
├── start.sh            # Skrip setup + jalankan
├── requirements.txt    # flask, flask-socketio
├── templates/          # HTML (index.html)
├── static/             # CSS + JS (app.js, style.css)
├── .venv/              # Python venv (dicipta start.sh)
└── .agents/brain/      # State projek (untuk pembangun)
```

- **Container lalai:** `lab-target` (nginx), `lab-scanner` (nmap + alat rangkaian)
- **Imej asas:** `images:debian/13`
- **Port API:** `127.0.0.1:8081`

---

## 6. Perintah Berguna (WSL / Incus)

| Perintah | Kegunaan |
|----------|----------|
| `wsl -l -v` | Senarai distro WSL & versi |
| `wsl --terminate Debian` | Hentikan WSL Debian sepenuhnya |
| `incus list` | Senarai container |
| `incus info` | Maklumat Incus (storage, network, dsb.) |
| `incus exec lab-scanner -- bash` | Masuk shell container scanner |
| `sudo systemctl restart incus` | Restart daemon Incus (jika perlu) |

---

## 7. Penyelesaian Masalah (Troubleshooting)

| Masalah | Penyelesaian |
|---------|--------------|
| `incus` not found | Ikut langkah **Bahagian 2** untuk pasang Incus |
| `Error: not a member of incus-admin` | Jalankan `sudo usermod -aG incus-admin $USER && newgrp incus-admin`, lalu `exec bash` |
| Port 8081 sudah digunakan | Hentikan proses lama: `pkill -f "python app.py"` lalu jalankan `./start.sh` semula |
| Container tidak nampak di UI | Pastikan Incus daemon berjalan: `systemctl status incus` (atau `service incus status`) |
| `ModuleNotFoundError: flask` | Jalankan `./start.sh` semula (akan pasang deps ke `.venv/`) |

---



### Perintah Pembangun
```bash
# Mulakan server pembangunan
./start.sh

# Uji sintaks Python
python -m compileall .

# Uji JS (Node perlu dipasang)
node --check static/app.js
```

---

## 8. Lesen
Projek ini dikongsi untuk tujuan pembelajaran. Sila rujuk fail `LICENSE` (jika ada) untuk terma penggunaan.

---

**Selamat belajar rangkaian dengan Incus Lab!** 🚀  
Soalan? Buka *Issue* di repositori GitHub.

#!/usr/bin/env bash
# Setup ringkas + jalankan Incus Lab.
set -e

cd "$(dirname "$0")"

# 1. pastikan incus ada
if ! command -v incus >/dev/null 2>&1; then
  echo "Incus tak dijumpai. Pasang dulu:"
  echo "  sudo apt install -y incus && sudo incus admin init --minimal"
  exit 1
fi

# 2. pastikan user dalam incus-admin
if ! id -nG "$USER" | grep -qw incus-admin; then
  echo "Tambah diri ke kumpulan incus-admin dulu:"
  echo "  sudo usermod -aG incus-admin \$USER && newgrp incus-admin"
  exit 1
fi

# 3. venv + deps
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
./.venv/bin/pip install -q -r requirements.txt

# 4. jalan
echo "Incus Lab: http://127.0.0.1:8080"
exec ./.venv/bin/python app.py

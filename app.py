"""Incus Lab — visualiser ringkas untuk ajar ping & nmap."""
from flask import Flask, jsonify, render_template, request

import incus

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/containers")
def api_containers():
    return jsonify({
        "containers": [c.__dict__ for c in incus.list_lab()],
        "log": incus.LOG[-20:],  # 20 baris terakhir
    })


@app.post("/api/lab/create")
def api_create():
    incus.create_lab()
    return jsonify({"ok": True, "log": incus.LOG[-30:]})


@app.post("/api/lab/destroy")
def api_destroy():
    incus.destroy_lab()
    return jsonify({"ok": True, "log": incus.LOG[-30:]})


@app.post("/api/scan")
def api_scan():
    target = request.json.get("target", incus.TARGET)
    rc, out = incus.run_nmap(target)
    return jsonify({"ok": rc == 0, "output": out, "log": incus.LOG[-20:]})


@app.post("/api/ping")
def api_ping():
    src = request.json.get("source", incus.SCANNER)
    dst = request.json.get("target", incus.TARGET)
    rc, out = incus.run_ping(src, dst)
    return jsonify({"ok": rc == 0, "output": out, "log": incus.LOG[-20:]})


@app.get("/api/ip-addr")
def api_ip_addr():
    target = request.args.get("target", incus.SCANNER)
    rc, out = incus.run_ip_addr(target)
    return jsonify({"ok": rc == 0, "output": out, "log": incus.LOG[-20:]})


@app.get("/api/ip-route")
def api_ip_route():
    target = request.args.get("target", incus.SCANNER)
    rc, out = incus.run_ip_route(target)
    return jsonify({"ok": rc == 0, "output": out, "log": incus.LOG[-20:]})


@app.get("/api/ip-neigh")
def api_ip_neigh():
    target = request.args.get("target", incus.SCANNER)
    rc, out = incus.run_ip_neigh(target)
    return jsonify({"ok": rc == 0, "output": out, "log": incus.LOG[-20:]})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8081, debug=False)

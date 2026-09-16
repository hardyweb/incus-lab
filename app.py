"""Incus Lab — visualiser ringkas untuk ajar ping & nmap."""
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit

import incus

app = Flask(__name__)
app.config["SECRET_KEY"] = "incus-lab"
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

terminal_sessions: dict[str, incus.TerminalSession] = {}


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


@app.get("/api/ss")
def api_ss():
    target = request.args.get("target", incus.SCANNER)
    rc, out = incus.run_ss(target)
    return jsonify({"ok": rc == 0, "output": out, "log": incus.LOG[-20:]})


@app.get("/api/nc")
def api_nc():
    target = request.args.get("target", incus.SCANNER)
    host = request.args.get("host")
    port = request.args.get("port", type=int)
    timeout = request.args.get("timeout", type=int, default=5)
    if not host or not port:
        return jsonify({"ok": False, "output": "Missing host or port", "log": []}), 400
    rc, out = incus.run_nc(target, host, port, timeout)
    return jsonify({"ok": rc == 0, "output": out, "log": incus.LOG[-20:]})


@app.get("/api/curl")
def api_curl():
    target = request.args.get("target", incus.SCANNER)
    url = request.args.get("url")
    if not url:
        return jsonify({"ok": False, "output": "Missing URL", "log": []}), 400
    rc, out = incus.run_curl(target, url)
    return jsonify({"ok": rc == 0, "output": out, "log": incus.LOG[-20:]})


@app.get("/api/dig")
def api_dig():
    target = request.args.get("target", incus.SCANNER)
    domain = request.args.get("domain")
    record_type = request.args.get("record_type", "A").upper()
    if not domain:
        return jsonify({"ok": False, "output": "Missing domain", "log": []}), 400
    rc, out = incus.run_dig(target, domain, record_type)
    return jsonify({"ok": rc == 0, "output": out, "log": incus.LOG[-20:]})


@app.get("/api/nslookup")
def api_nslookup():
    target = request.args.get("target", incus.SCANNER)
    domain = request.args.get("domain")
    if not domain:
        return jsonify({"ok": False, "output": "Missing domain", "log": []}), 400
    rc, out = incus.run_nslookup(target, domain)
    return jsonify({"ok": rc == 0, "output": out, "log": incus.LOG[-20:]})


@socketio.on("terminal_start")
def on_terminal_start(data):
    container = (data or {}).get("container", incus.SCANNER)
    sid = request.sid
    if sid in terminal_sessions:
        terminal_sessions[sid].close()
        del terminal_sessions[sid]
    try:
        session = incus.TerminalSession(container, socketio.emit, sid)
        terminal_sessions[sid] = session
        emit("terminal_started", {"ok": True, "container": container})
    except Exception as exc:
        emit("terminal_started", {"ok": False, "error": str(exc)})


@socketio.on("terminal_input")
def on_terminal_input(data):
    session = terminal_sessions.get(request.sid)
    if session and isinstance(data, dict):
        session.write(data.get("data", ""))


@socketio.on("terminal_resize")
def on_terminal_resize(data):
    session = terminal_sessions.get(request.sid)
    if session and isinstance(data, dict):
        session.resize(int(data.get("cols", 80)), int(data.get("rows", 24)))


@socketio.on("terminal_stop")
def on_terminal_stop():
    sid = request.sid
    session = terminal_sessions.pop(sid, None)
    if session:
        session.close()


@socketio.on("disconnect")
def on_disconnect():
    session = terminal_sessions.pop(request.sid, None)
    if session:
        session.close()


if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=8081, debug=False, allow_unsafe_werkzeug=True)

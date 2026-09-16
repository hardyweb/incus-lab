const $ = (id) => document.getElementById(id);

async function api(path, body) {
  const opts = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : { method: "GET" };
  const res = await fetch(path, opts);
  return res.json();
}

function renderContainers(containers) {
  clearPackets();
  const el = $("topology-nodes");
  if (!containers.length) {
    currentArrow = null;
    el.innerHTML = '<p class="empty">Tiada container. Tekan <strong>Create Lab</strong>.</p>';
    return;
  }
  el.innerHTML = containers.map((c) => `
    <div class="card ${c.status === "Running" ? "running" : "stopped"}"
         data-node-name="${c.name}"
         data-node-role="${c.roles[0] || (c.name === "lab-target" ? "target" : "scanner")}">
      <div class="card-name">${c.name}</div>
      <div class="card-role">${c.roles.join(", ") || "-"}</div>
      <div class="card-row"><span>Status</span><b>${c.status}</b></div>
      <div class="card-row"><span>IPv4</span><b>${c.ipv4}</b></div>
      <div class="card-row"><span>Image</span><b>${c.image}</b></div>
      <div class="card-row"><span>Arch</span><b>${c.arch}</b></div>
    </div>
  `).join("");
  if (currentArrow) scheduleRedraw();
}

const STATUS_CLASSES = { ok: "ok", warn: "warn", off: "off" };

function renderStatus(containers) {
  const indicator = $("incus-status");
  const dot = indicator.querySelector(".status-indicator");
  const text = indicator.querySelector(".status-text");
  const running = containers.filter((c) => c.status === "Running");

  dot.className = "status-indicator";
  if (running.length === containers.length && containers.length > 0) {
    dot.classList.add(STATUS_CLASSES.ok);
    text.textContent = `${containers.length} container • semua aktif`;
  } else if (containers.length > 0) {
    dot.classList.add(STATUS_CLASSES.warn);
    text.textContent = `${running.length}/${containers.length} container aktif`;
  } else {
    dot.classList.add(STATUS_CLASSES.off);
    text.textContent = "Tiada container";
  }
}

function renderLog(lines) {
  $("log").textContent = lines.join("\n");
}

async function refresh() {
  const data = await api("/api/containers");
  renderContainers(data.containers);
  renderStatus(data.containers);
  renderLog(data.log);
}

let animFrame = null;
let redrawFrame = null;
let currentArrow = null;

function clearPackets() {
  if (animFrame !== null) {
    cancelAnimationFrame(animFrame);
    animFrame = null;
  }
  const svg = document.getElementById("topology-svg");
  if (svg) svg.querySelectorAll(".topology-arrow, .topology-packet").forEach((el) => el.remove());
}

function getNode(container, name) {
  return container.querySelector(`[data-node-name="${name}"]`);
}

function drawArrow() {
  clearPackets();
  const container = $("topology");
  const svg = document.getElementById("topology-svg");
  if (!container || !svg || !currentArrow) return;

  const fromEl = getNode(container, currentArrow.from);
  const toEl = getNode(container, currentArrow.to);
  if (!fromEl || !toEl || fromEl === toEl) return;

  const color = currentArrow.color;
  const cr = container.getBoundingClientRect();
  const fr = fromEl.getBoundingClientRect();
  const tr = toEl.getBoundingClientRect();

  const forward = fr.left + fr.width / 2 <= tr.left + tr.width / 2;
  let x1, y1, x2, y2, c1x, c1y, c2x, c2y;

  if (tr.top >= fr.bottom - 1) {
    x1 = fr.left + fr.width / 2 - cr.left;
    y1 = fr.bottom - cr.top;
    x2 = tr.left + tr.width / 2 - cr.left;
    y2 = tr.top - cr.top;
    const dy = y2 - y1;
    c1x = x1; c1y = y1 + dy * 0.5;
    c2x = x2; c2y = y2 - dy * 0.5;
  } else {
    x1 = (forward ? fr.right : fr.left) - cr.left;
    x2 = (forward ? tr.left : tr.right) - cr.left;
    y1 = fr.top + fr.height / 2 - cr.top;
    y2 = tr.top + tr.height / 2 - cr.top;
    const dx = x2 - x1;
    c1x = x1 + dx * 0.5; c1y = y1;
    c2x = x2 - dx * 0.5; c2y = y2;
  }

  svg.setAttribute("width", cr.width);
  svg.setAttribute("height", cr.height);

  const pathData = `M ${x1} ${y1} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${x2} ${y2}`;

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", pathData);
  path.setAttribute("class", `topology-arrow ${color || ""}`);
  path.setAttribute("marker-end", `url(#arrowhead${color ? "-" + color : ""})`);
  svg.appendChild(path);

  const packet = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  packet.setAttribute("class", `topology-packet${color ? " " + color : ""}`);
  packet.setAttribute("r", "4");
  svg.appendChild(packet);

  const duration = color === "ping" ? 800 : 1200;
  const total = path.getTotalLength();
  const startTime = performance.now();

  function animate(now) {
    const progress = ((now - startTime) % duration) / duration;
    const point = path.getPointAtLength(progress * total);
    packet.setAttribute("cx", point.x);
    packet.setAttribute("cy", point.y);
    animFrame = requestAnimationFrame(animate);
  }
  animFrame = requestAnimationFrame(animate);
}

function scheduleRedraw() {
  if (redrawFrame !== null) cancelAnimationFrame(redrawFrame);
  redrawFrame = requestAnimationFrame(() => {
    redrawFrame = null;
    if (currentArrow) drawArrow();
  });
}

function showArrow(from, to, color) {
  currentArrow = { from, to, color };
  drawArrow();
}

function animatePing(source, target) {
  showArrow(source, target, "ping");
}

function animateScan() {
  showArrow("lab-scanner", "lab-target", "active");
}

const $ = (id) => document.getElementById(id);

async function api(path, body) {
  const opts = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : { method: "GET" };
  const res = await fetch(path, opts);
  return res.json();
}

function renderContainers(containers) {
  clearPackets();
  const el = $("topology-nodes");
  if (!containers.length) {
    currentArrow = null;
    el.innerHTML = '<p class="empty">Tiada container. Tekan <strong>Create Lab</strong>.</p>';
    return;
  }
  el.innerHTML = containers.map((c) => `
    <div class="card ${c.status === "Running" ? "running" : "stopped"}"
         data-node-name="${c.name}"
         data-node-role="${c.roles[0] || (c.name === "lab-target" ? "target" : "scanner")}">
      <div class="card-name">${c.name}</div>
      <div class="card-role">${c.roles.join(", ") || "-"}</div>
      <div class="card-row"><span>Status</span><b>${c.status}</b></div>
      <div class="card-row"><span>IPv4</span><b>${c.ipv4}</b></div>
      <div class="card-row"><span>Image</span><b>${c.image}</b></div>
      <div class="card-row"><span>Arch</span><b>${c.arch}</b></div>
    </div>
  `).join("");
  if (currentArrow) scheduleRedraw();
}

const STATUS_CLASSES = { ok: "ok", warn: "warn", off: "off" };

function renderStatus(containers) {
  const indicator = $("incus-status");
  const dot = indicator.querySelector(".status-indicator");
  const text = indicator.querySelector(".status-text");
  const running = containers.filter((c) => c.status === "Running");

  dot.className = "status-indicator";
  if (running.length === containers.length && containers.length > 0) {
    dot.classList.add(STATUS_CLASSES.ok);
    text.textContent = `${containers.length} container • semua aktif`;
  } else if (containers.length > 0) {
    dot.classList.add(STATUS_CLASSES.warn);
    text.textContent = `${running.length}/${containers.length} container aktif`;
  } else {
    dot.classList.add(STATUS_CLASSES.off);
    text.textContent = "Tiada container";
  }
}

function renderLog(lines) {
  $("log").textContent = lines.join("\n");
}

async function refresh() {
  const data = await api("/api/containers");
  renderContainers(data.containers);
  renderStatus(data.containers);
  renderLog(data.log);
}

let animFrame = null;
let redrawFrame = null;
let currentArrow = null;

function clearPackets() {
  if (animFrame !== null) {
    cancelAnimationFrame(animFrame);
    animFrame = null;
  }
  const svg = document.getElementById("topology-svg");
  if (svg) svg.querySelectorAll(".topology-arrow, .topology-packet").forEach((el) => el.remove());
}

function getNode(container, name) {
  return container.querySelector(`[data-node-name="${name}"]`);
}

function drawArrow() {
  clearPackets();
  const container = $("topology");
  const svg = document.getElementById("topology-svg");
  if (!container || !svg || !currentArrow) return;

  const fromEl = getNode(container, currentArrow.from);
  const toEl = getNode(container, currentArrow.to);
  if (!fromEl || !toEl || fromEl === toEl) return;

  const color = currentArrow.color;
  const cr = container.getBoundingClientRect();
  const fr = fromEl.getBoundingClientRect();
  const tr = toEl.getBoundingClientRect();

  const forward = fr.left + fr.width / 2 <= tr.left + tr.width / 2;
  let x1, y1, x2, y2, c1x, c1y, c2x, c2y;

  if (tr.top >= fr.bottom - 1) {
    x1 = fr.left + fr.width / 2 - cr.left;
    y1 = fr.bottom - cr.top;
    x2 = tr.left + tr.width / 2 - cr.left;
    y2 = tr.top - cr.top;
    const dy = y2 - y1;
    c1x = x1; c1y = y1 + dy * 0.5;
    c2x = x2; c2y = y2 - dy * 0.5;
  } else {
    x1 = (forward ? fr.right : fr.left) - cr.left;
    x2 = (forward ? tr.left : tr.right) - cr.left;
    y1 = fr.top + fr.height / 2 - cr.top;
    y2 = tr.top + tr.height / 2 - cr.top;
    const dx = x2 - x1;
    c1x = x1 + dx * 0.5; c1y = y1;
    c2x = x2 - dx * 0.5; c2y = y2;
  }

  svg.setAttribute("width", cr.width);
  svg.setAttribute("height", cr.height);

  const pathData = `M ${x1} ${y1} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${x2} ${y2}`;

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", pathData);
  path.setAttribute("class", `topology-arrow ${color || ""}`);
  path.setAttribute("marker-end", `url(#arrowhead${color ? "-" + color : ""})`);
  svg.appendChild(path);

  const packet = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  packet.setAttribute("class", `topology-packet${color ? " " + color : ""}`);
  packet.setAttribute("r", "4");
  svg.appendChild(packet);

  const duration = color === "ping" ? 800 : 1200;
  const total = path.getTotalLength();
  const startTime = performance.now();

  function animate(now) {
    const progress = ((now - startTime) % duration) / duration;
    const point = path.getPointAtLength(progress * total);
    packet.setAttribute("cx", point.x);
    packet.setAttribute("cy", point.y);
    animFrame = requestAnimationFrame(animate);
  }
  animFrame = requestAnimationFrame(animate);
}

function scheduleRedraw() {
  if (redrawFrame !== null) cancelAnimationFrame(redrawFrame);
  redrawFrame = requestAnimationFrame(() => {
    redrawFrame = null;
    if (currentArrow) drawArrow();
  });
}

function showArrow(from, to, color) {
  currentArrow = { from, to, color };
  drawArrow();
}

function animatePing(source, target) {
  showArrow(source, target, "ping");
}

function animateScan() {
  showArrow("lab-scanner", "lab-target", "active");
}

$("btn-scan").onclick = async () => {
  const target = $("scan-target").value;
  $("output").textContent = "Running nmap…";
  const data = await api("/api/scan", { target });
  $("output").textContent = data.output;
  renderLog(data.log);
  animateScan();
};

$("btn-ping").onclick = async () => {
  const source = $("ping-source").value;
  const target = $("ping-target").value;
  $("output").textContent = "Running ping…";
  const data = await api("/api/ping", { source, target });
  $("output").textContent = data.output;
  renderLog(data.log);
  animatePing(source, target);
};

$("btn-refresh").onclick = async () => {
  const data = await api("/api/containers");
  renderContainers(data.containers);
  renderStatus(data.containers);
  renderLog(data.log);
};

$("btn-create").onclick = async () => {
  $("output").textContent = "Creating lab… (ini ambil masa 1–3 minit)";
  const data = await api("/api/lab/create", {});
  renderLog(data.log);
  $("output").textContent = "Lab ready.";
  refresh();
};

$("btn-destroy").onclick = async () => {
  const data = await api("/api/lab/destroy", {});
  renderLog(data.log);
  refresh();
};

// NEW: Phase 1 connectivity commands
$("btn-ip-addr").onclick = async () => {
  const target = $("conn-target").value;
  $("output").textContent = `Menjalankan ip addr pada ${target}...`;
  const data = await api(`/api/ip-addr?target=${encodeURIComponent(target)}`);
  $("output").textContent = data.output;
  renderLog(data.log);
};

$("btn-ip-route").onclick = async () => {
  const target = $("conn-target").value;
  $("output").textContent = `Menjalankan ip route pada ${target}...`;
  const data = await api(`/api/ip-route?target=${encodeURIComponent(target)}`);
  $("output").textContent = data.output;
  renderLog(data.log);
};

$("btn-ip-neigh").onclick = async () => {
  const target = $("conn-target").value;
  $("output").textContent = `Menjalankan ip neigh pada ${target}...`;
  const data = await api(`/api/ip-neigh?target=${encodeURIComponent(target)}`);
  $("output").textContent = data.output;
  renderLog(data.log);
};

window.addEventListener("resize", scheduleRedraw);
if (window.ResizeObserver) {
  new ResizeObserver(scheduleRedraw).observe($("topology"));
}

refresh();

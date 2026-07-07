import psutil
import datetime
import time
import httpx
from collections import deque
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="System Monitor")

cpu_history = deque(maxlen=60)

@app.get("/")
def root():
    return {"status": "running", "service": "system-monitor"}

@app.get("/metrics")
def metrics():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    boot_time = psutil.boot_time()
    uptime_seconds = datetime.datetime.now().timestamp() - boot_time
    uptime = str(datetime.timedelta(seconds=int(uptime_seconds)))

    cpu_history.append({
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "value": cpu
    })

    return {
        "cpu": {
            "usage_percent": cpu,
            "core_count": psutil.cpu_count(logical=False),
            "thread_count": psutil.cpu_count(logical=True)
        },
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "free_gb": round(memory.available / (1024**3), 2),
            "usage_percent": memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "usage_percent": disk.percent
        },
        "network": {
            "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2)
        },
        "system": {
            "uptime": uptime,
            "process_count": len(psutil.pids()),
            "boot_time": datetime.datetime.fromtimestamp(boot_time).strftime("%Y-%m-%d %H:%M:%S")
        }
    }

@app.get("/metrics/history")
def history():
    return list(cpu_history)

@app.get("/metrics/processes")
def processes():
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            procs.append(p.info)
        except Exception:
            pass
    top5 = sorted(procs, key=lambda x: x["cpu_percent"] or 0, reverse=True)[:5]
    return top5

@app.get("/health/check")
async def health_check():
    urls = [
        {"name": "AI Summarizer API", "url": "https://ai-summarizer-api-ge8q.onrender.com/"},
        {"name": "Google", "url": "https://www.google.com"},
        {"name": "GitHub", "url": "https://github.com"},
        {"name": "HuggingFace", "url": "https://huggingface.co"}
    ]
    results = []
    async with httpx.AsyncClient(timeout=10) as client:
        for item in urls:
            try:
                start = time.time()
                res = await client.get(item["url"])
                elapsed = round((time.time() - start) * 1000)
                results.append({
                    "name": item["name"],
                    "url": item["url"],
                    "status": "up",
                    "status_code": res.status_code,
                    "response_time_ms": elapsed
                })
            except Exception:
                results.append({
                    "name": item["name"],
                    "url": item["url"],
                    "status": "down",
                    "status_code": None,
                    "response_time_ms": None
                })
    return results

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Monitor Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }
        header { margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; }
        header h1 { font-size: 1.8rem; color: #38bdf8; display: flex; align-items: center; gap: 10px; }
        header p { color: #64748b; font-size: 0.85rem; margin-top: 4px; }
        .grid-top { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem; }
        .grid-bottom { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }
        .grid-health { margin-bottom: 1.5rem; }
        @media (max-width: 768px) { .grid-bottom { grid-template-columns: 1fr; } }
        .card { background: #1e293b; border-radius: 16px; padding: 1.5rem; border: 1px solid #334155; position: relative; overflow: hidden; }
        .card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }
        .card.cpu::before { background: linear-gradient(90deg, #38bdf8, #0ea5e9); }
        .card.memory::before { background: linear-gradient(90deg, #a78bfa, #7c3aed); }
        .card.disk::before { background: linear-gradient(90deg, #34d399, #059669); }
        .card.network::before { background: linear-gradient(90deg, #fb923c, #ea580c); }
        .card.chart-card::before { background: linear-gradient(90deg, #38bdf8, #a78bfa); }
        .card.process-card::before { background: linear-gradient(90deg, #f472b6, #db2777); }
        .card.health-card::before { background: linear-gradient(90deg, #34d399, #38bdf8); }
        .card h2 { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem; }
        .big-number { font-size: 2.5rem; font-weight: 700; margin-bottom: 0.25rem; }
        .big-number.cpu { color: #38bdf8; }
        .big-number.memory { color: #a78bfa; }
        .big-number.disk { color: #34d399; }
        .big-number.network { color: #fb923c; }
        .bar-container { background: #0f172a; border-radius: 999px; height: 6px; margin: 0.75rem 0; overflow: hidden; }
        .bar { height: 100%; border-radius: 999px; transition: width 0.8s ease, background 0.5s ease; }
        .metric-row { display: flex; justify-content: space-between; font-size: 0.82rem; padding: 4px 0; border-bottom: 1px solid #263345; }
        .metric-row:last-child { border-bottom: none; }
        .metric-row .label { color: #64748b; }
        .metric-row .value { color: #cbd5e1; font-weight: 500; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; background: #34d399; display: inline-block; animation: pulse 2s infinite; }
        @keyframes pulse { 0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(52,211,153,0.4)} 50%{opacity:.8;box-shadow:0 0 0 6px rgba(52,211,153,0)} }
        .tag { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.7rem; font-weight: 600; margin-left: 8px; }
        .tag.good { background: #052e16; color: #34d399; }
        .tag.warn { background: #422006; color: #fb923c; }
        .tag.danger { background: #450a0a; color: #f87171; }
        table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        th { color: #64748b; font-weight: 500; text-align: left; padding: 6px 8px; border-bottom: 1px solid #334155; font-size: 0.75rem; text-transform: uppercase; }
        td { padding: 8px; border-bottom: 1px solid #1e293b; color: #cbd5e1; }
        tr:last-child td { border-bottom: none; }
        .health-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
        .health-dot.up { background: #34d399; }
        .health-dot.down { background: #f87171; }
        .response-time { font-size: 0.75rem; }
        .response-time.fast { color: #34d399; }
        .response-time.medium { color: #fb923c; }
        .response-time.slow { color: #f87171; }
        .footer { text-align: center; color: #334155; font-size: 0.8rem; margin-top: 1rem; }
        .footer span { color: #38bdf8; }
    </style>
</head>
<body>
<header>
    <div>
        <h1><span class="status-dot"></span> System Monitor <span id="status-tag" class="tag good">Healthy</span></h1>
        <p>Live system metrics + API health monitoring — updates every 3 seconds</p>
    </div>
</header>

<div class="grid-top">
    <div class="card cpu">
        <h2>CPU Usage</h2>
        <div class="big-number cpu" id="cpu-percent">--</div>
        <div class="bar-container"><div class="bar" id="cpu-bar" style="width:0%"></div></div>
        <div class="metric-row"><span class="label">Physical Cores</span><span class="value" id="cpu-cores">--</span></div>
        <div class="metric-row"><span class="label">Logical Threads</span><span class="value" id="cpu-threads">--</span></div>
    </div>

    <div class="card memory">
        <h2>Memory (RAM)</h2>
        <div class="big-number memory" id="mem-percent">--</div>
        <div class="bar-container"><div class="bar" id="mem-bar" style="width:0%"></div></div>
        <div class="metric-row"><span class="label">Used</span><span class="value" id="mem-used">--</span></div>
        <div class="metric-row"><span class="label">Free</span><span class="value" id="mem-free">--</span></div>
        <div class="metric-row"><span class="label">Total</span><span class="value" id="mem-total">--</span></div>
    </div>

    <div class="card disk">
        <h2>Disk Storage</h2>
        <div class="big-number disk" id="disk-percent">--</div>
        <div class="bar-container"><div class="bar" id="disk-bar" style="width:0%"></div></div>
        <div class="metric-row"><span class="label">Used</span><span class="value" id="disk-used">--</span></div>
        <div class="metric-row"><span class="label">Free</span><span class="value" id="disk-free">--</span></div>
        <div class="metric-row"><span class="label">Total</span><span class="value" id="disk-total">--</span></div>
    </div>

    <div class="card network">
        <h2>Network I/O</h2>
        <div class="big-number network" id="net-recv">--</div>
        <p style="color:#64748b;font-size:0.75rem;margin-bottom:0.75rem">MB received total</p>
        <div class="metric-row"><span class="label">Sent</span><span class="value" id="net-sent">--</span></div>
        <div class="metric-row"><span class="label">Processes</span><span class="value" id="process-count">--</span></div>
        <div class="metric-row"><span class="label">Uptime</span><span class="value" id="uptime">--</span></div>
    </div>
</div>

<div class="grid-bottom">
    <div class="card chart-card">
        <h2>CPU History (last 60s)</h2>
        <canvas id="cpuChart" height="120"></canvas>
    </div>

    <div class="card process-card">
        <h2>Top Processes by CPU</h2>
        <table>
            <thead><tr><th>Process</th><th>PID</th><th>CPU %</th><th>MEM %</th></tr></thead>
            <tbody id="process-table"></tbody>
        </table>
    </div>
</div>

<div class="grid-health">
    <div class="card health-card">
        <h2>API Health Monitor</h2>
        <table>
            <thead><tr><th>Service</th><th>Status</th><th>Response Time</th><th>HTTP Code</th></tr></thead>
            <tbody id="health-table"></tbody>
        </table>
    </div>
</div>

<div class="footer">Last updated: <span id="last-updated">--</span></div>

<script>
const ctx = document.getElementById('cpuChart').getContext('2d');
const cpuChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'CPU %',
            data: [],
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56,189,248,0.1)',
            borderWidth: 2,
            pointRadius: 0,
            fill: true,
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        animation: false,
        scales: {
            y: { min: 0, max: 100, ticks: { color: '#64748b', callback: v => v+'%' }, grid: { color: '#1e293b' } },
            x: { ticks: { color: '#64748b', maxTicksLimit: 6 }, grid: { color: '#1e293b' } }
        },
        plugins: { legend: { display: false } }
    }
});

function getBarColor(p) {
    if (p < 60) return '#34d399';
    if (p < 80) return '#fb923c';
    return '#f87171';
}

function getResponseClass(ms) {
    if (ms < 300) return 'fast';
    if (ms < 800) return 'medium';
    return 'slow';
}

function getStatusTag(cpu, mem, disk) {
    const max = Math.max(cpu, mem, disk);
    if (max < 60) return ['Healthy', 'good'];
    if (max < 80) return ['Warning', 'warn'];
    return ['Critical', 'danger'];
}

async function fetchMetrics() {
    try {
        const res = await fetch('/metrics');
        const d = await res.json();

        document.getElementById('cpu-percent').textContent = d.cpu.usage_percent + '%';
        document.getElementById('cpu-cores').textContent = d.cpu.core_count;
        document.getElementById('cpu-threads').textContent = d.cpu.thread_count;
        const cpuBar = document.getElementById('cpu-bar');
        cpuBar.style.width = d.cpu.usage_percent + '%';
        cpuBar.style.background = getBarColor(d.cpu.usage_percent);

        document.getElementById('mem-percent').textContent = d.memory.usage_percent + '%';
        document.getElementById('mem-used').textContent = d.memory.used_gb + ' GB';
        document.getElementById('mem-free').textContent = d.memory.free_gb + ' GB';
        document.getElementById('mem-total').textContent = d.memory.total_gb + ' GB';
        const memBar = document.getElementById('mem-bar');
        memBar.style.width = d.memory.usage_percent + '%';
        memBar.style.background = getBarColor(d.memory.usage_percent);

        document.getElementById('disk-percent').textContent = d.disk.usage_percent + '%';
        document.getElementById('disk-used').textContent = d.disk.used_gb + ' GB';
        document.getElementById('disk-free').textContent = d.disk.free_gb + ' GB';
        document.getElementById('disk-total').textContent = d.disk.total_gb + ' GB';
        const diskBar = document.getElementById('disk-bar');
        diskBar.style.width = d.disk.usage_percent + '%';
        diskBar.style.background = getBarColor(d.disk.usage_percent);

        document.getElementById('net-recv').textContent = d.network.bytes_recv_mb;
        document.getElementById('net-sent').textContent = d.network.bytes_sent_mb + ' MB';
        document.getElementById('process-count').textContent = d.system.process_count;
        document.getElementById('uptime').textContent = d.system.uptime;

        const [label, cls] = getStatusTag(d.cpu.usage_percent, d.memory.usage_percent, d.disk.usage_percent);
        const tag = document.getElementById('status-tag');
        tag.textContent = label;
        tag.className = 'tag ' + cls;

        document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
    } catch(e) {}
}

async function fetchHistory() {
    try {
        const res = await fetch('/metrics/history');
        const data = await res.json();
        cpuChart.data.labels = data.map(d => d.time);
        cpuChart.data.datasets[0].data = data.map(d => d.value);
        cpuChart.update();
    } catch(e) {}
}

async function fetchProcesses() {
    try {
        const res = await fetch('/metrics/processes');
        const data = await res.json();
        const tbody = document.getElementById('process-table');
        tbody.innerHTML = data.map(p => `
            <tr>
                <td>${p.name || 'unknown'}</td>
                <td style="color:#64748b">${p.pid}</td>
                <td style="color:${getBarColor(p.cpu_percent || 0)}">${(p.cpu_percent || 0).toFixed(1)}%</td>
                <td style="color:#a78bfa">${(p.memory_percent || 0).toFixed(1)}%</td>
            </tr>
        `).join('');
    } catch(e) {}
}

async function fetchHealth() {
    try {
        const res = await fetch('/health/check');
        const data = await res.json();
        const tbody = document.getElementById('health-table');
        tbody.innerHTML = data.map(item => `
            <tr>
                <td><span class="health-dot ${item.status}"></span>${item.name}</td>
                <td><span class="tag ${item.status === 'up' ? 'good' : 'danger'}">${item.status.toUpperCase()}</span></td>
                <td class="response-time ${item.response_time_ms ? getResponseClass(item.response_time_ms) : ''}">${item.response_time_ms ? item.response_time_ms + ' ms' : 'timeout'}</td>
                <td style="color:#64748b">${item.status_code || '--'}</td>
            </tr>
        `).join('');
    } catch(e) {}
}

fetchMetrics();
fetchHistory();
fetchProcesses();
fetchHealth();

setInterval(fetchMetrics, 3000);
setInterval(fetchHistory, 3000);
setInterval(fetchProcesses, 5000);
setInterval(fetchHealth, 15000);
</script>
</body>
</html>
"""

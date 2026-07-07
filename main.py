import psutil
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="System Monitor")

@app.get("/")
def root():
    return {"status": "running", "service": "system-monitor"}

@app.get("/metrics")
def metrics():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu": {
            "usage_percent": cpu
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
        }
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }
        h1 { font-size: 1.8rem; margin-bottom: 0.5rem; color: #38bdf8; }
        p.subtitle { color: #94a3b8; margin-bottom: 2rem; font-size: 0.9rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
        .card { background: #1e293b; border-radius: 12px; padding: 1.5rem; border: 1px solid #334155; }
        .card h2 { font-size: 1rem; color: #94a3b8; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.05em; }
        .metric { display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.9rem; }
        .metric span:last-child { color: #38bdf8; font-weight: 600; }
        .bar-container { background: #334155; border-radius: 999px; height: 8px; margin-top: 1rem; overflow: hidden; }
        .bar { height: 100%; border-radius: 999px; transition: width 0.5s ease; }
        .bar.cpu { background: #38bdf8; }
        .bar.memory { background: #a78bfa; }
        .bar.disk { background: #34d399; }
        .percent { font-size: 2rem; font-weight: 700; margin: 0.5rem 0; }
        .percent.cpu { color: #38bdf8; }
        .percent.memory { color: #a78bfa; }
        .percent.disk { color: #34d399; }
        .status { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #34d399; margin-right: 6px; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        .last-updated { color: #475569; font-size: 0.8rem; margin-top: 2rem; text-align: center; }
    </style>
</head>
<body>
    <h1><span class="status"></span>System Monitor</h1>
    <p class="subtitle">Live system metrics — updates every 3 seconds</p>

    <div class="grid">
        <div class="card">
            <h2>CPU Usage</h2>
            <div class="percent cpu" id="cpu-percent">--</div>
            <div class="metric"><span>Usage</span><span id="cpu-val">--</span></div>
            <div class="bar-container"><div class="bar cpu" id="cpu-bar" style="width:0%"></div></div>
        </div>

        <div class="card">
            <h2>Memory</h2>
            <div class="percent memory" id="mem-percent">--</div>
            <div class="metric"><span>Used</span><span id="mem-used">--</span></div>
            <div class="metric"><span>Free</span><span id="mem-free">--</span></div>
            <div class="metric"><span>Total</span><span id="mem-total">--</span></div>
            <div class="bar-container"><div class="bar memory" id="mem-bar" style="width:0%"></div></div>
        </div>

        <div class="card">
            <h2>Disk</h2>
            <div class="percent disk" id="disk-percent">--</div>
            <div class="metric"><span>Used</span><span id="disk-used">--</span></div>
            <div class="metric"><span>Free</span><span id="disk-free">--</span></div>
            <div class="metric"><span>Total</span><span id="disk-total">--</span></div>
            <div class="bar-container"><div class="bar disk" id="disk-bar" style="width:0%"></div></div>
        </div>
    </div>

    <p class="last-updated" id="last-updated">Fetching data...</p>

    <script>
        async function fetchMetrics() {
            try {
                const res = await fetch('/metrics');
                const data = await res.json();

                document.getElementById('cpu-percent').textContent = data.cpu.usage_percent + '%';
                document.getElementById('cpu-val').textContent = data.cpu.usage_percent + '%';
                document.getElementById('cpu-bar').style.width = data.cpu.usage_percent + '%';

                document.getElementById('mem-percent').textContent = data.memory.usage_percent + '%';
                document.getElementById('mem-used').textContent = data.memory.used_gb + ' GB';
                document.getElementById('mem-free').textContent = data.memory.free_gb + ' GB';
                document.getElementById('mem-total').textContent = data.memory.total_gb + ' GB';
                document.getElementById('mem-bar').style.width = data.memory.usage_percent + '%';

                document.getElementById('disk-percent').textContent = data.disk.usage_percent + '%';
                document.getElementById('disk-used').textContent = data.disk.used_gb + ' GB';
                document.getElementById('disk-free').textContent = data.disk.free_gb + ' GB';
                document.getElementById('disk-total').textContent = data.disk.total_gb + ' GB';
                document.getElementById('disk-bar').style.width = data.disk.usage_percent + '%';

                document.getElementById('last-updated').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
            } catch(e) {
                document.getElementById('last-updated').textContent = 'Error fetching metrics';
            }
        }

        fetchMetrics();
        setInterval(fetchMetrics, 3000);
    </script>
</body>
</html>
"""

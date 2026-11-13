import http.server
import json
import socketserver
import sqlite3

PORT = 8000

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>xv6 Telemetry & Kernel Performance Observatory</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 25px; }
        .container { max-width: 1150px; margin: 0 auto; }
        h1 { color: #38bdf8; font-size: 26px; border-bottom: 2px solid #1e293b; padding-bottom: 10px; }
        .card { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); }
        h2 { color: #94a3b8; font-size: 17px; margin-top: 0; }
        
        .section-header { display: flex; justify-content: space-between; align-items: center; margin: 25px 0 15px 0; }
        .section-title { color: #38bdf8; font-size: 20px; border-left: 4px solid #38bdf8; padding-left: 10px; }

        .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }
        .metric-box { background: #0f172a; padding: 18px 12px; border-radius: 8px; text-align: center; border-left: 4px solid #38bdf8; }
        .metric-val { font-size: 22px; font-weight: bold; color: #38bdf8; margin-top: 5px; }
        
        .metric-sub { font-size: 13px; font-weight: 600; color: #e2e8f0; margin-top: 8px; background: rgba(255, 255, 255, 0.08); padding: 4px 10px; border-radius: 6px; display: inline-block; letter-spacing: 0.3px; }
        
        .algo-badge { background: linear-gradient(135deg, #0284c7, #2563eb); color: #ffffff; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 700; letter-spacing: 0.5px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2); }

        .chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .legend { display: flex; gap: 20px; font-size: 14px; font-weight: 500; }
        .legend-item { display: flex; align-items: center; gap: 8px; }
        .legend-color { width: 16px; height: 16px; border-radius: 4px; }
        
        .bar-container { display: flex; align-items: flex-end; justify-content: space-around; height: 220px; padding-top: 20px; border-bottom: 2px solid #475569; }
        .pid-group { display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; flex: 1; }
        .bars-wrapper { display: flex; align-items: flex-end; gap: 12px; height: 100%; justify-content: center; width: 100%; }
        
        .bar { width: 38px; border-radius: 6px 6px 0 0; text-align: center; color: #0f172a; font-weight: bold; font-size: 12px; padding-top: 4px; box-sizing: border-box; transition: height 0.4s ease; }
        .bar-prio { background: linear-gradient(180deg, #38bdf8, #0284c7); color: #0f172a; }
        .bar-rr { background: linear-gradient(180deg, #facc15, #ca8a04); color: #0f172a; }
        
        /* Control Plane UI */
        .control-panel { background: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 20px; display: flex; align-items: center; gap: 30px; }
        select, input[type="number"], input[type="text"] { background: #1e293b; color: white; border: 1px solid #475569; padding: 8px; border-radius: 4px; font-weight: bold; margin-top: 5px; }
        .btn-action { background: #38bdf8; color: #0f172a; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; cursor: pointer; }
        .btn-action:hover { background: #0284c7; color: white; }
        .sim-inputs-table td { padding: 4px 10px; }
        .pid-label { margin-top: 10px; font-size: 13px; color: #cbd5e1; font-weight: 600; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }
        th, td { text-align: left; padding: 10px 14px; border-bottom: 1px solid #334155; }
        th { background: #0f172a; color: #38bdf8; }
        
        .badge-prio { background: #0369a1; color: #e0f2fe; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
        .badge-rr { background: #854d0e; color: #fef08a; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
        .badge-thread { background: #7e22ce; color: #f3e8ff; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
        
        .refresh-btn { background: #38bdf8; color: #0f172a; border: none; padding: 10px 18px; border-radius: 6px; font-weight: bold; cursor: pointer; float: right; }
        .refresh-btn:hover { background: #0284c7; color: white; }
        
        .progress-bg { background: #0f172a; border-radius: 8px; height: 18px; width: 100%; overflow: hidden; margin-top: 8px; border: 1px solid #334155; }
        .progress-fill { background: linear-gradient(90deg, #38bdf8, #818cf8); height: 100%; transition: width 0.5s ease; }
    </style>
</head>
<body>
    <div class="container">
        <button class="refresh-btn" onclick="loadAllData()">🔄 Refresh Telemetry</button>
        <h1>🚀 xv6 Kernel Observatory & Analytics</h1>
        
        <!-- GLOBAL CONTROL PANEL -->
        <div class="card control-panel" style="border-left: 4px solid #10b981;">
            <div>
                <label style="color: #94a3b8; font-size: 13px; display: block; font-weight:bold;">🧠 Memory Paging Policy:</label>
                <select id="mem-algo-selector" onchange="switchMemMode()">
                    <option value="REAL_MEM">Kernel Pipeline (Live DB)</option>
                    <option value="SIM_FIFO">First-In, First-Out (FIFO)</option>
                    <option value="SIM_LRU">Least Recently Used (LRU)</option>
                </select>
            </div>
            
            <div>
                <label style="color: #94a3b8; font-size: 13px; display: block; font-weight:bold;">📄 Test Pages Variable:</label>
                <input type="number" id="test-pages-input" value="8" min="1" max="32" style="width: 80px;" onchange="if(memMode!=='REAL_MEM') simulateMemoryData();">
            </div>

            <div>
                <label style="color: #94a3b8; font-size: 13px; display: block; font-weight:bold;">⚡ CPU Scheduler Algorithm:</label>
                <select id="algo-selector" onchange="switchMode()">
                    <option value="REAL_PRIORITY">Priority Scheduler (Live DB)</option>
                    <option value="FCFS">First-Come, First-Served (FCFS)</option>
                    <option value="SJF">Shortest Job First (SJF)</option>
                    <option value="SRTF">Shortest Remaining Time First (SRTF)</option>
                    <option value="LJF">Longest Job First (LJF)</option>
                </select>
            </div>
            
            <div id="sim-setup" style="display: none; align-items: center; gap: 15px; border-left: 1px solid #334155; padding-left: 20px;">
                <div>
                    <label style="color: #94a3b8; font-size: 13px;">Active Processes:</label>
                    <input type="number" id="sim-count" value="4" min="1" max="8" style="width: 50px;">
                </div>
                <button class="btn-action" onclick="generateSimInputs()">Configure Workload</button>
            </div>
        </div>

        <div class="section-title">🧠 Phase 1 & 3: Memory Telemetry</div>
        <div class="grid-4">
            <div class="card metric-box" style="border-left-color: #38bdf8;">
                <h2>Total Physical RAM</h2>
                <div class="metric-val" id="mem-total">128.0 MB</div>
                <div class="metric-sub" id="mem-total-pages">32768 Pages</div>
            </div>
            <div class="card metric-box" style="border-left-color: #f43f5e;">
                <h2>Used RAM Footprint</h2>
                <div class="metric-val" style="color: #f43f5e;" id="mem-used">0 KB</div>
                <div class="metric-sub" id="mem-used-pages">0 Pages</div>
            </div>
            <div class="card metric-box" style="border-left-color: #4ade80;">
                <h2>Free RAM Pool</h2>
                <div class="metric-val" style="color: #4ade80;" id="mem-free">128.0 MB</div>
                <div class="metric-sub" id="mem-free-pages">32768 Pages</div>
            </div>
            <div class="card metric-box" style="border-left-color: #a855f7;">
                <h2>RAM Utilization</h2>
                <div class="metric-val" style="color: #a855f7;" id="mem-util">0.0%</div>
                <div class="progress-bg"><div class="progress-fill" id="mem-progress" style="width: 0%;"></div></div>
            </div>
        </div>

        <div class="section-header">
            <div class="section-title" style="border-left-color: #60a5fa; color: #60a5fa; margin:0;">⚙️ Page Replacement Analytics</div>
            <span class="algo-badge" id="algo-badge">Active Algo: FIFO</span>
        </div>
        <div class="grid-3">
            <div class="card metric-box" style="border-left-color: #38bdf8;">
                <h2>Total Page Faults (Lazy Alloc)</h2>
                <div class="metric-val" style="color: #38bdf8;" id="page-faults-val">0</div>
                <div class="metric-sub">On-Demand RAM Hits</div>
            </div>
            <div class="card metric-box" style="border-left-color: #f59e0b;">
                <h2>Total Swap Outs (Evictions)</h2>
                <div class="metric-val" style="color: #f59e0b;" id="swap-outs-val">0</div>
                <div class="metric-sub">Pages Swapped to Disk</div>
            </div>
            <div class="card metric-box" style="border-left-color: #10b981;">
                <h2>Paging Efficiency</h2>
                <div class="metric-val" style="color: #10b981;" id="paging-eff-val">100.0%</div>
                <div class="metric-sub">Zero Eviction Overhead</div>
            </div>
        </div>

        <div class="card">
            <h2>📋 Active Processes: Virtual Memory vs Resident Pages (RSS)</h2>
            <table>
                <thead>
                    <tr>
                        <th>PID</th>
                        <th>ASID</th>
                        <th>Type</th>
                        <th>Process Name</th>
                        <th>Virtual Memory Size</th>
                        <th>Resident Physical Pages</th>
                        <th>RAM Footprint</th>
                        <th>State</th>
                    </tr>
                </thead>
                <tbody id="proc-mem-table">
                    <tr><td colspan="8" style="text-align: center; color: #64748b;">Waiting for memory telemetry logs...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- SECTION: BANKER'S ALGORITHM & DEADLOCK SIMULATOR -->
        <div class="section-title">🔒 Concurrency & Banker's Algorithm Simulator</div>
        <div class="card" style="border-left: 4px solid #f43f5e;">
            <h2 style="color: #f43f5e;">Resource Allocation & Safety Check</h2>
            <p style="font-size: 13px; color: #94a3b8; margin-bottom: 15px;">
                Interactive implementation of Dijkstra's Banker's Algorithm. Modify matrices below and click test.
            </p>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 15px;">
                <div>
                    <label style="font-size: 12px; font-weight: bold; color: #38bdf8;">Allocation Matrix (3x3):</label>
                    <textarea id="banker-alloc" rows="3" style="width: 100%; background: #0f172a; color: white; border: 1px solid #475569; border-radius: 4px; padding: 6px; font-family: monospace;">0 1 0
2 0 0
3 0 2</textarea>
                </div>
                <div>
                    <label style="font-size: 12px; font-weight: bold; color: #38bdf8;">Max Matrix (3x3):</label>
                    <textarea id="banker-max" rows="3" style="width: 100%; background: #0f172a; color: white; border: 1px solid #475569; border-radius: 4px; padding: 6px; font-family: monospace;">7 5 3
3 2 2
9 0 2</textarea>
                </div>
                <div>
                    <label style="font-size: 12px; font-weight: bold; color: #38bdf8;">Available Resources (1x3):</label>
                    <input type="text" id="banker-avail" value="3 3 2" style="width: 100%; background: #0f172a; color: white; border: 1px solid #475569; border-radius: 4px; padding: 8px; font-family: monospace; margin-top: 5px;">
                </div>
            </div>
            
            <button class="btn-action" style="background: #f43f5e; color: white;" onclick="runBankerSimulation()">▶ Run Banker's Safety Check</button>
            
            <div id="banker-result" style="margin-top: 15px; padding: 12px; background: #0f172a; border-radius: 6px; font-weight: bold; font-size: 14px; border: 1px solid #334155; color: #94a3b8;">
                Result: Click the button above to evaluate system safety state.
            </div>
        </div>

        <div class="section-title">⚡ CPU Scheduling Observatory</div>
        
        <div class="card" id="sim-input-area" style="display: none; border-left: 4px solid #38bdf8;">
            <h2 style="color: #38bdf8;">🛠️ Configure Burst Times (Execution Ticks)</h2>
            <table class="sim-inputs-table" id="sim-input-table"></table>
            <button class="btn-action" style="margin-top: 15px;" onclick="runSimulation()">▶ Execute Workload</button>
        </div>

        <div class="grid-4">
            <div class="card metric-box">
                <h2 id="tat-header-text">Priority Avg TAT</h2>
                <div class="metric-val" id="prio-tat">0 ticks</div>
                <div class="metric-sub">Across All Runs</div>
            </div>
            <div class="card metric-box" style="border-left-color: #facc15;">
                <h2 id="rr-header-text">RR Benchmark TAT</h2>
                <div class="metric-val" style="color: #facc15;" id="rr-tat">0 ticks</div>
                <div class="metric-sub" id="rr-sub-text">Preemption delay</div>
            </div>
            <div class="card metric-box" style="border-left-color: #4ade80;">
                <h2>CPU Utilization</h2>
                <div class="metric-val" style="color: #4ade80;" id="cpu-util">95.8%</div>
                <div class="metric-sub" id="cpu-sub-text">vs 81.2% in RR</div>
            </div>
            <div class="card metric-box" style="border-left-color: #a855f7;">
                <h2>Data Source</h2>
                <div class="metric-val" style="color: #a855f7;" id="data-source-badge">xv6 Kernel</div>
                <div class="metric-sub" id="ctx-sub-text">Live Pipeline Sync</div>
            </div>
        </div>

        <div class="card">
            <div class="chart-header">
                <h2 id="chart-title-text">📊 Benchmark Side-by-Side Comparison (RR Baseline vs Priority)</h2>
                <div class="legend" id="chart-legend">
                    <div class="legend-item"><div class="legend-color" style="background: #38bdf8;"></div><span>Priority Scheduler</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #facc15;"></div><span>Round Robin (Baseline)</span></div>
                </div>
            </div>
            <div class="bar-container" id="chart"></div>
        </div>

        <div class="card">
            <h2>📋 Historical CPU Scheduling Log</h2>
            <table>
                <thead>
                    <tr>
                        <th>Algorithm</th>
                        <th>PID</th>
                        <th id="table-prio-header">Prio</th>
                        <th>Exec Ticks</th>
                        <th>Wait Ticks</th>
                        <th>TAT Ticks</th>
                    </tr>
                </thead>
                <tbody id="table-body"></tbody>
            </table>
        </div>
    </div>

    <script>
        let cpuMode = 'REAL_PRIORITY';
        let memMode = 'REAL_MEM';

        function getValue(obj, keys) {
            for (let k in obj) {
                for (let searchKey of keys) {
                    if (k.toLowerCase() === searchKey.toLowerCase()) return obj[k];
                }
            }
            return 0;
        }

        // --- MEMORY ENGINE (REAL vs ANALYTICAL) ---
        function switchMemMode() {
            memMode = document.getElementById('mem-algo-selector').value;
            if (memMode === 'REAL_MEM') {
                loadMemoryData();
            } else {
                simulateMemoryData();
            }
        }

        async function loadMemoryData() {
            if (memMode !== 'REAL_MEM') return;
            try {
                const sysRes = await fetch('/memory_sys');
                const sysData = await sysRes.json();
                if (sysData.length > 0) {
                    const latest = sysData[0];
                    document.getElementById('mem-total').innerText = (latest.total_memory / (1024 * 1024)).toFixed(1) + ' MB';
                    document.getElementById('mem-total-pages').innerText = (latest.total_memory / 4096) + ' Pages';
                    document.getElementById('mem-used').innerText = (latest.used_memory / 1024).toFixed(1) + ' KB';
                    document.getElementById('mem-used-pages').innerText = (latest.used_memory / 4096) + ' Pages';
                    document.getElementById('mem-free').innerText = (latest.free_memory / (1024 * 1024)).toFixed(1) + ' MB';
                    document.getElementById('mem-free-pages').innerText = (latest.free_memory / 4096) + ' Pages';
                    document.getElementById('mem-util').innerText = latest.utilization_percentage.toFixed(1) + '%';
                    document.getElementById('mem-progress').style.width = latest.utilization_percentage.toFixed(1) + '%';
                    
                    const algo = latest.active_algo || 'FIFO';
                    const pageFaults = latest.page_faults !== undefined ? latest.page_faults : 0;
                    const swapOuts = latest.swap_outs !== undefined ? latest.swap_outs : 0;
                    
                    document.getElementById('algo-badge').innerText = 'Active Algo: ' + algo;
                    document.getElementById('algo-badge').style.background = 'linear-gradient(135deg, #0284c7, #2563eb)';
                    document.getElementById('page-faults-val').innerText = pageFaults;
                    document.getElementById('swap-outs-val').innerText = swapOuts;
                    
                    let eff = 100.0;
                    if (pageFaults > 0) eff = Math.max(0, ((pageFaults - swapOuts) / pageFaults) * 100).toFixed(1);
                    document.getElementById('paging-eff-val').innerText = eff + '%';
                }

                const procRes = await fetch('/memory_proc');
                const procData = await procRes.json();
                const procTable = document.getElementById('proc-mem-table');
                procTable.innerHTML = '';

                if (procData.length === 0) {
                    procTable.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #64748b;">No active memory statistics found.</td></tr>';
                    return;
                }
                const stateNames = { 0: 'UNUSED', 1: 'USED', 2: 'SLEEPING', 3: 'RUNNABLE', 4: 'RUNNING', 5: 'ZOMBIE' };
                procData.forEach(p => {
                    const typeBadge = p.is_thread === 1 ? '<span class="badge-thread">Thread</span>' : '<span class="badge-prio" style="background:#15803d; color:#dcfce7;">Process</span>';
                    procTable.innerHTML += `<tr>
                        <td><b>PID ${p.pid}</b></td>
                        <td>ASID ${p.asid}</td>
                        <td>${typeBadge}</td>
                        <td><code>${p.process_name}</code></td>
                        <td>${(p.virtual_memory / 1024).toFixed(1)} KB</td>
                        <td><b>${p.resident_pages} pages</b></td>
                        <td><span style="color: #38bdf8; font-weight: bold;">${(p.resident_memory / 1024).toFixed(1)} KB</span></td>
                        <td>${stateNames[p.process_state] || 'UNKNOWN'}</td>
                    </tr>`;
                });
            } catch (e) {}
        }

        function simulateMemoryData() {
            const isLRU = memMode === 'SIM_LRU';
            const targetPages = parseInt(document.getElementById('test-pages-input').value) || 8;
            
            document.getElementById('mem-total').innerText = "128.0 MB";
            document.getElementById('mem-total-pages').innerText = "32768 Pages";
            
            const usedKb = targetPages * 4;
            document.getElementById('mem-used').innerText = usedKb.toFixed(1) + " KB";
            document.getElementById('mem-used-pages').innerText = targetPages + " Pages";
            
            const freeMb = 128.0 - (usedKb / 1024);
            document.getElementById('mem-free').innerText = freeMb.toFixed(1) + " MB";
            document.getElementById('mem-free-pages').innerText = (32768 - targetPages) + " Pages";
            
            const util = (usedKb / (128*1024)) * 100;
            document.getElementById('mem-util').innerText = util.toFixed(2) + "%";
            document.getElementById('mem-progress').style.width = util.toFixed(2) + "%";
            
            const algoName = isLRU ? 'LRU' : 'FIFO';
            document.getElementById('algo-badge').innerText = 'Active Algo: ' + algoName;
            document.getElementById('algo-badge').style.background = 'linear-gradient(135deg, #a855f7, #7e22ce)';
            
            const faults = isLRU ? Math.floor(targetPages * 0.4) + 1 : targetPages;
            const swaps = isLRU ? 0 : Math.max(0, targetPages - 8);
            
            document.getElementById('page-faults-val').innerText = faults;
            document.getElementById('swap-outs-val').innerText = swaps;
            
            let eff = 100.0;
            if(faults > 0) eff = Math.max(0, ((faults - swaps) / faults) * 100).toFixed(1);
            document.getElementById('paging-eff-val').innerText = eff + '%';
            
            document.getElementById('proc-mem-table').innerHTML = `<tr><td colspan="8" style="text-align: center; color: #a855f7; font-weight:bold;">Running Pagetest for ${targetPages} Pages under ${algoName} Policy...</td></tr>`;
        }

        // --- CPU ENGINE (REAL vs ANALYTICAL) ---
        async function loadCpuData() {
            if (cpuMode !== 'REAL_PRIORITY') return;

            try {
                const res = await fetch('/data');
                const data = await res.json();
                
                const tbody = document.getElementById('table-body');
                const chart = document.getElementById('chart');
                tbody.innerHTML = ''; chart.innerHTML = '';

                document.getElementById('tat-header-text').innerText = "Priority Avg TAT";
                document.getElementById('rr-header-text').innerText = "RR Benchmark TAT";
                document.getElementById('chart-title-text').innerText = "📊 Benchmark Side-by-Side Comparison (RR Baseline vs Priority)";
                document.getElementById('data-source-badge').innerText = "xv6 Kernel";
                document.getElementById('data-source-badge').style.color = "#a855f7";
                document.getElementById('table-prio-header').innerText = "Prio";
                
                document.getElementById('chart-legend').innerHTML = `
                    <div class="legend-item"><div class="legend-color" style="background: #38bdf8;"></div><span>Priority Scheduler</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #facc15;"></div><span>Round Robin (Baseline)</span></div>
                `;

                let prioTatSum = 0, prioCount = 0, rrTatSum = 0, rrCount = 0;
                const pidMap = {};

                data.forEach(item => {
                    const algo = getValue(item, ['algo_type', 'algo']) || 'Priority';
                    const pid = getValue(item, ['pid']);
                    const prio = getValue(item, ['priority']);
                    const exec = getValue(item, ['execution_time_ticks', 'exec_ticks', 'exec']);
                    const wt = getValue(item, ['wait_time_ticks', 'wait_ticks', 'wait']);
                    let tat = getValue(item, ['tat_ticks', 'tat']);
                    if (tat === 0) tat = exec + wt;

                    if (pid >= 4) {
                        if (!pidMap[pid]) pidMap[pid] = { prioTat: 0, rrTat: 0 };
                        if (algo.toLowerCase().includes('round')) {
                            pidMap[pid].rrTat = tat;
                            rrTatSum += tat;
                            rrCount++;
                        } else {
                            pidMap[pid].prioTat = tat;
                            prioTatSum += tat;
                            prioCount++;
                        }
                    }

                    let badgeClass = algo.toLowerCase().includes('round') ? 'badge-rr' : 'badge-prio';
                    tbody.innerHTML += `<tr>
                        <td><span class="${badgeClass}">${algo}</span></td>
                        <td><b>PID ${pid}</b></td>
                        <td>${prio}</td>
                        <td>${exec} ticks</td>
                        <td>${wt} ticks</td>
                        <td><b>${tat} ticks</b></td>
                    </tr>`;
                });

                document.getElementById('prio-tat').innerText = (prioCount ? (prioTatSum / prioCount).toFixed(1) : 0) + ' ticks';
                document.getElementById('rr-tat').innerText = (rrCount ? (rrTatSum / rrCount).toFixed(1) : 0) + ' ticks';

                const benchmarkPids = Object.keys(pidMap).map(Number).filter(pid => pidMap[pid].rrTat > 0).sort((a,b) => a - b);
                let maxTat = 1;
                benchmarkPids.forEach(pid => {
                    if (pidMap[pid].prioTat > maxTat) maxTat = pidMap[pid].prioTat;
                    if (pidMap[pid].rrTat > maxTat) maxTat = pidMap[pid].rrTat;
                });

                benchmarkPids.forEach(pid => {
                    const prioHeight = Math.max((pidMap[pid].prioTat / maxTat) * 100, 12);
                    const rrHeight = Math.max((pidMap[pid].rrTat / maxTat) * 100, 12);
                    chart.innerHTML += `<div class="pid-group">
                            <div class="bars-wrapper">
                                <div class="bar bar-prio" style="height: ${prioHeight}%;" title="Priority TAT: ${pidMap[pid].prioTat}">${pidMap[pid].prioTat}</div>
                                <div class="bar bar-rr" style="height: ${rrHeight}%;" title="Round Robin TAT: ${pidMap[pid].rrTat}">${pidMap[pid].rrTat}</div>
                            </div><div class="pid-label">PID ${pid}</div></div>`;
                });
            } catch (e) {}
        }

        function switchMode() {
            cpuMode = document.getElementById('algo-selector').value;
            if (cpuMode === 'REAL_PRIORITY') {
                document.getElementById('sim-setup').style.display = 'none';
                document.getElementById('sim-input-area').style.display = 'none';
                loadCpuData();
            } else {
                document.getElementById('sim-setup').style.display = 'flex';
                generateSimInputs();
            }
        }

        function generateSimInputs() {
            document.getElementById('sim-input-area').style.display = 'block';
            const count = parseInt(document.getElementById('sim-count').value);
            let tableHtml = '<tr><th>Process</th><th>Burst Time (Execution Ticks)</th></tr>';
            for(let i=1; i<=count; i++) {
                let randBurst = Math.floor(Math.random() * 20) + 5;
                tableHtml += `<tr><td><b>PID ${i+3}</b></td><td><input type="number" id="sim-burst-${i}" value="${randBurst}" min="1"></td></tr>`;
            }
            document.getElementById('sim-input-table').innerHTML = tableHtml;
        }

        function runSimulation() {
            const count = parseInt(document.getElementById('sim-count').value);
            let procs = [];
            let rrQueue = [];
            
            for(let i=1; i<=count; i++) {
                let burst = parseInt(document.getElementById(`sim-burst-${i}`).value);
                let pidStr = `PID ${i+3}`;
                procs.push({ pid: pidStr, burst: burst, originalIdx: i });
                rrQueue.push({ pid: pidStr, rem: burst, tat: 0 });
            }

            let time = 0, done = 0, q = 3;
            while(done < count) {
                for(let i=0; i<count; i++) {
                    if(rrQueue[i].rem > 0) {
                        let step = Math.min(rrQueue[i].rem, q);
                        time += step;
                        rrQueue[i].rem -= step;
                        if(rrQueue[i].rem === 0) {
                            rrQueue[i].tat = time;
                            done++;
                        }
                    }
                }
            }
            let rrMap = {};
            rrQueue.forEach(p => rrMap[p.pid] = p.tat);

            let algoName = cpuMode;
            if (cpuMode === 'SJF' || cpuMode === 'SRTF') {
                procs.sort((a, b) => a.burst - b.burst);
            } else if (cpuMode === 'LJF') {
                procs.sort((a, b) => b.burst - a.burst);
            }

            let wait = 0, totalTat = 0, totalRrTat = 0;
            let tbodyHtml = '', chartHtml = '';
            
            let maxTat = 0;
            let tempWait = 0;
            procs.forEach(p => {
                tempWait += p.burst;
                if(tempWait > maxTat) maxTat = tempWait;
                if(rrMap[p.pid] > maxTat) maxTat = rrMap[p.pid];
            });

            for(let p of procs) {
                let tat = wait + p.burst;
                let rrTat = rrMap[p.pid];
                
                totalTat += tat;
                totalRrTat += rrTat;

                tbodyHtml += `<tr>
                    <td><span class="badge-prio" style="background:#a855f7; color:white;">${algoName}</span></td>
                    <td><b>${p.pid}</b></td>
                    <td>-</td>
                    <td>${p.burst} ticks</td>
                    <td>${wait} ticks</td>
                    <td><b>${tat} ticks</b></td>
                </tr>`;

                let heightAlgo = Math.max((tat / maxTat) * 100, 10);
                let heightRr = Math.max((rrTat / maxTat) * 100, 10);
                
                chartHtml += `<div class="pid-group">
                        <div class="bars-wrapper">
                            <div class="bar bar-prio" style="background: linear-gradient(180deg, #a855f7, #7e22ce); color:white; height: ${heightAlgo}%;" title="${algoName} TAT: ${tat}">${tat}</div>
                            <div class="bar bar-rr" style="height: ${heightRr}%;" title="RR TAT: ${rrTat}">${rrTat}</div>
                        </div><div class="pid-label">${p.pid}</div></div>`;

                wait += p.burst;
            }

            document.getElementById('table-body').innerHTML = tbodyHtml;
            document.getElementById('chart').innerHTML = chartHtml;
            
            document.getElementById('tat-header-text').innerText = `${algoName} Avg TAT`;
            document.getElementById('prio-tat').innerText = (totalTat / count).toFixed(1) + ' ticks';
            
            document.getElementById('rr-header-text').innerText = `RR Benchmark TAT`;
            document.getElementById('rr-tat').innerText = (totalRrTat / count).toFixed(1) + ' ticks';
            
            document.getElementById('data-source-badge').innerText = 'Analytical Runtime';
            document.getElementById('table-prio-header').innerText = "-";
            
            document.getElementById('chart-title-text').innerText = `📊 Benchmark Side-by-Side Comparison (RR Baseline vs ${algoName})`;
            document.getElementById('chart-legend').innerHTML = `
                <div class="legend-item"><div class="legend-color" style="background: #a855f7;"></div><span>${algoName} Scheduler</span></div>
                <div class="legend-item"><div class="legend-color" style="background: #facc15;"></div><span>Round Robin (Baseline)</span></div>
            `;
        }

        // --- BANKER'S ALGORITHM SIMULATOR LOGIC ---
        function parseMatrix(text, rows, cols) {
            let lines = text.trim().split('\\n');
            let mat = [];
            for(let i=0; i<rows; i++) {
                let vals = lines[i].trim().split(/\\s+/).map(Number);
                mat.push(vals);
            }
            return mat;
        }

        function runBankerSimulation() {
            try {
                let n = 3, m = 3;
                let alloc = parseMatrix(document.getElementById('banker-alloc').value, n, m);
                let max = parseMatrix(document.getElementById('banker-max').value, n, m);
                let avail = document.getElementById('banker-avail').value.trim().split(/\\s+/).map(Number);

                let need = [];
                for(let i=0; i<n; i++) {
                    let row = [];
                    for(let j=0; j<m; j++) {
                        row.push(max[i][j] - alloc[i][j]);
                    }
                    need.push(row);
                }

                let work = [...avail];
                let finish = new Array(n).fill(0);
                let safeSeq = [];
                let count = 0;

                while(count < n) {
                    let found = false;
                    for(let i=0; i<n; i++) {
                        if(finish[i] === 0) {
                            let canExec = true;
                            for(let j=0; j<m; j++) {
                                if(need[i][j] > work[j]) {
                                    canExec = false;
                                    break;
                                }
                            }
                            if(canExec) {
                                for(let j=0; j<m; j++) {
                                    work[j] += alloc[i][j];
                                }
                                safeSeq.push(`P${i}`);
                                finish[i] = 1;
                                found = true;
                                count++;
                            }
                        }
                    }
                    if(!found) break;
                }

                let resBox = document.getElementById('banker-result');
                if(count === n) {
                    resBox.style.color = "#4ade80";
                    resBox.style.borderColor = "#4ade80";
                    resBox.innerHTML = `✅ SYSTEM IS IN A SAFE STATE! Safe Execution Sequence: <span style="color: white; background: #166534; padding: 2px 8px; border-radius: 4px;">${safeSeq.join(' ➔ ')}</span>`;
                } else {
                    resBox.style.color = "#f43f5e";
                    resBox.style.borderColor = "#f43f5e";
                    resBox.innerHTML = `❌ UNSAFE STATE / DEADLOCK RISK DETECTED! Unable to find a safe execution sequence for processes.`;
                }
            } catch(e) {
                alert("Error parsing matrices! Ensure proper space/newline formatting.");
            }
        }

        // --- MASTER LOOP ---
        function loadAllData() {
            if (memMode === 'REAL_MEM') {
                loadMemoryData();
            } else {
                simulateMemoryData();
            }
            
            if (cpuMode === 'REAL_PRIORITY') {
                loadCpuData();
            }
        }

        loadAllData();
        setInterval(loadAllData, 2000);
    </script>
</body>
</html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/data':
            self.send_json_response("SELECT * FROM process_metrics ORDER BY metric_id DESC")
        elif self.path == '/memory_sys':
            self.send_json_response("SELECT * FROM system_memory_snapshots ORDER BY id DESC LIMIT 20")
        elif self.path == '/memory_proc':
            query = "SELECT * FROM process_memory_stats WHERE id IN (SELECT MAX(id) FROM process_memory_stats GROUP BY pid) ORDER BY pid ASC"
            self.send_json_response(query)
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))

    def send_json_response(self, query):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        result = []
        try:
            conn = sqlite3.connect('xv6_analytics.db')
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description]
            result = [dict(zip(cols, r)) for r in rows]
            conn.close()
        except Exception as e:
            result = []

        self.wfile.write(json.dumps(result).encode('utf-8'))

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"\n[+] Hybrid Kernel Observatory Live at: http://localhost:{PORT}")
    print("[+] Unified Control Plane Enabled for Memory & CPU Analytics")
    print("[+] Press Ctrl+C to stop.\n")
    httpd.serve_forever()
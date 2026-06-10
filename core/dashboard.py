"""
dashboard.py — Generates a self-contained HTML dashboard from analysis results.
Opens automatically in the default browser.

Usage:
    python main.py samples/bad_code.c --dashboard
    python main.py samples/bad_code.py --dashboard
"""

import json
import os
import webbrowser
from typing import List
from core.models import Violation


def generate_dashboard(filepath: str, violations: List[Violation], open_browser: bool = True) -> str:
    errors   = [v for v in violations if v.severity.value == "ERROR"]
    warnings = [v for v in violations if v.severity.value == "WARNING"]
    infos    = [v for v in violations if v.severity.value == "INFO"]

    filename = os.path.basename(filepath)
    total    = len(violations)
    n_err    = len(errors)
    n_warn   = len(warnings)
    n_info   = len(infos)

    # Donut math (r=54, so circumference = 2*pi*54 ≈ 339.3)
    C = 339.3
    err_arc  = round(C * n_err  / total, 1) if total else 0
    warn_arc = round(C * n_warn / total, 1) if total else 0
    info_arc = round(C * n_info / total, 1) if total else 0
    err_off  = round(C * 0.25, 1)                          # start at top
    warn_off = round(err_off  - err_arc,  1)
    info_off = round(warn_off - warn_arc, 1)

    err_pct  = round(n_err  / total * 100) if total else 0
    warn_pct = round(n_warn / total * 100) if total else 0
    info_pct = round(n_info / total * 100) if total else 0

    violations_json = json.dumps([
        {
            "line":     v.line,
            "rule":     v.rule,
            "severity": v.severity.value,
            "message":  v.message,
        }
        for v in sorted(violations, key=lambda x: x.line)
    ])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Static Analyzer — {filename}</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
      background:#f4f4f5;color:#111;font-size:14px;line-height:1.5}}

/* ── TOPBAR ── */
.topbar{{background:#fff;border-bottom:1px solid #e4e4e7;padding:0 28px;
         height:56px;display:flex;align-items:center;justify-content:space-between;
         position:sticky;top:0;z-index:100;box-shadow:0 1px 4px rgba(0,0,0,.04)}}
.topbar-left{{display:flex;align-items:center;gap:14px}}
.brand{{display:flex;align-items:center;gap:8px;font-weight:600;font-size:15px}}
.brand svg{{color:#6366f1}}
.divider{{width:1px;height:20px;background:#e4e4e7}}
.file-pill{{display:flex;align-items:center;gap:6px;background:#f4f4f5;
            border:1px solid #e4e4e7;border-radius:6px;padding:4px 10px;
            font-family:monospace;font-size:12px;color:#555}}
.topbar-right{{display:flex;align-items:center;gap:10px}}
.btn{{border:none;border-radius:7px;padding:7px 16px;font-size:13px;
      font-weight:500;cursor:pointer;transition:opacity .15s}}
.btn:hover{{opacity:.85}}
.btn-ai{{background:#6366f1;color:#fff}}
.btn-fix{{background:#10b981;color:#fff}}
.total-badge{{background:#111;color:#fff;border-radius:20px;
              padding:4px 12px;font-size:12px;font-weight:500}}

/* ── LAYOUT ── */
.main{{max-width:1140px;margin:0 auto;padding:28px 24px}}

/* ── METRIC CARDS ── */
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}}
.metric{{background:#fff;border:1px solid #e4e4e7;border-radius:12px;
         padding:20px 22px;transition:box-shadow .15s}}
.metric:hover{{box-shadow:0 4px 16px rgba(0,0,0,.07)}}
.metric-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}}
.metric-label{{font-size:12px;font-weight:500;color:#888;text-transform:uppercase;letter-spacing:.05em}}
.metric-icon{{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;
              justify-content:center;font-size:16px}}
.icon-total{{background:#f0f0ff}} .icon-err{{background:#fff0f0}}
.icon-warn{{background:#fffbeb}} .icon-info{{background:#eff6ff}}
.metric-val{{font-size:34px;font-weight:700;letter-spacing:-.5px}}
.c-total{{color:#111}} .c-err{{color:#dc2626}} .c-warn{{color:#d97706}} .c-info{{color:#2563eb}}
.metric-sub{{font-size:12px;color:#aaa;margin-top:4px}}

/* ── TWO-COL ── */
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}}
.card{{background:#fff;border:1px solid #e4e4e7;border-radius:12px;padding:22px}}
.card-title{{font-size:11px;font-weight:600;color:#888;text-transform:uppercase;
             letter-spacing:.06em;margin-bottom:18px}}

/* ── DONUT ── */
.donut-wrap{{display:flex;align-items:center;gap:28px}}
.donut-svg{{flex-shrink:0}}
.donut-legend{{flex:1}}
.leg-row{{display:flex;align-items:center;gap:10px;margin-bottom:14px}}
.leg-row:last-child{{margin-bottom:0}}
.leg-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.leg-label{{flex:1;font-size:13px;color:#444}}
.leg-num{{font-weight:600;font-size:14px}}
.leg-pct{{font-size:12px;color:#aaa;margin-left:4px}}
.leg-bar-track{{width:100%;height:5px;background:#f0f0f0;border-radius:3px;margin-top:3px}}
.leg-bar-fill{{height:100%;border-radius:3px}}

/* ── VIOLATIONS TABLE ── */
.vcard{{background:#fff;border:1px solid #e4e4e7;border-radius:12px;
        overflow:hidden;margin-bottom:24px}}
.vcard-header{{display:flex;align-items:center;justify-content:space-between;
               padding:16px 22px;border-bottom:1px solid #f0f0f0}}
.vcard-title{{font-size:11px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:.06em}}
.filter-tabs{{display:flex;gap:6px}}
.ftab{{background:#f4f4f5;border:1px solid #e4e4e7;border-radius:6px;
       padding:5px 13px;font-size:12px;cursor:pointer;color:#666;transition:all .15s;
       user-select:none}}
.ftab:hover{{border-color:#aaa;color:#333}}
.ftab.active{{background:#111;color:#fff;border-color:#111;font-weight:500}}

.search-wrap{{padding:12px 22px;border-bottom:1px solid #f0f0f0;display:flex;gap:10px}}
.search-wrap input{{flex:1;padding:8px 14px;border:1px solid #e4e4e7;
                    border-radius:7px;font-size:13px;outline:none;background:#fafafa}}
.search-wrap input:focus{{border-color:#6366f1;background:#fff}}
.sort-btn{{padding:8px 14px;border:1px solid #e4e4e7;border-radius:7px;
           background:#fafafa;font-size:12px;cursor:pointer;color:#666;white-space:nowrap}}
.sort-btn:hover{{background:#f0f0f0}}

table{{width:100%;border-collapse:collapse;font-size:13px}}
thead th{{padding:10px 22px;text-align:left;font-size:11px;font-weight:600;color:#888;
          background:#fafafa;border-bottom:1px solid #f0f0f0;
          text-transform:uppercase;letter-spacing:.05em;cursor:pointer;user-select:none}}
thead th:hover{{color:#333}}
thead th.sorted{{color:#6366f1}}
td{{padding:12px 22px;border-bottom:1px solid #f9f9f9;vertical-align:middle}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:#fafafa}}

.badge{{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;
        border-radius:20px;font-size:11px;font-weight:500;white-space:nowrap}}
.b-err {{background:#fef2f2;color:#dc2626}}
.b-warn{{background:#fffbeb;color:#d97706}}
.b-info{{background:#eff6ff;color:#2563eb}}
.rule-code{{font-family:monospace;font-size:12px;color:#888;background:#f4f4f5;
            padding:2px 7px;border-radius:4px}}
.line-num{{font-family:monospace;font-size:12px;color:#aaa;font-weight:500}}
.msg-text{{color:#333;max-width:420px}}

/* ── AI BANNER ── */
.ai-banner{{background:linear-gradient(135deg,#eef2ff 0%,#f0fdf4 100%);
            border:1px solid #c7d2fe;border-radius:12px;
            padding:20px 24px;display:flex;align-items:center;
            justify-content:space-between;gap:20px;margin-bottom:24px}}
.ai-icon{{width:42px;height:42px;background:#6366f1;border-radius:10px;
          display:flex;align-items:center;justify-content:center;
          font-size:20px;flex-shrink:0}}
.ai-body{{flex:1}}
.ai-title{{font-size:15px;font-weight:600;color:#3730a3;margin-bottom:4px}}
.ai-sub{{font-size:13px;color:#6366f1}}
.ai-actions{{display:flex;gap:10px;flex-shrink:0}}
.ai-cmd{{font-family:monospace;font-size:12px;background:#fff;
         border:1px solid #c7d2fe;border-radius:7px;padding:8px 14px;
         color:#3730a3;cursor:pointer;transition:all .15s}}
.ai-cmd:hover{{background:#eef2ff}}

/* ── EMPTY ── */
.empty{{padding:60px;text-align:center;color:#aaa}}
.empty-check{{width:56px;height:56px;background:#f0fdf4;border-radius:50%;
              display:flex;align-items:center;justify-content:center;
              font-size:26px;margin:0 auto 16px}}
.empty-title{{font-size:16px;font-weight:600;color:#333;margin-bottom:6px}}

/* ── FOOTER ── */
.footer{{text-align:center;padding:20px;color:#bbb;font-size:12px}}

/* ── PAGINATION ── */
.pager{{display:flex;align-items:center;justify-content:space-between;
        padding:12px 22px;border-top:1px solid #f0f0f0;}}
.pager-info{{font-size:12px;color:#888}}
.pager-btns{{display:flex;gap:6px}}
.pager-btn{{padding:5px 12px;border:1px solid #e4e4e7;border-radius:6px;
            background:#fff;font-size:12px;cursor:pointer;color:#555}}
.pager-btn:hover{{background:#f4f4f5}}
.pager-btn:disabled{{opacity:.4;cursor:default}}

@media(max-width:720px){{
  .metrics{{grid-template-columns:repeat(2,1fr)}}
  .two-col{{grid-template-columns:1fr}}
  .ai-banner{{flex-direction:column;align-items:flex-start}}
}}
</style>
</head>
<body>

<!-- TOPBAR -->
<div class="topbar">
  <div class="topbar-left">
    <div class="brand">
      <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
        <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
      </svg>
      Static Analyzer
    </div>
    <div class="divider"></div>
    <div class="file-pill">
      <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      {filename}
    </div>
  </div>
  <div class="topbar-right">
    <span class="total-badge">{total} issues</span>
    <button class="btn btn-ai" onclick="copyCmd('--ai')">✦ AI Fix</button>
    <button class="btn btn-fix" onclick="copyCmd('--ai --fix')">↓ Save Fixed</button>
  </div>
</div>

<div class="main">

  <!-- METRIC CARDS -->
  <div class="metrics">
    <div class="metric">
      <div class="metric-top">
        <span class="metric-label">Total Issues</span>
        <div class="metric-icon icon-total">🔍</div>
      </div>
      <div class="metric-val c-total">{total}</div>
      <div class="metric-sub">across {filename}</div>
    </div>
    <div class="metric">
      <div class="metric-top">
        <span class="metric-label">Errors</span>
        <div class="metric-icon icon-err">🚨</div>
      </div>
      <div class="metric-val c-err">{n_err}</div>
      <div class="metric-sub">must fix before compiling</div>
    </div>
    <div class="metric">
      <div class="metric-top">
        <span class="metric-label">Warnings</span>
        <div class="metric-icon icon-warn">⚠️</div>
      </div>
      <div class="metric-val c-warn">{n_warn}</div>
      <div class="metric-sub">risky patterns detected</div>
    </div>
    <div class="metric">
      <div class="metric-top">
        <span class="metric-label">Info</span>
        <div class="metric-icon icon-info">💡</div>
      </div>
      <div class="metric-val c-info">{n_info}</div>
      <div class="metric-sub">style &amp; optimization hints</div>
    </div>
  </div>

  <!-- CHARTS ROW -->
  <div class="two-col">

    <!-- DONUT CHART -->
    <div class="card">
      <div class="card-title">Severity Breakdown</div>
      <div class="donut-wrap">
        <svg class="donut-svg" width="130" height="130" viewBox="0 0 130 130">
          <circle cx="65" cy="65" r="54" fill="none" stroke="#f0f0f0" stroke-width="18"/>
          <circle cx="65" cy="65" r="54" fill="none" stroke="#dc2626" stroke-width="18"
            stroke-dasharray="{err_arc} {C}" stroke-dashoffset="{err_off}"
            transform="rotate(-90 65 65)" style="transition:stroke-dasharray .5s"/>
          <circle cx="65" cy="65" r="54" fill="none" stroke="#f59e0b" stroke-width="18"
            stroke-dasharray="{warn_arc} {C}" stroke-dashoffset="{warn_off}"
            transform="rotate(-90 65 65)" style="transition:stroke-dasharray .5s"/>
          <circle cx="65" cy="65" r="54" fill="none" stroke="#3b82f6" stroke-width="18"
            stroke-dasharray="{info_arc} {C}" stroke-dashoffset="{info_off}"
            transform="rotate(-90 65 65)" style="transition:stroke-dasharray .5s"/>
          <text x="65" y="60" text-anchor="middle" font-size="22" font-weight="700" fill="#111">{total}</text>
          <text x="65" y="78" text-anchor="middle" font-size="11" fill="#aaa">issues</text>
        </svg>
        <div class="donut-legend">
          <div class="leg-row">
            <span class="leg-dot" style="background:#dc2626"></span>
            <div style="flex:1">
              <div style="display:flex;align-items:center;justify-content:space-between">
                <span class="leg-label">Errors</span>
                <span><span class="leg-num c-err">{n_err}</span><span class="leg-pct">{err_pct}%</span></span>
              </div>
              <div class="leg-bar-track"><div class="leg-bar-fill" style="width:{err_pct}%;background:#dc2626"></div></div>
            </div>
          </div>
          <div class="leg-row">
            <span class="leg-dot" style="background:#f59e0b"></span>
            <div style="flex:1">
              <div style="display:flex;align-items:center;justify-content:space-between">
                <span class="leg-label">Warnings</span>
                <span><span class="leg-num c-warn">{n_warn}</span><span class="leg-pct">{warn_pct}%</span></span>
              </div>
              <div class="leg-bar-track"><div class="leg-bar-fill" style="width:{warn_pct}%;background:#f59e0b"></div></div>
            </div>
          </div>
          <div class="leg-row">
            <span class="leg-dot" style="background:#3b82f6"></span>
            <div style="flex:1">
              <div style="display:flex;align-items:center;justify-content:space-between">
                <span class="leg-label">Info</span>
                <span><span class="leg-num c-info">{n_info}</span><span class="leg-pct">{info_pct}%</span></span>
              </div>
              <div class="leg-bar-track"><div class="leg-bar-fill" style="width:{info_pct}%;background:#3b82f6"></div></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TOP RULES -->
    <div class="card">
      <div class="card-title">Most Common Rules</div>
      <div id="top-rules-chart"></div>
    </div>

  </div>

  <!-- AI BANNER -->
  <div class="ai-banner">
    <div class="ai-icon">✦</div>
    <div class="ai-body">
      <div class="ai-title">AI-powered fixes available</div>
      <div class="ai-sub">Claude can automatically fix all {total} issues and generate corrected code for you.</div>
    </div>
    <div class="ai-actions">
      <button class="ai-cmd" onclick="copyCmd('--ai')" title="Copy command">
        python main.py {filename} --ai
      </button>
      <button class="btn btn-ai" onclick="copyCmd('--ai --fix')">Generate fix ↗</button>
    </div>
  </div>

  <!-- VIOLATIONS TABLE -->
  <div class="vcard">
    <div class="vcard-header">
      <span class="vcard-title">All Violations</span>
      <div class="filter-tabs">
        <span class="ftab active" onclick="setFilter('all',this)">All <span style="opacity:.6">({total})</span></span>
        <span class="ftab" onclick="setFilter('ERROR',this)">Errors <span style="opacity:.6">({n_err})</span></span>
        <span class="ftab" onclick="setFilter('WARNING',this)">Warnings <span style="opacity:.6">({n_warn})</span></span>
        <span class="ftab" onclick="setFilter('INFO',this)">Info <span style="opacity:.6">({n_info})</span></span>
      </div>
    </div>
    <div class="search-wrap">
      <input type="text" id="search" placeholder="Search by rule, message, or line number…" oninput="applyFilters()">
      <button class="sort-btn" onclick="toggleSort()">⇅ Sort by Line</button>
    </div>
    {"" if not total else """
    <table>
      <thead>
        <tr>
          <th onclick="sortBy('line')"   id="th-line">Line ↕</th>
          <th onclick="sortBy('rule')"   id="th-rule">Rule ↕</th>
          <th onclick="sortBy('severity')" id="th-sev">Severity ↕</th>
          <th>Message</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
    <div class="pager">
      <span class="pager-info" id="pager-info"></span>
      <div class="pager-btns">
        <button class="pager-btn" id="btn-prev" onclick="prevPage()">← Prev</button>
        <button class="pager-btn" id="btn-next" onclick="nextPage()">Next →</button>
      </div>
    </div>"""}
    {"<div class='empty'><div class='empty-check'>✓</div><div class='empty-title'>No issues found!</div><div>Your code looks clean.</div></div>" if not total else ""}
  </div>

</div>

<div class="footer">
  Generated by <strong>Static Analyzer v2</strong> &nbsp;·&nbsp; {filename} &nbsp;·&nbsp; {total} issues found
</div>

<!-- TOAST -->
<div id="toast" style="position:fixed;bottom:24px;right:24px;background:#111;color:#fff;
  padding:10px 18px;border-radius:8px;font-size:13px;opacity:0;transition:opacity .3s;
  pointer-events:none;z-index:999">Copied to clipboard!</div>

<script>
const DATA = {violations_json};

const SEV_ICON = {{ERROR:'🚨', WARNING:'⚠️', INFO:'💡'}};
const SEV_CLASS = {{ERROR:'b-err', WARNING:'b-warn', INFO:'b-info'}};

let filtered = [...DATA];
let currentFilter = 'all';
let sortKey = 'line';
let sortAsc = true;
let page = 0;
const PAGE_SIZE = 20;

// ── TOP RULES CHART ──────────────────────────
function buildTopRules() {{
  const counts = {{}};
  DATA.forEach(v => {{ counts[v.rule] = (counts[v.rule] || 0) + 1; }});
  const sorted = Object.entries(counts).sort((a,b) => b[1]-a[1]).slice(0,6);
  const max = sorted[0]?.[1] || 1;
  const wrap = document.getElementById('top-rules-chart');
  if (!wrap) return;
  wrap.innerHTML = sorted.map(([rule, count]) => {{
    const pct = Math.round(count/max*100);
    return `<div style="display:flex;align-items:center;gap:10px;margin-bottom:11px">
      <span style="font-family:monospace;font-size:11px;background:#f4f4f5;
        padding:2px 7px;border-radius:4px;color:#555;width:62px;text-align:center;flex-shrink:0">${{rule}}</span>
      <div style="flex:1;height:8px;background:#f0f0f0;border-radius:4px;overflow:hidden">
        <div style="width:${{pct}}%;height:100%;background:#6366f1;border-radius:4px;transition:width .4s"></div>
      </div>
      <span style="font-size:12px;color:#888;width:18px;text-align:right">${{count}}</span>
    </div>`;
  }}).join('');
}}

// ── TABLE ────────────────────────────────────
function applyFilters() {{
  const q = (document.getElementById('search')?.value||'').toLowerCase();
  filtered = DATA.filter(r => {{
    const matchSev = currentFilter === 'all' || r.severity === currentFilter;
    const matchQ   = !q || r.rule.toLowerCase().includes(q) ||
                     r.message.toLowerCase().includes(q) ||
                     String(r.line).includes(q);
    return matchSev && matchQ;
  }});
  sortFiltered();
  page = 0;
  renderTable();
}}

function sortFiltered() {{
  filtered.sort((a,b) => {{
    let av = a[sortKey], bv = b[sortKey];
    if (typeof av === 'string') av = av.toLowerCase(), bv = bv.toLowerCase();
    return sortAsc ? (av > bv ? 1 : av < bv ? -1 : 0)
                   : (av < bv ? 1 : av > bv ? -1 : 0);
  }});
}}

function renderTable() {{
  const tb = document.getElementById('tbody');
  if (!tb) return;
  const start = page * PAGE_SIZE;
  const slice = filtered.slice(start, start + PAGE_SIZE);
  if (!slice.length) {{
    tb.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:36px;color:#aaa">No matching violations</td></tr>';
  }} else {{
    tb.innerHTML = slice.map(r => `
      <tr>
        <td class="line-num">${{r.line}}</td>
        <td><span class="rule-code">${{r.rule}}</span></td>
        <td><span class="badge ${{SEV_CLASS[r.severity]}}">${{SEV_ICON[r.severity]}} ${{r.severity}}</span></td>
        <td class="msg-text">${{r.message}}</td>
      </tr>`).join('');
  }}
  const info = document.getElementById('pager-info');
  const prev = document.getElementById('btn-prev');
  const next = document.getElementById('btn-next');
  const total = filtered.length;
  if (info) info.textContent = `Showing ${{Math.min(start+1,total)}}–${{Math.min(start+PAGE_SIZE,total)}} of ${{total}}`;
  if (prev) prev.disabled = page === 0;
  if (next) next.disabled = start + PAGE_SIZE >= total;
}}

function setFilter(f, el) {{
  currentFilter = f;
  document.querySelectorAll('.ftab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  applyFilters();
}}

function sortBy(key) {{
  if (sortKey === key) sortAsc = !sortAsc;
  else {{ sortKey = key; sortAsc = true; }}
  ['line','rule','sev'].forEach(k => {{
    const th = document.getElementById('th-'+k);
    if (th) th.classList.remove('sorted');
  }});
  const thMap = {{line:'th-line',rule:'th-rule',severity:'th-sev'}};
  const active = document.getElementById(thMap[key]);
  if (active) active.classList.add('sorted');
  sortFiltered();
  renderTable();
}}

function toggleSort() {{
  sortAsc = !sortAsc;
  sortFiltered();
  renderTable();
}}

function prevPage() {{ if (page > 0) {{ page--; renderTable(); }} }}
function nextPage() {{ if ((page+1)*PAGE_SIZE < filtered.length) {{ page++; renderTable(); }} }}

// ── COPY COMMAND ─────────────────────────────
function copyCmd(flag) {{
  const cmd = `python main.py {filename} ${{flag}}`;
  navigator.clipboard.writeText(cmd).catch(()=>{{}});
  const toast = document.getElementById('toast');
  toast.textContent = 'Command copied: ' + cmd;
  toast.style.opacity = '1';
  setTimeout(() => toast.style.opacity = '0', 2500);
}}

// ── INIT ─────────────────────────────────────
buildTopRules();
applyFilters();
</script>
</body>
</html>"""

    base = os.path.splitext(filepath)[0]
    out_path = base + "_report.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    if open_browser:
        webbrowser.open("file://" + os.path.abspath(out_path))

    return out_path

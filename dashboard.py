import os
import yaml
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from src.database import Database
from src.ai_coach import AICoach

app = FastAPI(title="Trading AI Bot Dashboard")


def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML


@app.get("/api/status")
def status():
    cfg = load_config()
    db = Database("data/bot.db")
    ai = AICoach("data/ai_model.json")

    ai_report = ""
    if os.path.exists("logs/ai_report.txt"):
        with open("logs/ai_report.txt", "r", encoding="utf-8") as f:
            ai_report = f.read()

    return JSONResponse({
        "mode": "PAPER-TRADING",
        "symbols": cfg.get("symbols", []),
        "entry_timeframe": cfg.get("timeframes", {}).get("entry", "15m"),
        "trend_timeframe": cfg.get("timeframes", {}).get("trend", "1h"),
        "performance": db.performance_summary(cfg["risk"]["equity_start"]),
        "snapshots": db.get_market_snapshots(),
        "open_trades": db.get_open_trades(),
        "recent_trades": db.get_recent_trades(12),
        "ai_weights": ai.model.get("weights", {}),
        "ai_report": ai_report,
    })


HTML = """
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Trading AI Bot Dashboard</title>
  <style>
    :root {
      --bg:#070b10; --card:rgba(16,24,35,.9); --line:rgba(18,230,160,.18);
      --text:#eef7f4; --mut:#8fa2a0; --g:#12e6a0; --r:#ff5c7a; --b:#6fb7ff; --y:#ffd166;
    }
    * { box-sizing:border-box; }
    body {
      margin:0; min-height:100vh; padding:28px;
      background:
        radial-gradient(circle at 20% 0,rgba(18,230,160,.18),transparent 30%),
        radial-gradient(circle at 80% 10%,rgba(111,183,255,.12),transparent 28%),
        var(--bg);
      color:var(--text); font-family:Inter,system-ui,Segoe UI,sans-serif;
    }
    .shell { max-width:1400px; margin:auto; }
    .top { display:flex; justify-content:space-between; gap:20px; align-items:center; margin-bottom:22px; }
    h1 { font-size:clamp(30px,5vw,52px); letter-spacing:-.05em; margin:0; }
    p { color:var(--mut); }
    .badge { color:var(--g); border:1px solid var(--line); background:rgba(18,230,160,.08); padding:10px 14px; border-radius:999px; font-weight:800; }
    .grid { display:grid; gap:16px; }
    .kpis { grid-template-columns:repeat(6,minmax(0,1fr)); margin-bottom:16px; }
    .main { grid-template-columns:1.5fr .9fr; align-items:start; }
    .coins { grid-template-columns:repeat(2,minmax(0,1fr)); }
    .card { background:linear-gradient(180deg,var(--card),rgba(11,18,28,.94)); border:1px solid var(--line); border-radius:24px; padding:18px; box-shadow:0 24px 80px rgba(0,0,0,.42); }
    .label { color:var(--mut); font-size:12px; text-transform:uppercase; letter-spacing:.08em; }
    .value { font-size:24px; font-weight:900; margin-top:8px; }
    .positive { color:var(--g); } .negative { color:var(--r); } .blue { color:var(--b); } .yellow { color:var(--y); } .muted { color:var(--mut); }
    .coin-head { display:flex; justify-content:space-between; gap:14px; align-items:start; }
    .coin-title { font-size:24px; font-weight:900; letter-spacing:-.04em; }
    .signal { padding:8px 12px; border-radius:999px; font-weight:900; background:rgba(255,255,255,.06); }
    .LONG { color:var(--g); } .SHORT { color:var(--r); } .WAIT { color:var(--mut); }
    .meter { height:10px; background:rgba(255,255,255,.08); border-radius:999px; overflow:hidden; margin:12px 0; }
    .meter div { height:100%; background:linear-gradient(90deg,var(--g),var(--b)); border-radius:999px; }
    .stats { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin-top:14px; }
    .mini { background:rgba(255,255,255,.045); border:1px solid rgba(255,255,255,.07); border-radius:16px; padding:12px; }
    .mini span { display:block; color:var(--mut); font-size:12px; margin-bottom:4px; }
    .reason { margin-top:14px; color:var(--mut); line-height:1.45; font-size:14px; }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    th,td { padding:10px 8px; border-bottom:1px solid rgba(255,255,255,.07); text-align:left; }
    th { color:var(--mut); font-size:11px; text-transform:uppercase; letter-spacing:.08em; }
    pre { white-space:pre-wrap; color:var(--mut); line-height:1.45; max-height:360px; overflow:auto; }
    .weights { display:grid; gap:10px; }
    .weight-row { display:grid; grid-template-columns:120px 1fr 48px; gap:10px; align-items:center; font-size:13px; }
    .bar { height:8px; background:rgba(255,255,255,.08); border-radius:999px; overflow:hidden; }
    .bar div { height:100%; background:linear-gradient(90deg,var(--g),var(--b)); }
    .footer { margin-top:16px; color:var(--mut); font-size:12px; }
    @media(max-width:1100px){ .kpis{grid-template-columns:repeat(3,1fr)} .main{grid-template-columns:1fr} }
    @media(max-width:760px){ body{padding:16px} .top{flex-direction:column;align-items:flex-start} .kpis,.coins{grid-template-columns:1fr} .stats{grid-template-columns:1fr} }
  </style>
</head>
<body>
  <div class="shell">
    <div class="top">
      <div>
        <h1>Trading AI Bot</h1>
        <p>Live Paper-Trading Dashboard. Permanente Marktanalyse ohne echtes Geld.</p>
      </div>
      <div class="badge" id="mode">PAPER-TRADING</div>
    </div>

    <div class="grid kpis">
      <div class="card"><div class="label">Equity</div><div class="value" id="equity">-</div></div>
      <div class="card"><div class="label">Total PnL</div><div class="value" id="totalPnl">-</div></div>
      <div class="card"><div class="label">Heute</div><div class="value" id="dailyPnl">-</div></div>
      <div class="card"><div class="label">Winrate</div><div class="value" id="winrate">-</div></div>
      <div class="card"><div class="label">Profit Factor</div><div class="value" id="profitFactor">-</div></div>
      <div class="card"><div class="label">Offene Trades</div><div class="value" id="openTradesCount">-</div></div>
    </div>

    <div class="grid main">
      <div class="grid">
        <div class="grid coins" id="coins"></div>
        <div class="card"><h2>Offene Paper-Trades</h2><div id="openTrades"></div></div>
        <div class="card"><h2>Letzte Trades</h2><div id="recentTrades"></div></div>
      </div>
      <div class="grid">
        <div class="card"><h2>KI-Gewichte</h2><div class="weights" id="weights"></div></div>
        <div class="card"><h2>KI-Report</h2><pre id="aiReport">Noch kein KI-Report vorhanden.</pre></div>
      </div>
    </div>

    <div class="footer" id="lastUpdate">Warte auf Daten...</div>
  </div>

<script>
const fmt = (n,d=2) => n===null || n===undefined || Number.isNaN(Number(n)) ? "-" : Number(n).toLocaleString("de-CH",{minimumFractionDigits:d,maximumFractionDigits:d});
const money = (n) => fmt(n,2);
const pnlClass = (n) => Number(n) >= 0 ? "positive" : "negative";

function table(trades, open=false) {
  if (!trades || trades.length === 0) return '<p class="muted">Keine Trades vorhanden.</p>';
  return '<table><thead><tr><th>Symbol</th><th>Side</th><th>Entry</th><th>SL</th><th>TP</th><th>' + (open ? 'Conf.' : 'PnL') + '</th><th>Status</th></tr></thead><tbody>' +
    trades.map(t => '<tr><td>'+t.symbol+'</td><td class="'+t.side+'">'+t.side+'</td><td>'+fmt(t.entry)+'</td><td>'+fmt(t.stop_loss)+'</td><td>'+fmt(t.take_profit)+'</td><td class="'+(open?'blue':pnlClass(t.pnl))+'">'+(open?fmt(t.confidence,1)+'%':money(t.pnl))+'</td><td class="muted">'+(t.close_reason || t.status || '-')+'</td></tr>').join('') +
    '</tbody></table>';
}

function coin(s) {
  const conf = Number(s.confidence || 0);
  const trendClass = s.trend === "Bullish" ? "positive" : s.trend === "Bearish" ? "negative" : "muted";
  const rsiClass = s.rsi < 35 ? "positive" : s.rsi > 65 ? "negative" : "blue";
  return '<div class="card">' +
    '<div class="coin-head"><div><div class="coin-title">'+s.symbol+'</div><p>Preis: '+fmt(s.price)+'</p></div><div class="signal '+s.signal_side+'">'+(s.signal_side || "WAIT")+'</div></div>' +
    '<div class="label">Confidence</div><div class="meter"><div style="width:'+Math.max(0,Math.min(100,conf))+'%"></div></div><strong>'+fmt(conf,1)+'%</strong>' +
    '<div class="stats">' +
    '<div class="mini"><span>Trend 1h</span><strong class="'+trendClass+'">'+s.trend+'</strong></div>' +
    '<div class="mini"><span>RSI</span><strong class="'+rsiClass+'">'+fmt(s.rsi,1)+'</strong></div>' +
    '<div class="mini"><span>MACD Hist</span><strong>'+fmt(s.macd_hist,4)+'</strong></div>' +
    '<div class="mini"><span>ATR</span><strong>'+fmt(s.atr)+'</strong></div>' +
    '<div class="mini"><span>Support</span><strong>'+fmt(s.support)+'</strong></div>' +
    '<div class="mini"><span>Resistance</span><strong>'+fmt(s.resistance)+'</strong></div>' +
    '</div><div class="reason">'+(s.reason || 'Kein starkes Setup. Bot wartet.')+'</div></div>';
}

async function load() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    const p = data.performance || {};
    document.getElementById("mode").textContent = data.mode || "PAPER-TRADING";
    document.getElementById("equity").textContent = money(p.equity);
    document.getElementById("totalPnl").textContent = money(p.total_pnl);
    document.getElementById("totalPnl").className = "value " + pnlClass(p.total_pnl);
    document.getElementById("dailyPnl").textContent = money(p.daily_pnl);
    document.getElementById("dailyPnl").className = "value " + pnlClass(p.daily_pnl);
    document.getElementById("winrate").textContent = fmt(p.winrate,1) + "%";
    document.getElementById("profitFactor").textContent = fmt(p.profit_factor,2);
    document.getElementById("openTradesCount").textContent = p.open_trades ?? 0;
    document.getElementById("coins").innerHTML = (data.snapshots || []).map(coin).join("") || '<div class="card"><p class="muted">Noch keine Marktdaten. Starte zuerst python main.py.</p></div>';
    document.getElementById("openTrades").innerHTML = table(data.open_trades, true);
    document.getElementById("recentTrades").innerHTML = table(data.recent_trades, false);
    document.getElementById("weights").innerHTML = Object.entries(data.ai_weights || {}).map(([k,v]) => '<div class="weight-row"><span class="muted">'+k+'</span><div class="bar"><div style="width:'+Math.min(100,Number(v)/1.45*100)+'%"></div></div><strong>'+fmt(v,2)+'</strong></div>').join("");
    document.getElementById("aiReport").textContent = data.ai_report || "Noch kein KI-Report vorhanden.";
    document.getElementById("lastUpdate").textContent = "Letztes Update: " + new Date().toLocaleString("de-CH");
  } catch(e) {
    document.getElementById("lastUpdate").textContent = "Dashboard-Fehler: " + e.message;
  }
}

load();
setInterval(load, 3000);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    uvicorn.run("dashboard:app", host="127.0.0.1", port=8000, reload=False)

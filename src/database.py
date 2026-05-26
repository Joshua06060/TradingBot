import sqlite3
import json
from datetime import datetime, timezone, timedelta


class Database:
    def __init__(self, path):
        self.path = path
        self._init()

    def conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def _init(self):
        with self.conn() as c:
            c.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                side TEXT,
                entry REAL,
                stop_loss REAL,
                take_profit REAL,
                size REAL,
                risk_amount REAL,
                confidence REAL,
                rr REAL,
                reason TEXT,
                features TEXT,
                status TEXT,
                opened_at TEXT,
                closed_at TEXT,
                exit_price REAL,
                pnl REAL,
                close_reason TEXT,
                learned INTEGER DEFAULT 0
            )
            """)
            c.execute("""
            CREATE TABLE IF NOT EXISTS market_snapshots (
                symbol TEXT PRIMARY KEY,
                price REAL,
                trend TEXT,
                trend_ema_50 REAL,
                trend_ema_200 REAL,
                entry_ema_50 REAL,
                entry_ema_200 REAL,
                rsi REAL,
                macd_hist REAL,
                atr REAL,
                volume REAL,
                volume_sma REAL,
                resistance REAL,
                support REAL,
                signal_side TEXT,
                confidence REAL,
                rr REAL,
                reason TEXT,
                updated_at TEXT
            )
            """)
            c.commit()

    def insert_trade(self, trade):
        with self.conn() as c:
            cur = c.execute("""
            INSERT INTO trades (
                symbol, side, entry, stop_loss, take_profit, size, risk_amount,
                confidence, rr, reason, features, status, opened_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade["symbol"], trade["side"], trade["entry"], trade["stop_loss"],
                trade["take_profit"], trade["size"], trade["risk_amount"],
                trade["confidence"], trade["rr"], trade["reason"],
                json.dumps(trade["features"]), trade["status"], trade["opened_at"]
            ))
            c.commit()
            return cur.lastrowid

    def close_trade(self, trade_id, exit_price, pnl, reason):
        with self.conn() as c:
            c.execute("""
            UPDATE trades
            SET status='closed', closed_at=?, exit_price=?, pnl=?, close_reason=?
            WHERE id=?
            """, (datetime.now(timezone.utc).isoformat(), exit_price, pnl, reason, trade_id))
            c.commit()

    def upsert_market_snapshot(self, s):
        with self.conn() as c:
            c.execute("""
            INSERT INTO market_snapshots (
                symbol, price, trend, trend_ema_50, trend_ema_200, entry_ema_50, entry_ema_200,
                rsi, macd_hist, atr, volume, volume_sma, resistance, support,
                signal_side, confidence, rr, reason, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                price=excluded.price, trend=excluded.trend,
                trend_ema_50=excluded.trend_ema_50, trend_ema_200=excluded.trend_ema_200,
                entry_ema_50=excluded.entry_ema_50, entry_ema_200=excluded.entry_ema_200,
                rsi=excluded.rsi, macd_hist=excluded.macd_hist, atr=excluded.atr,
                volume=excluded.volume, volume_sma=excluded.volume_sma,
                resistance=excluded.resistance, support=excluded.support,
                signal_side=excluded.signal_side, confidence=excluded.confidence,
                rr=excluded.rr, reason=excluded.reason, updated_at=excluded.updated_at
            """, (s["symbol"], s["price"], s["trend"], s["trend_ema_50"], s["trend_ema_200"],
                  s["entry_ema_50"], s["entry_ema_200"], s["rsi"], s["macd_hist"], s["atr"],
                  s["volume"], s["volume_sma"], s["resistance"], s["support"], s["signal_side"],
                  s["confidence"], s["rr"], s["reason"], s["updated_at"]))
            c.commit()

    def _rows(self, query, params=()):
        with self.conn() as c:
            rows = c.execute(query, params).fetchall()
        return [self._dict(r) for r in rows]

    def _dict(self, row):
        d = dict(row)
        if d.get("features"):
            d["features"] = json.loads(d["features"])
        return d

    def get_market_snapshots(self):
        return self._rows("SELECT * FROM market_snapshots ORDER BY symbol ASC")

    def get_all_trades(self):
        return self._rows("SELECT * FROM trades ORDER BY id DESC")

    def get_recent_trades(self, limit=20):
        return self._rows("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,))

    def get_open_trades(self):
        return self._rows("SELECT * FROM trades WHERE status='open' ORDER BY opened_at DESC")

    def has_open_trade(self, symbol):
        with self.conn() as c:
            row = c.execute("SELECT COUNT(*) AS n FROM trades WHERE symbol=? AND status='open'", (symbol,)).fetchone()
        return row["n"] > 0

    def get_recent_closed_unlearned(self):
        return self._rows("SELECT * FROM trades WHERE status='closed' AND learned=0 ORDER BY id ASC LIMIT 50")

    def mark_trades_learned(self, ids):
        if not ids: return
        with self.conn() as c:
            c.executemany("UPDATE trades SET learned=1 WHERE id=?", [(i,) for i in ids])
            c.commit()

    def trades_today_count(self):
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        with self.conn() as c:
            row = c.execute("SELECT COUNT(*) AS n FROM trades WHERE opened_at >= ?", (start,)).fetchone()
        return row["n"]

    def consecutive_losses(self):
        closed = self._rows("SELECT * FROM trades WHERE status='closed' ORDER BY closed_at DESC LIMIT 20")
        n = 0
        for t in closed:
            if t["pnl"] is not None and t["pnl"] <= 0: n += 1
            else: break
        return n

    def pnl_since(self, period):
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) if period == "day" else now - timedelta(days=7)
        with self.conn() as c:
            row = c.execute("SELECT COALESCE(SUM(pnl), 0) AS pnl FROM trades WHERE status='closed' AND closed_at >= ?", (start.isoformat(),)).fetchone()
        return float(row["pnl"])

    def current_equity(self, start_equity):
        with self.conn() as c:
            row = c.execute("SELECT COALESCE(SUM(pnl), 0) AS pnl FROM trades WHERE status='closed'").fetchone()
        return float(start_equity + row["pnl"])

    def performance_summary(self, start_equity):
        closed = self._rows("SELECT * FROM trades WHERE status='closed'")
        wins = [t for t in closed if t["pnl"] is not None and t["pnl"] > 0]
        losses = [t for t in closed if t["pnl"] is not None and t["pnl"] <= 0]
        total_pnl = sum(t["pnl"] or 0 for t in closed)
        gross_profit = sum(t["pnl"] or 0 for t in wins)
        gross_loss = abs(sum(t["pnl"] or 0 for t in losses))
        return {
            "equity": start_equity + total_pnl,
            "total_pnl": total_pnl,
            "daily_pnl": self.pnl_since("day"),
            "weekly_pnl": self.pnl_since("week"),
            "closed_trades": len(closed),
            "open_trades": len(self.get_open_trades()),
            "wins": len(wins), "losses": len(losses),
            "winrate": (len(wins) / len(closed) * 100) if closed else 0,
            "profit_factor": (gross_profit / gross_loss) if gross_loss else (999 if gross_profit > 0 else 0),
            "consecutive_losses": self.consecutive_losses(),
        }

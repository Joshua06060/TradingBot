from datetime import datetime, timezone, timedelta
import ccxt


class PaperBroker:
    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db
        exchange_cls = getattr(ccxt, cfg["exchange"]["name"])
        self.exchange = exchange_cls({"enableRateLimit": True})

    def open_trade(self, signal):
        equity = self.db.current_equity(self.cfg["risk"]["equity_start"])
        risk_amount = equity * self.cfg["risk"]["risk_per_trade_pct"] / 100
        risk_per_unit = abs(signal["entry"] - signal["stop_loss"])
        size = risk_amount / risk_per_unit if risk_per_unit > 0 else 0

        trade = {
            **signal,
            "size": size,
            "risk_amount": risk_amount,
            "status": "open",
            "opened_at": datetime.now(timezone.utc).isoformat(),
        }

        trade_id = self.db.insert_trade(trade)
        trade["id"] = trade_id
        return trade

    def manage_open_trades(self):
        open_trades = self.db.get_open_trades()
        for trade in open_trades:
            ticker = self.exchange.fetch_ticker(trade["symbol"])
            price = float(ticker["last"])
            close_reason = None

            if trade["side"] == "LONG":
                if price <= trade["stop_loss"]:
                    close_reason = "stop_loss"
                elif price >= trade["take_profit"]:
                    close_reason = "take_profit"
            else:
                if price >= trade["stop_loss"]:
                    close_reason = "stop_loss"
                elif price <= trade["take_profit"]:
                    close_reason = "take_profit"

            opened_at = datetime.fromisoformat(trade["opened_at"])
            max_age = timedelta(hours=self.cfg["risk"]["max_holding_hours"])
            if datetime.now(timezone.utc) - opened_at > max_age:
                close_reason = "max_holding_time"

            if close_reason:
                self.close_trade(trade, price, close_reason)

    def close_trade(self, trade, exit_price, reason):
        if trade["side"] == "LONG":
            pnl = (exit_price - trade["entry"]) * trade["size"]
        else:
            pnl = (trade["entry"] - exit_price) * trade["size"]

        self.db.close_trade(
            trade_id=trade["id"],
            exit_price=exit_price,
            pnl=pnl,
            reason=reason
        )

        print(
            f"Paper-Trade geschlossen: {trade['side']} {trade['symbol']} "
            f"Exit: {exit_price:.2f} PnL: {pnl:.2f} Grund: {reason}"
        )

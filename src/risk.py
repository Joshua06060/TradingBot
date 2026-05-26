from datetime import datetime, timezone


class RiskManager:
    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db

    def can_trade(self, symbol):
        if self.db.has_open_trade(symbol):
            return False

        if self.db.trades_today_count() >= self.cfg["risk"]["max_trades_per_day"]:
            return False

        if self.db.consecutive_losses() >= self.cfg["risk"]["pause_after_losses"]:
            return False

        equity_start = self.cfg["risk"]["equity_start"]
        daily_pnl = self.db.pnl_since("day")
        weekly_pnl = self.db.pnl_since("week")

        if daily_pnl <= -equity_start * self.cfg["risk"]["max_daily_loss_pct"] / 100:
            return False

        if weekly_pnl <= -equity_start * self.cfg["risk"]["max_weekly_loss_pct"] / 100:
            return False

        return True

    def validate_signal(self, signal):
        if signal["rr"] < self.cfg["strategy"]["min_rr"]:
            return False

        if signal["entry"] <= 0 or signal["stop_loss"] <= 0 or signal["take_profit"] <= 0:
            return False

        if signal["side"] == "LONG":
            return signal["stop_loss"] < signal["entry"] < signal["take_profit"]

        if signal["side"] == "SHORT":
            return signal["take_profit"] < signal["entry"] < signal["stop_loss"]

        return False

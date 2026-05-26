class Strategy:
    def __init__(self, cfg):
        self.cfg = cfg

    def generate_signal(self, symbol, entry_df, trend_df):
        if len(entry_df) < 210 or len(trend_df) < 210:
            return None

        e = entry_df.iloc[-1]
        p = entry_df.iloc[-2]
        t = trend_df.iloc[-1]

        price = float(e["close"])
        atr = float(e["atr"])
        if atr <= 0:
            return None

        trend_long = t["ema_50"] > t["ema_200"]
        trend_short = t["ema_50"] < t["ema_200"]

        volume_ok = e["volume"] > e["vol_sma_20"] * 1.15
        macd_long = e["macd_hist"] > p["macd_hist"] and e["macd_hist"] > 0
        macd_short = e["macd_hist"] < p["macd_hist"] and e["macd_hist"] < 0

        rsi_long = p["rsi"] < 40 and e["rsi"] > p["rsi"]
        rsi_short = p["rsi"] > 60 and e["rsi"] < p["rsi"]

        breakout_long = price > e["resistance_20"]
        breakout_short = price < e["support_20"]

        features = {
            "trend": 1 if trend_long or trend_short else 0,
            "rsi_reversal": 1 if rsi_long or rsi_short else 0,
            "macd": 1 if macd_long or macd_short else 0,
            "volume": 1 if volume_ok else 0,
            "breakout": 1 if breakout_long or breakout_short else 0,
        }

        long_score = sum([
            22 if trend_long else 0,
            16 if rsi_long else 0,
            16 if macd_long else 0,
            15 if volume_ok else 0,
            18 if breakout_long else 0,
        ])

        short_score = sum([
            22 if trend_short else 0,
            16 if rsi_short else 0,
            16 if macd_short else 0,
            15 if volume_ok else 0,
            18 if breakout_short else 0,
        ])

        side = None
        raw_conf = 0

        if long_score >= 68 and long_score >= short_score:
            side = "LONG"
            raw_conf = long_score
            stop_loss = price - atr * self.cfg["strategy"]["atr_stop_multiplier"]
            risk = price - stop_loss
            take_profit = price + risk * self.cfg["strategy"]["tp_rr"]
            reason = "1h-Trend positiv, RSI-Reversal, MACD/Volumen/Breakout bestätigt"
        elif short_score >= 68:
            side = "SHORT"
            raw_conf = short_score
            stop_loss = price + atr * self.cfg["strategy"]["atr_stop_multiplier"]
            risk = stop_loss - price
            take_profit = price - risk * self.cfg["strategy"]["tp_rr"]
            reason = "1h-Trend negativ, RSI-Reversal, MACD/Volumen/Breakdown bestätigt"
        else:
            return None

        rr = abs(take_profit - price) / abs(price - stop_loss)
        if rr < self.cfg["strategy"]["min_rr"]:
            return None

        return {
            "symbol": symbol,
            "side": side,
            "entry": price,
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "confidence": float(min(raw_conf, 95)),
            "rr": float(rr),
            "features": features,
            "reason": reason,
        }

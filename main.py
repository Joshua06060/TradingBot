import time
import yaml
from dotenv import load_dotenv
from datetime import datetime, timezone

from src.market_data import MarketData
from src.database import Database
from src.indicators import add_indicators
from src.strategy import Strategy
from src.paper_broker import PaperBroker
from src.risk import RiskManager
from src.ai_coach import AICoach
from src.notifier import Notifier


def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_snapshot(symbol, entry_df, trend_df, signal):
    e = entry_df.iloc[-1]
    t = trend_df.iloc[-1]
    trend = "Bullish" if t["ema_50"] > t["ema_200"] else "Bearish" if t["ema_50"] < t["ema_200"] else "Neutral"
    return {
        "symbol": symbol,
        "price": float(e["close"]),
        "trend": trend,
        "trend_ema_50": float(t["ema_50"]),
        "trend_ema_200": float(t["ema_200"]),
        "entry_ema_50": float(e["ema_50"]),
        "entry_ema_200": float(e["ema_200"]),
        "rsi": float(e["rsi"]),
        "macd_hist": float(e["macd_hist"]),
        "atr": float(e["atr"]),
        "volume": float(e["volume"]),
        "volume_sma": float(e["vol_sma_20"]),
        "resistance": float(e["resistance_20"]),
        "support": float(e["support_20"]),
        "signal_side": signal["side"] if signal else "WAIT",
        "confidence": float(signal["confidence"]) if signal else 0,
        "rr": float(signal["rr"]) if signal else 0,
        "reason": signal["reason"] if signal else "Kein starkes Setup. Bot wartet.",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    load_dotenv()
    cfg = load_config()
    db = Database("data/bot.db")
    market = MarketData(cfg)
    strategy = Strategy(cfg)
    ai = AICoach("data/ai_model.json")
    risk = RiskManager(cfg, db)
    broker = PaperBroker(cfg, db)
    notifier = Notifier(cfg)

    print("Trading AI Bot gestartet. Modus: PAPER-TRADING. Kein echtes Geld.")
    notifier.send("Trading AI Bot gestartet. Modus: PAPER-TRADING. Kein echtes Geld.")

    while True:
        try:
            broker.manage_open_trades()
            for symbol in cfg["symbols"]:
                entry_df = market.fetch_ohlcv(symbol, cfg["timeframes"]["entry"], cfg["loop"]["candles_limit"])
                trend_df = market.fetch_ohlcv(symbol, cfg["timeframes"]["trend"], cfg["loop"]["candles_limit"])
                entry_df = add_indicators(entry_df)
                trend_df = add_indicators(trend_df)
                signal = strategy.generate_signal(symbol, entry_df, trend_df)
                if signal is not None:
                    signal = ai.adjust_signal(signal)
                db.upsert_market_snapshot(build_snapshot(symbol, entry_df, trend_df, signal))
                print(f"Analyse: {symbol} | Signal: {signal['side'] if signal else 'WAIT'} | Confidence: {signal['confidence']:.1f}%" if signal else f"Analyse: {symbol} | Signal: WAIT")
                if signal is None: continue
                if signal["confidence"] < cfg["strategy"]["min_confidence"]: continue
                if not risk.can_trade(symbol): continue
                if not risk.validate_signal(signal): continue
                trade = broker.open_trade(signal)
                msg = (f"Paper-Trade eröffnet: {trade['side']} {trade['symbol']}\n"
                       f"Entry: {trade['entry']:.2f}\nSL: {trade['stop_loss']:.2f}\nTP: {trade['take_profit']:.2f}\n"
                       f"Confidence: {trade['confidence']:.1f}%\nGrund: {trade['reason']}")
                print(msg)
                notifier.send(msg)
            closed = db.get_recent_closed_unlearned()
            if closed:
                ai.learn_from_trades(closed)
                db.mark_trades_learned([t["id"] for t in closed])
                with open("logs/ai_report.txt", "w", encoding="utf-8") as f:
                    f.write(ai.generate_report(db))
        except KeyboardInterrupt:
            print("Bot gestoppt.")
            notifier.send("Trading AI Bot gestoppt.")
            break
        except Exception as e:
            print(f"Fehler: {e}")
            notifier.send(f"Bot-Fehler: {e}")
        time.sleep(cfg["loop"]["sleep_seconds"])


if __name__ == "__main__":
    main()

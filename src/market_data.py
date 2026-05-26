import ccxt
import pandas as pd


class MarketData:
    def __init__(self, cfg):
        exchange_name = cfg["exchange"]["name"]
        exchange_cls = getattr(ccxt, exchange_name)
        self.exchange = exchange_cls({
            "enableRateLimit": cfg["exchange"].get("rate_limit", True)
        })

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 250) -> pd.DataFrame:
        rows = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

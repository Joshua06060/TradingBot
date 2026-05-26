import json
import os
from collections import defaultdict


class AICoach:
    """
    Kontrollierte Lern-KI:
    - Kein echtes Trading
    - Keine magischen Vorhersagen
    - Lernt aus Paper-Trades, welche Signal-Features besser/schlechter waren
    - Passt Confidence leicht an
    """

    def __init__(self, model_path):
        self.model_path = model_path
        self.model = self._load()

    def _default(self):
        return {
            "weights": {
                "trend": 1.0,
                "rsi_reversal": 1.0,
                "macd": 1.0,
                "volume": 1.0,
                "breakout": 1.0,
            },
            "trade_count": 0,
            "notes": []
        }

    def _load(self):
        if not os.path.exists(self.model_path):
            return self._default()
        with open(self.model_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, "w", encoding="utf-8") as f:
            json.dump(self.model, f, indent=2)

    def adjust_signal(self, signal):
        weights = self.model["weights"]
        active = [k for k, v in signal["features"].items() if v == 1]

        if not active:
            return signal

        avg_weight = sum(weights.get(k, 1.0) for k in active) / len(active)
        adjustment = (avg_weight - 1.0) * 12
        signal["confidence"] = max(0, min(95, signal["confidence"] + adjustment))
        signal["reason"] += f" | KI-Gewichtung: {avg_weight:.2f}"
        return signal

    def learn_from_trades(self, trades):
        lr = 0.035

        for trade in trades:
            pnl = trade["pnl"] or 0
            reward = 1 if pnl > 0 else -1

            for feature, active in trade["features"].items():
                if not active:
                    continue

                old = self.model["weights"].get(feature, 1.0)
                new = old + lr * reward
                new = max(0.55, min(1.45, new))
                self.model["weights"][feature] = new

            self.model["trade_count"] += 1

        self._save()

    def generate_report(self, db):
        trades = [t for t in db.get_all_trades() if t["status"] == "closed"]
        lines = []
        lines.append("KI-Report")
        lines.append("=" * 30)
        lines.append(f"Gelernte Trades total: {self.model['trade_count']}")
        lines.append("")
        lines.append("Aktuelle Feature-Gewichte:")
        for k, v in self.model["weights"].items():
            lines.append(f"- {k}: {v:.2f}")

        if not trades:
            lines.append("")
            lines.append("Noch keine abgeschlossenen Trades vorhanden.")
            return "\n".join(lines)

        by_feature = defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": 0.0})

        for t in trades:
            for feature, active in t["features"].items():
                if active:
                    if t["pnl"] > 0:
                        by_feature[feature]["wins"] += 1
                    else:
                        by_feature[feature]["losses"] += 1
                    by_feature[feature]["pnl"] += t["pnl"] or 0

        lines.append("")
        lines.append("Feature-Auswertung:")
        for feature, stats in by_feature.items():
            total = stats["wins"] + stats["losses"]
            winrate = stats["wins"] / total * 100 if total else 0
            lines.append(f"- {feature}: Winrate {winrate:.1f}%, PnL {stats['pnl']:.2f}, Trades {total}")

        lines.append("")
        lines.append("Vorschläge:")
        for feature, stats in by_feature.items():
            total = stats["wins"] + stats["losses"]
            if total >= 5:
                winrate = stats["wins"] / total * 100
                if winrate < 40:
                    lines.append(f"- {feature} war schwach. Dieses Signal strenger filtern.")
                elif winrate > 60:
                    lines.append(f"- {feature} war stark. Dieses Signal weiter bevorzugen.")

        return "\n".join(lines)

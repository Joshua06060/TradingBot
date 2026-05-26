from src.database import Database
from src.ai_coach import AICoach

db = Database("data/bot.db")
ai = AICoach("data/ai_model.json")

trades = db.get_all_trades()
closed = [t for t in trades if t["status"] == "closed"]

print("=== Trading AI Bot Report ===")
print(f"Alle Trades: {len(trades)}")
print(f"Geschlossene Trades: {len(closed)}")

if closed:
    wins = [t for t in closed if t["pnl"] and t["pnl"] > 0]
    losses = [t for t in closed if t["pnl"] and t["pnl"] <= 0]
    total_pnl = sum(t["pnl"] or 0 for t in closed)
    gross_profit = sum(t["pnl"] for t in wins)
    gross_loss = abs(sum(t["pnl"] for t in losses))
    winrate = len(wins) / len(closed) * 100
    profit_factor = gross_profit / gross_loss if gross_loss else 999

    print(f"Winrate: {winrate:.2f}%")
    print(f"Total PnL: {total_pnl:.2f}")
    print(f"Profit Factor: {profit_factor:.2f}")
    print(f"Gewinner: {len(wins)}")
    print(f"Verlierer: {len(losses)}")

print("\n=== KI-Auswertung ===")
print(ai.generate_report(db))

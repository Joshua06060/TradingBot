# Trading AI Bot – Paper-Trading Signal Bot

Ein Daytrading-Bot für BTC/ETH mit:
- Marktanalyse über CCXT
- EMA / RSI / MACD / ATR / Volumen
- 15m Haupt-Timeframe und 1h Trendfilter
- Paper-Trading, kein echtes Geld
- SQLite Trade-Journal
- integrierter Lern-KI, die abgeschlossene Trades auswertet
- optionalen Telegram-Signalen
- Sicherheitslimits: Tagesverlust, Wochenverlust, Verlustserie, max. Trades pro Tag

Wichtig: Dieser Bot ist kein Gelddrucker. Er garantiert keine Gewinne. Er ist bewusst zuerst als Paper-Trading-System gebaut.

---

## 1. Installation

### Voraussetzungen
- Python 3.10 oder neuer
- VS Code
- Internetverbindung

### Projekt entpacken
ZIP entpacken, dann im Terminal in den Ordner wechseln:

```bash
cd trading_ai_bot
```

### Virtuelle Umgebung erstellen

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Pakete installieren

```bash
pip install -r requirements.txt
```

---

## 2. Starten

```bash
python main.py
```

Der Bot:
1. lädt BTC/USDT und ETH/USDT Daten
2. analysiert 15m und 1h Chart
3. erstellt Signale
4. eröffnet Paper-Trades
5. verwaltet SL/TP
6. speichert alles in `data/bot.db`
7. lässt die KI nach abgeschlossenen Trades lernen

---

## 3. Konfiguration

In `config.yaml` kannst du einstellen:

```yaml
symbols:
  - BTC/USDT
  - ETH/USDT

timeframes:
  entry: 15m
  trend: 1h

risk:
  equity_start: 1000
  risk_per_trade_pct: 0.75
  max_trades_per_day: 4
  max_daily_loss_pct: 2
  max_weekly_loss_pct: 5
  pause_after_losses: 3
```

Für Daytrading empfehle ich:
- 15m Entry
- 1h Trendfilter
- max. 3 bis 5 Trades pro Tag
- 0.5 bis 1 % Risiko pro Trade
- keine Meme-Coins am Anfang

---

## 4. Telegram optional aktivieren

1. Telegram öffnen
2. `@BotFather` suchen
3. `/newbot`
4. Token kopieren
5. `.env.example` zu `.env` kopieren
6. Werte eintragen:

```env
TELEGRAM_BOT_TOKEN=dein_token
TELEGRAM_CHAT_ID=deine_chat_id
```

Dann in `config.yaml`:

```yaml
telegram:
  enabled: true
```

Ohne Telegram läuft der Bot normal in der Konsole.

---

## 5. KI-Lernsystem

Die KI ist absichtlich sicher gebaut.

Sie darf:
- abgeschlossene Trades analysieren
- Feature-Gewichtungen anpassen
- Confidence-Score verbessern
- schwache Marktbedingungen erkennen
- Vorschläge in `logs/ai_report.txt` schreiben

Sie darf nicht:
- echtes Geld handeln
- API-Keys nutzen
- eigenständig gefährliche Strategien live aktivieren

Das Lernmodell liegt in:

```text
data/ai_model.json
```

---

## 6. Backtest / Auswertung

Aktuell läuft der Bot als Live-Paper-Bot auf aktuellen Marktdaten.

Nach einiger Laufzeit kannst du die Daten anschauen:

```bash
python report.py
```

Der Report zeigt:
- Anzahl Trades
- Winrate
- Gewinn/Verlust
- Profit Factor
- durchschnittlicher Gewinn
- durchschnittlicher Verlust
- KI-Vorschläge

---

## 7. Späterer Live-Trading-Ausbau

Erst wenn Paper-Trading stabil ist:

- API-Key ohne Withdrawal-Rechte
- zuerst nur kleine Beträge
- Live-Modul getrennt aktivieren
- tägliches Verlustlimit hart einbauen
- Notfall-Stopp
- keine Hebel am Anfang

Im aktuellen Projekt ist echtes Trading absichtlich nicht eingebaut.


---

## Live-Dashboard starten

Dieses Update enthält ein lokales Web-Dashboard.

Terminal 1, Bot starten:

```bash
python main.py
```

Terminal 2, Dashboard starten:

```bash
python dashboard.py
```

Dann im Browser öffnen:

```text
http://127.0.0.1:8000
```

Das Dashboard zeigt Live-Marktanalyse, Preis, Trend, RSI, MACD, ATR, Confidence, offene Paper-Trades, letzte Trades, PnL, Winrate und KI-Gewichte.

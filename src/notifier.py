import os
import asyncio
from telegram import Bot


class Notifier:
    def __init__(self, cfg):
        self.enabled = cfg.get("telegram", {}).get("enabled", False)
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def send(self, message):
        if not self.enabled:
            return
        if not self.token or not self.chat_id:
            print("Telegram ist aktiviert, aber Token oder Chat ID fehlt.")
            return

        try:
            asyncio.run(self._send_async(message))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._send_async(message))
        except Exception as e:
            print(f"Telegram-Fehler: {e}")

    async def _send_async(self, message):
        bot = Bot(token=self.token)
        await bot.send_message(chat_id=self.chat_id, text=message)

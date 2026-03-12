import asyncio
import re
import json
import requests
import sqlite3
import os
from telethon import TelegramClient, errors

# -----------------------------
# Environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
SOURCE_CHAT_ID = int(os.getenv("SOURCE_CHAT_ID"))
TRADERSPOST_WEBHOOK = os.getenv("TRADERSPOST_WEBHOOK")

# Tradovate ticker mapping
TICKER_MAP = {
    "NQ": "MNQ1!",
    "ES": "MES1!"
}
DEFAULT_QUANTITY = 1

# -----------------------------
# Save trades to SQLite
def save_trade_to_db(trade):
    conn = sqlite3.connect("trades.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            ticker TEXT, action TEXT, type TEXT, quantity INTEGER, price REAL, timestamp TEXT
        )
    """)
    c.execute("""
        INSERT INTO trades (ticker, action, type, quantity, price, timestamp) VALUES (?,?,?,?,?,datetime('now'))
    """, (trade["ticker"], trade["action"], trade["type"], trade["quantity"], trade["price"]))
    conn.commit()
    conn.close()

# -----------------------------
class TelegramForwarder:
    def __init__(self):
        self.client = TelegramClient(SESSION_STRING, API_ID, API_HASH)
        self.sent_trades = set()

    def parse_trade_signal(self, text):
        if not text:
            return []

        trades = []

        entry_pattern = r"ENTRY:\s*(Bought|Sold)\s+(NQ|ES).*price\s*=\s*([\d\.]+)"
        exit_pattern = r"EXIT:\s*(Sold|Bought to Cover|Bought)\s+(NQ|ES).*price\s*=\s*([\d\.]+)"

        # ENTRY
        for side, symbol, price in re.findall(entry_pattern, text, re.IGNORECASE):
            action = "BUY" if side.lower() == "bought" else "SELL"
            ticker = TICKER_MAP.get(symbol.upper(), symbol.upper())
            trades.append({
                "ticker": ticker,
                "action": action,
                "orderType": "market",
                "type": "ENTRY",
                "quantity": DEFAULT_QUANTITY,
                "price": float(price)
            })

        # EXIT
        for side, symbol, price in re.findall(exit_pattern, text, re.IGNORECASE):
            ticker = TICKER_MAP.get(symbol.upper(), symbol.upper())
            trades.append({
                "ticker": ticker,
                "action": "EXIT",
                "orderType": "market",
                "type": "EXIT",
                "quantity": DEFAULT_QUANTITY,
                "price": float(price)
            })

        return trades

    def send_to_traderspost(self, trade):
        key = (trade["ticker"], trade["action"], trade["type"])
        if key in self.sent_trades:
            print("Duplicate trade skipped:", trade)
            return

        try:
            response = requests.post(
                TRADERSPOST_WEBHOOK,
                headers={"Content-Type": "application/json"},
                json=trade,
                timeout=10
            )
            self.sent_trades.add(key)
            print("\nSent Trade:")
            print(json.dumps(trade, indent=2))
            print("Response:", response.status_code)
        except Exception as e:
            print("Webhook Error:", e)

        # Save to DB
        save_trade_to_db(trade)

    async def listen_for_signals(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            print("Session not authorized! Please create SESSION_STRING first.")
            return

        last_message = await self.client.get_messages(SOURCE_CHAT_ID, limit=1)
        last_id = last_message[0].id if last_message else 0
        print("\nListening for signals...\n")

        while True:
            messages = await self.client.get_messages(SOURCE_CHAT_ID, limit=1)
            for msg in messages:
                if msg.id <= last_id:
                    continue
                print("\nNew Message:")
                print(msg.text or "")
                trades = self.parse_trade_signal(msg.text)
                for trade in trades:
                    self.send_to_traderspost(trade)
                last_id = msg.id
            await asyncio.sleep(3)

# -----------------------------
if __name__ == "__main__":
    forwarder = TelegramForwarder()
    asyncio.run(forwarder.listen_for_signals())
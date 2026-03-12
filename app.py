import os
import threading
import sqlite3
from flask import Flask, render_template
from bot import run_bot  # your Telegram bot main function

app = Flask(__name__)

# -------------------------
# Initialize Database
def init_db():
    conn = sqlite3.connect("trades.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            ticker TEXT,
            action TEXT,
            type TEXT,
            quantity INTEGER,
            price REAL,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------------
# Helper to save trade to DB
def save_trade_to_db(trade):
    conn = sqlite3.connect("trades.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO trades (ticker, action, type, quantity, price, timestamp)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (trade["ticker"], trade["action"], trade["type"], trade["quantity"], trade["price"]))
    conn.commit()
    conn.close()

# -------------------------
# Flask route for dashboard
@app.route("/")
def dashboard():
    conn = sqlite3.connect("trades.db")
    c = conn.cursor()
    c.execute("""
        SELECT ticker, action, type, quantity, price, timestamp
        FROM trades
        ORDER BY timestamp DESC
    """)
    trades = c.fetchall()
    conn.close()
    return render_template("dashboard.html", trades=trades)

# -------------------------
# Start Telegram bot in background
def start_bot():
    threading.Thread(target=run_bot, daemon=True).start()

start_bot()

# -------------------------
# Run Flask app on Railway port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

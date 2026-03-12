from flask import Flask, render_template
import sqlite3
from datetime import date
import os

app = Flask(__name__)

DB_PATH = "trades.db"


def init_db():
    """
    Create trades table if it doesn't exist
    """
    conn = sqlite3.connect(DB_PATH)
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


@app.route("/")
def dashboard():

    # Ensure database table exists
    init_db()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    today = date.today().isoformat()

    c.execute(
        "SELECT ticker, action, type, quantity, price, timestamp FROM trades WHERE date(timestamp)=?",
        (today,)
    )

    trades = c.fetchall()

    conn.close()

    # Calculate daily P&L
    pnl = 0
    for trade in trades:
        ticker = trade[0]
        action = trade[1]
        trade_type = trade[2]
        quantity = trade[3]
        price = trade[4]

        if action == "SELL":
            pnl += price * quantity
        else:
            pnl -= price * quantity

    return render_template("dashboard.html", trades=trades, pnl=pnl)


@app.route("/all")
def all_trades():
    """
    Show all trades in database
    """
    init_db()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "SELECT ticker, action, type, quantity, price, timestamp FROM trades ORDER BY timestamp DESC"
    )

    trades = c.fetchall()
    conn.close()

    return render_template("dashboard.html", trades=trades, pnl="N/A")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    # Initialize DB when app starts
    init_db()

    app.run(host="0.0.0.0", port=port)

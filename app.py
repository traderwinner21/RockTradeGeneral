from flask import Flask, render_template
import sqlite3
from datetime import date

app = Flask(__name__)

DB_PATH = "trades.db"

@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Example: get today's trades
    today = date.today().isoformat()
    c.execute("SELECT ticker, action, type, quantity, price, timestamp FROM trades WHERE date(timestamp)=?", (today,))
    trades = c.fetchall()

    # Calculate daily P&L
    pnl = 0
    for t in trades:
        action, quantity, price = t[1], t[3], float(t[4])
        pnl += price * quantity if action == "SELL" else -price * quantity

    conn.close()
    return render_template("dashboard.html", trades=trades, pnl=pnl)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
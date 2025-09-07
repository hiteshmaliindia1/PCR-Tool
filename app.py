from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from fetcher import refresh_all, cache_path
from symbols import symbols
import json, os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
INDEX_SYMBOLS = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"}

def now_ist():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))

def read_card(symbol, label):
    path = cache_path(symbol)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"symbol": symbol, "label": label, "error": "No data"}

@app.route("/")
def dashboard():
    cards = [read_card(code, label) for code, label in symbols.items()]
    indices = [c for c in cards if c["symbol"] in INDEX_SYMBOLS]
    stocks = [c for c in cards if c["symbol"] not in INDEX_SYMBOLS]

    # Sort by PCR descending
    indices.sort(key=lambda x: (x["pcr"] is None, x["pcr"]), reverse=True)
    stocks.sort(key=lambda x: (x["pcr"] is None, x["pcr"]), reverse=True)

    return render_template("index.html",
        indices=indices,
        stocks=stocks,
        last_updated=now_ist().strftime("%H:%M:%S"),
        next_fetch=(now_ist() + timedelta(minutes=15)).strftime("%H:%M:%S"),
        auto_refresh_sec=60
    )

def refresh_job():
    print("[REFRESH] Fetching fresh data...")
    refresh_all()

if __name__ == "__main__":
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(refresh_job, "interval", minutes=1, next_run_time=datetime.now() + timedelta(seconds=1))
    scheduler.start()

    refresh_job()  # Immediate fetch on startup
    app.run(host="127.0.0.1", port=8000, debug=True)
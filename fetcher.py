import os, json
from datetime import datetime, timezone, timedelta
from symbols import symbols
from nsepython import nse_optionchain_scrapper  # one function for all

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_path(symbol):
    return os.path.join(CACHE_DIR, f"{symbol}.json")

def now_ist():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))

def compute_totals(rows):
    def i(x): 
        try: return int(x)
        except: return 0
    call_oi = sum(i(r.get("CE", {}).get("openInterest")) for r in rows)
    put_oi  = sum(i(r.get("PE", {}).get("openInterest")) for r in rows)
    call_chg = sum(i(r.get("CE", {}).get("changeinOpenInterest")) for r in rows)
    put_chg  = sum(i(r.get("PE", {}).get("changeinOpenInterest")) for r in rows)
    pcr = round(put_oi / call_oi, 3) if call_oi else None
    return call_oi, put_oi, call_chg, put_chg, pcr

def fetch_symbol(symbol, label):
    try:
        data = nse_optionchain_scrapper(symbol)  # works for both indices & equities
        rows = data.get("filtered", {}).get("data") or data.get("records", {}).get("data", [])
        call_oi, put_oi, call_chg, put_chg, pcr = compute_totals(rows)
        card = {
            "label": label, "symbol": symbol,
            "underlying": data["records"].get("underlyingValue"),
            "expiry": (data["records"].get("expiryDates") or [None])[0],
            "callOI": call_oi, "putOI": put_oi,
            "callChgOI": call_chg, "putChgOI": put_chg,
            "pcr": pcr, "error": None,
            "updatedAt": now_ist().strftime("%H:%M:%S")
        }
        with open(cache_path(symbol), "w") as f:
            json.dump(card, f, indent=2)
        print(f"[OK] {symbol}")
    except Exception as e:
        print(f"[FAIL] {symbol}: {e}")
        with open(cache_path(symbol), "w") as f:
            json.dump({
                "label": label, "symbol": symbol,
                "underlying": None, "expiry": None,
                "callOI": None, "putOI": None,
                "callChgOI": None, "putChgOI": None,
                "pcr": None, "error": str(e),
                "updatedAt": now_ist().strftime("%H:%M:%S")
            }, f, indent=2)

def refresh_all():
    for sym, lbl in symbols.items():
        fetch_symbol(sym, lbl)
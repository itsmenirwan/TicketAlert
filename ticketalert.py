import requests
import time
import threading
import os
from bs4 import BeautifulSoup
from datetime import datetime
from flask import Flask

# --- FLASK HEARTBEAT FOR RENDER/NORTHFLANK ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Ticket Bot is Running!", 200

# --- CONFIGURATION ---
# Using os.environ.get is recommended once you set these in Render Dashboard
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8751636091:AAExdFpUPDhlAhesRnHUgSvsrtcj-Kg49lk")
CHAT_ID = os.environ.get("CHAT_ID", "-1003786313599")
CHECK_INTERVAL = 1800        
HEARTBEAT_INTERVAL = 1800  
SCRAPER_API_KEY = "e0a916714723875f6dd476f9baa71af9"

URLS = ["https://in.bookmyshow.com/sports/icc-men-s-t20-world-cup-2026-final/ET00476187"]
KEYWORDS = ["book now", "buy tickets", "add to cart", "proceed", "select seats"]

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
        if res.status_code == 200:
            log("Telegram notification sent ✅")
        else:
            log(f"Telegram failed ❌: {res.text}")
    except Exception as e:
        log(f"Telegram error: {e}")

def check_tickets():
    for url in URLS:
        try:
            scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true"
            res = requests.get(scraper_url, timeout=30)
            soup = BeautifulSoup(res.text, "html.parser")
            page_text = soup.get_text().lower()
            for kw in KEYWORDS:
                if kw in page_text:
                    return True, url, kw
        except Exception as e:
            log(f"Error checking {url}: {e}")
    return False, None, None

# --- THE MAIN MONITORING LOOP ---
def run_monitoring_loop():
    log("🚀 Monitoring thread started...")
    # Initial startup message so you know it's working
    send_telegram("✅ <b>Ticket Bot Started!</b>\nMonitoring ICC T20 World Cup Final...")
    
    alerted = False
    check_count = 0
    last_heartbeat = time.time()

    while True:
        try:
            check_count += 1
            log(f"Performing check #{check_count}")
            found, source_url, keyword = check_tickets()

            if found and not alerted:
                send_telegram(f"🚨 <b>TICKETS LIVE!</b>\nDetected: {keyword}\nURL: {source_url}")
                alerted = True

            if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
                send_telegram(f"💓 Bot Active. Checks: {check_count}")
                last_heartbeat = time.time()

        except Exception as e:
            log(f"Loop error: {e}")
        
        time.sleep(CHECK_INTERVAL)

# --- START BOTH SERVICES ---

# 1. Start the monitoring thread IMMEDIATELY (Gunicorn needs this here)
monitoring_thread = threading.Thread(target=run_monitoring_loop, daemon=True)
monitoring_thread.start()

# 2. This block only runs if you run 'python ticketalert.py' locally
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

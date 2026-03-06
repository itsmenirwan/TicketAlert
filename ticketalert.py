import requests
import time
import threading
import os
from bs4 import BeautifulSoup
from datetime import datetime
from flask import Flask

# --- FLASK HEARTBEAT FOR RENDER ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Ticket Bot is Running!", 200

# --- CONFIGURATION ---
# Intervals set to 600 seconds (10 minutes)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8751636091:AAExdFpUPDhlAhesRnHUgSvsrtcj-Kg49lk")
CHAT_ID = os.environ.get("CHAT_ID", "-1003786313599")
CHECK_INTERVAL = 600        
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
    send_telegram("✅ <b>Ticket Bot Started!</b>\nI will check and provide a status update every 10 minutes.")
    
    alerted = False
    check_count = 0

    while True:
        try:
            check_count += 1
            log(f"Performing check #{check_count}")
            found, source_url, keyword = check_tickets()

            # 1. ALERT IF TICKETS ARE FOUND
            if found:
                send_telegram(f"🚨 <b>TICKETS LIVE!</b>\nDetected: <i>{keyword}</i>\nURL: {source_url}")
                alerted = True
            
            # 2. 10-MINUTE STATUS LOG
            status_emoji = "✅ LIVE" if found else "❌ Not Live"
            status_msg = (
                f"📊 <b>Check #{check_count} Status</b>\n"
                f"Tickets: {status_emoji}\n"
                f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}\n"
                f"🎫 Found yet: {'YES' if alerted else 'No'}"
            )
            send_telegram(status_msg)

        except Exception as e:
            log(f"Loop error: {e}")
            send_telegram(f"⚠️ <b>Bot Error:</b> Logic crashed but loop is restarting...")
        
        # Wait 10 minutes (600 seconds)
        time.sleep(CHECK_INTERVAL)

# --- START BOTH SERVICES ---

# Start the monitoring thread immediately for Gunicorn
monitoring_thread = threading.Thread(target=run_monitoring_loop, daemon=True)
monitoring_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

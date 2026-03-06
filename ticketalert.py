import requests
import time
import threading
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import Flask

# --- FLASK HEARTBEAT FOR RENDER ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Ticket Bot is Running!", 200

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8751636091:AAExdFpUPDhlAhesRnHUgSvsrtcj-Kg49lk")
CHAT_ID = os.environ.get("CHAT_ID", "-1003786313599")

# Updated Intervals
CHECK_INTERVAL = 60         # Check every 1 minute
STATUS_INTERVAL = 600       # Send status update every 10 minutes

SCRAPER_API_KEY = "e0a916714723875f6dd476f9baa71af9"
URLS = ["https://in.bookmyshow.com/sports/icc-men-s-t20-world-cup-2026-final/ET00476187"]
KEYWORDS = ["book now", "buy tickets", "add to cart", "proceed", "select seats"]

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
        return res.status_code == 200
    except Exception as e:
        log(f"Telegram error: {e}")
        return False

def check_tickets():
    for url in URLS:
        try:
            # Note: Using ScraperAPI with render=true for heavy sites like BookMyShow
            scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true"
            res = requests.get(scraper_url, timeout=40)
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
    send_telegram("✅ <b>Bot Started!</b>\nChecking every 1 min. Status update every 10 mins.")
    
    last_status_time = datetime.now()
    check_count = 0
    alert_triggered = False

    while True:
        try:
            check_count += 1
            found, source_url, keyword = check_tickets()

            # 1. IMMEDIATE ALERT (If tickets found)
            if found:
                log(f"🚨 TICKETS FOUND via {keyword}!")
                send_telegram(f"🚨 <b>TICKETS LIVE!</b>\nDetected: <i>{keyword}</i>\nURL: {source_url}")
                alert_triggered = True
            else:
                log(f"Check #{check_count}: No tickets yet.")

            # 2. PERIODIC STATUS UPDATE (Every 10 minutes)
            time_since_last_status = (datetime.now() - last_status_time).total_seconds()
            
            if time_since_last_status >= STATUS_INTERVAL:
                status_emoji = "🔥 LIVE" if found else "😴 Waiting"
                status_msg = (
                    f"📊 <b>10-Min Status Report</b>\n"
                    f"Checks performed: {check_count}\n"
                    f"Current Status: {status_emoji}\n"
                    f"Last Check Time: {datetime.now().strftime('%H:%M:%S')}"
                )
                send_telegram(status_msg)
                # Reset status timer
                last_status_time = datetime.now()

        except Exception as e:
            log(f"Loop error: {e}")
        
        # Always wait 60 seconds before next check
        time.sleep(CHECK_INTERVAL)

# --- START BOTH SERVICES ---
monitoring_thread = threading.Thread(target=run_monitoring_loop, daemon=True)
monitoring_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # Use threaded=True to ensure Flask doesn't block the script
    app.run(host='0.0.0.0', port=port)

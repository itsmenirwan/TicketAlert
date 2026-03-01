

import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = "8217134371:AAG4wKoLY0Y5pnfgeSJuEzz_TyUJHDItNTc"
CHAT_ID = "1153831634"
CHECK_INTERVAL = 60        # Check every 60 seconds
HEARTBEAT_INTERVAL = 1800  # Telegram update every 30 mins

URLS = [
    "https://in.bookmyshow.com/sports/icc-men-s-t20-world-cup-2026-semi-final-2/ET00474271",
]

KEYWORDS = ["book now", "buy tickets", "add to cart", "proceed", "select seats"]

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
        if res.status_code == 200:
            log("Telegram sent ✅")
        else:
            log(f"Telegram failed: {res.text}")
    except Exception as e:
        log(f"Telegram error: {e}")

SCRAPER_API_KEY = "e0a916714723875f6dd476f9baa71af9"

def check_tickets():
    for url in URLS:
        try:
            scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            res = requests.get(scraper_url, timeout=30, headers=headers)
            soup = BeautifulSoup(res.text, "html.parser")
            page_text = soup.get_text().lower()
            log(f"Page snippet: {page_text[:300]}")
            for kw in KEYWORDS:
                if kw in page_text:
                    return True, url, kw
        except Exception as e:
            log(f"Error checking {url}: {e}")
            send_telegram(f"⚠️ Error: {e}")
    return False, None, None

# ---- STARTUP TEST ----
log("🚀 Bot starting...")
send_telegram("✅ <b>Ticket Alert Bot Started!</b>\n\n🔍 Monitoring:\n• Semi Final 1\n• Semi Final 2\n\n⏱ Checking every 60 seconds\n💓 Heartbeat every 30 mins\n\nYou'll be notified the moment tickets go live! 🏏")

# ---- MANUAL KEYWORD TEST ----
log("Running keyword test...")
found, url, kw = check_tickets()
if found:
    log(f"⚠️ Keyword '{kw}' already found at {url} — tickets might already be live!")
    send_telegram(f"⚠️ <b>Keyword already detected on startup!</b>\nKeyword: {kw}\nURL: {url}\n\nTickets may already be live — check now!")
else:
    log("No keywords found yet. Normal monitoring starting...")

alerted = False
check_count = 0
last_heartbeat = time.time()
errors_in_row = 0

while True:
    try:
        check_count += 1
        log(f"Check #{check_count}")

        found, source_url, keyword = check_tickets()

        if found and not alerted:
            send_telegram(
                f"🚨🚨 <b>TICKETS ARE LIVE!</b> 🚨🚨\n\n"
                f"🏏 ICC T20 WC Semi Final Tickets OPEN!\n"
                f"🔍 Detected: <i>{keyword}</i>\n\n"
                f"👉 <b>BOOK NOW:</b>\n{source_url}"
            )
            # Send 3 times so you don't miss it!
            time.sleep(5)
            send_telegram(f"🚨 REMINDER: Tickets are LIVE!\n👉 {source_url}")
            time.sleep(5)
            send_telegram(f"🚨 FINAL REMINDER: Book now!\n👉 {source_url}")
            alerted = True
            errors_in_row = 0

        # Heartbeat every 30 mins
        if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
            send_telegram(f"💓 <b>Bot Heartbeat</b>\n\n✅ Still running!\n📊 Checks done: {check_count}\n🕐 Time: {datetime.now().strftime('%H:%M:%S')}\n🎫 Tickets found: {'YES ✅' if alerted else 'Not yet ❌'}")
            last_heartbeat = time.time()

    except Exception as e:
        errors_in_row += 1
        log(f"CRASH: {e}")
        send_telegram(f"🔴 <b>Bot Error #{errors_in_row}!</b>\n{e}\n\nRestarting...")
        if errors_in_row >= 5:
            send_telegram("🔴 <b>Too many errors! Bot may have stopped. Please restart Colab!</b>")
        time.sleep(30)


    time.sleep(CHECK_INTERVAL)

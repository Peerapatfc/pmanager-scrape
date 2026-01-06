import os
import requests
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from datetime import datetime
from datetime import datetime, timedelta
import re

# ... (imports remain)

def get_sheet_data(sheet_name):
    # ... (unchanged)
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key("1F8FWV9w1gNAGbGDd6RG929dx2jAcM-N6p2ve9fOwSfU")
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return data
    except Exception as e:
        print(f"Error reading {sheet_name}: {e}")
        return []

def send_telegram_message(message):
    """Send message to Telegram with retry logic"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Error: Telegram credentials not found in env.")
        return
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Message sent to Telegram (Markdown)!")
        else:
            print(f"Failed to send Markdown: {response.text}")
            print("Retrying as Plain Text...")
            del payload["parse_mode"]
            # Plain text fallback
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print("Message sent to Telegram (Plain Text)!")
            else:
                print(f"Failed to send Plain Text: {response.text}")
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def parse_money(money_str):
    # ... (unchanged)
    if isinstance(money_str, (int, float)):
        return int(money_str)
    try:
        clean = str(money_str).split("baht")[0].strip()
        clean = clean.replace(".", "").replace(",", "")
        return int(clean)
    except:
        return 0

def parse_deadline(deadline_str):
    """
    Parse 'Today at 10:19' (UTC) -> Convert to Thailand Time (UTC+7).
    """
    if not deadline_str or not isinstance(deadline_str, str):
        return None
    
    txt = deadline_str.lower().strip()
    
    # Regex to find HH:MM
    match = re.search(r'(\d{1,2}):(\d{2})', txt)
    if not match:
        return None
        
    hour = int(match.group(1))
    minute = int(match.group(2))
    
    # Base is UTC
    utc_now = datetime.utcnow()
    
    if "today" in txt:
        utc_deadline = utc_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif "tomorrow" in txt:
        utc_deadline = (utc_now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    else:
        return None
    
    # Convert to Thailand Time (UTC+7)
    th_deadline = utc_deadline + timedelta(hours=7)
    return th_deadline

def generate_message(candidates, funds_str, current_time_th):
    """Generate Telegram message"""
    time_str = current_time_th.strftime('%H:%M')
    
    if not candidates:
        return f"📉 *Market Update* ({time_str})\n\nNo profitable flips found within budget right now."
        
    msg = f"🚀 *Top 15 Day Trade Signals (Algorithm)* 🚀\n\n"
    msg += f"💰 Budget: {funds_str}\n"
    msg += f"⏰ Time: {time_str}\n\n"
    
    for i, p in enumerate(candidates[:15], 1):
        name = p.get('name', 'N/A')
        pid = p.get('id', '')
        buy = f"{int(p.get('buy_price', 0)):,}"
        sell = f"{int(p.get('forecast_sell', 0)):,}"
        profit = p.get('forecast_sell', 0)
        deadline = p.get('deadline', 'N/A')
        
        # Emoji based on profit
        profit_icon = "🤑" if profit > 1000000 else "💵"
        
        entry = (
            f"{i}. *{name}*\n"
            f"   📉 Buy: {buy} | {profit_icon} Profit: {sell}\n"
            f"   ⏱️ Ends: {deadline}\n"
            f"   🔗 [Link](https://www.pmanager.org/comprar_jog_lista.asp?jg_id={pid})\n"
        )
        msg += entry + "\n"
        
    msg += "⚠️ *Auto-generated based on (Est. Value/2 * 0.8) - Buy Price*"
    return msg

def main():
    load_dotenv()
    
    # Set Reference Time (Thailand Time: UTC+7)
    now_th = datetime.utcnow() + timedelta(hours=7)
    
    # 1. Gather Data
    transfer_data = get_sheet_data("Transfer Info")
    if not transfer_data:
        print("No transfer data found.")
        return

    # 2. Get Team Funds
    team_info = get_sheet_data("Team Info")
    current_funds = 0
    funds_str = "0"
    
    if team_info and len(team_info) >= 1:
         row = team_info[0]
         funds_raw = row.get("Available Funds", "0")
         funds_str = str(funds_raw)
         current_funds = parse_money(funds_raw)

    print(f"Current Funds: {current_funds:,}")
    print(f"Current Time (TH): {now_th}")

    # 3. Filter Candidates
    candidates = []
    
    for p in transfer_data:
        try:
            buy_price = int(p.get("buy_price", 0))
            forecast_profit = int(p.get("forecast_sell", 0))
            deadline_str = str(p.get("deadline", ""))
            
            # Criteria 1: Affordable
            if buy_price > current_funds:
                continue
                
            # Criteria 2: Profitable
            if forecast_profit <= 0:
                continue
                
            # Criteria 3: Time Check (Future + Within 12 Hours)
            deadline_dt = parse_deadline(deadline_str)
            
            if not deadline_dt:
                continue
                
            # Calculate time difference
            diff = deadline_dt - now_th
            total_seconds = diff.total_seconds()
            
            # Keep if:
            # a) It is in the future (> 0)
            # b) It is within 12 hours (< 12*3600)
            if 0 < total_seconds < (12 * 3600):
                # Update deadline string to display nice Thailand Time in message
                p["deadline"] = deadline_dt.strftime("%d/%m %H:%M")
                candidates.append(p)
                
        except Exception as e:
            # print(f"Skipping row error: {e}")
            continue

    # 4. Sort by Profit (Descending)
    candidates.sort(key=lambda x: int(x.get("forecast_sell", 0)), reverse=True)
    
    print(f"Found {len(candidates)} valid trade targets (Future < 12h).")

    # 5. Send Message
    msg = generate_message(candidates, funds_str, now_th)
    print("Sending Telegram notification...")
    send_telegram_message(msg)

if __name__ == "__main__":
    main()

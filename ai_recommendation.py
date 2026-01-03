import os
import requests
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from datetime import datetime

def get_sheet_data(sheet_name):
    """Fetch all rows from a specific sheet"""
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key("1F8FWV9w1gNAGbGDd6RG929dx2jAcM-N6p2ve9fOwSfU")
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Get all values
        data = worksheet.get_all_records()
        return data
    except Exception as e:
        print(f"Error reading {sheet_name}: {e}")
        return []

def parse_money(money_str):
    """Parse money string like '9.136.350 baht' to int"""
    if isinstance(money_str, (int, float)):
        return int(money_str)
    try:
        clean = str(money_str).split("baht")[0].strip()
        clean = clean.replace(".", "").replace(",", "")
        return int(clean)
    except:
        return 0

def is_deadline_soon(deadline_str):
    """Check if deadline is 'Today' or within ~12 hours"""
    # Formats: "Today at 12:19", "2 Days", "Tomorrow at..."
    if not deadline_str or not isinstance(deadline_str, str):
        return False
    
    dl = deadline_str.lower()
    if "today" in dl:
        return True
    # If "12:30" (time only) usually means today in some contexts, but sticking to text
    return False

def generate_message(candidates, funds_str):
    """Generate Telegram message"""
    if not candidates:
        return "📉 *Market Update*\n\nNo profitable flips found within budget right now."
        
    msg = f"🚀 *Top 15 Day Trade Signals (Algorithm)* 🚀\n\n"
    msg += f"💰 Budget: {funds_str}\n"
    msg += f"⏰ Time: {datetime.now().strftime('%H:%M')}\n\n"
    
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

    # 3. Filter Candidates
    candidates = []
    for p in transfer_data:
        try:
            buy_price = int(p.get("buy_price", 0))
            forecast_profit = int(p.get("forecast_sell", 0))
            deadline = str(p.get("deadline", ""))
            
            # Criteria 1: Affordable
            if buy_price > current_funds:
                continue
                
            # Criteria 2: Profitable
            if forecast_profit <= 0:
                continue
                
            # Criteria 3: Ending Soon (Today)
            if not is_deadline_soon(deadline):
                continue
                
            candidates.append(p)
        except:
            continue

    # 4. Sort by Profit (Descending)
    candidates.sort(key=lambda x: int(x.get("forecast_sell", 0)), reverse=True)
    
    print(f"Found {len(candidates)} valid trade targets.")

    # 5. Send Message
    msg = generate_message(candidates, funds_str)
    print("Sending Telegram notification...")
    send_telegram_message(msg)

if __name__ == "__main__":
    main()

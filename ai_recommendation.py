import os
import requests
import gspread
import google.generativeai as genai
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

def send_telegram_message(message):
    """Send message to Telegram"""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Telegram credentials not found")
        return
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Message sent to Telegram (Markdown)!")
    else:
        print(f"Failed to send Markdown message: {response.text}")
        print("Retrying as plain text...")
        # Fallback to plain text
        del payload["parse_mode"]
        response = requests.post(url, json=payload)
        if response.status_code == 200:
             print("Message sent to Telegram (Plain Text)!")
        else:
             print(f"Failed to send Telegram message (Plain Text): {response.text}")

def main():
    load_dotenv()
    
    # Configure Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Gemini API Key not found")
        return
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Gather data from Transfer Info (Single Source of Truth)
    transfer_data = get_sheet_data("Transfer Info")
    
    if not transfer_data:
        print("No transfer data found.")
        return

    # Sort by Forecast Sell (Profit Potential) Descending to give AI the best candidates first
    # (Assuming forecast_sell is the estimated net profit)
    try:
        transfer_data.sort(key=lambda x: int(x.get("forecast_sell", 0)) if isinstance(x.get("forecast_sell"), (int, float)) or str(x.get("forecast_sell")).replace("-","").isdigit() else 0, reverse=True)
    except:
        pass # If sort fails, just pass as is

    # Top 50 candidates to let AI choose the best 15 fitting the criteria
    candidates = transfer_data[:50]

    # Get Team Funds
    team_info = get_sheet_data("Team Info")
    current_funds = "Unknown"
    if team_info:
        # Get last row (latest data) if row 2 exists
        if len(team_info) >= 1:
             row = team_info[0] # gspread get_all_records returns list of dicts. 0 is first data row.
             current_funds = row.get("Available Funds", "Unknown")

    # Get Current Time for context
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Construct Prompt
    prompt = f"""
    You are a ruthless Day Trader in the Planetarium Manager transfer market. 
    Your ONLY goal is IMMEDIATE PROFIT. 
    
    💰 **CURRENT TEAM FUNDS: {current_funds}** 💰
    ⏰ **CURRENT DATE/TIME: {current_time}** ⏰
    
    **YOUR MISSION:**
    Select the **TOP 15 BEST TRADES** from the list below.
    
    **SELECTION CRITERIA:**
    1.  **DEADLINE IS KING**: Must end within **12 HOURS**. Ignore anything later.
    2.  **AFFORDABILITY**: `Buy Price` MUST be LESS than `Current Team Funds`. Don't recommend players I can't buy.
    3.  **PROFITABILITY**: Prioritize high `Forecast Sell` (Estimated Net Profit).
    
    **CANDIDATE LIST:**
    {candidates}
    
    Please output a Telegram message in Markdown format.
    Structure:
    
    � *Top 15 Day Trade Signals (Expiring < 12h)* �
    
    1. [Player Name/ID]
       📉 Buy: [Price] | 🔮 Forecast Sell: [Forecast Sell]
       🤑 **Est. Profit: [Forecast Sell]**
       ⏱️ Ends: [Deadline]
       💡 [Strategy: Why is this a good flip?]
       🔗 [Link]
    
    2. ...
    ...
    15. ...
    
    ⚠️ *Note:* Buy Price must be within budget ({current_funds}). Profit is estimated.
    
    IMPORTANT: Format the [Link] exactly as: https://www.pmanager.org/comprar_jog_lista.asp?jg_id=[Player_ID]
    """
    
    try:
        response = model.generate_content(prompt)
        analysis = response.text
        
        print("AI Analysis generated. Sending to Telegram...")
        send_telegram_message(analysis)
        
    except Exception as e:
        print(f"Error generating AI analysis: {e}")

if __name__ == "__main__":
    main()

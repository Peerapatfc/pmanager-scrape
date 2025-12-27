import os
import requests
import gspread
import google.generativeai as genai
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

def get_sheet_data(sheet_name):
    """Fetch top 5 rows from a specific sheet"""
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
        
        # Return top 5 (assuming they are already sorted by the scraper)
        return data[:5]
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
        print("Message sent to Telegram!")
    else:
        print(f"Failed to send Telegram message: {response.text}")

def main():
    load_dotenv()
    
    # Configure Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Gemini API Key not found")
        return
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Gather data
    high_quality = get_sheet_data("High Quality")
    low_price = get_sheet_data("Low Price")
    young_potential = get_sheet_data("Young Potential")
    
    # Construct Prompt
    prompt = f"""
    You are a ruthless Day Trader in the Planetarium Manager transfer market. 
    Your ONLY goal is IMMEDIATE PROFIT. You do not care about player quality, age, or potential unless it helps resell value.
    
    Analyze the following transfer targets and pick the SINGLE BEST FLIP from EACH category.
    
    Data provided is the top 5 players sorted by Value Difference (Estimated Value - Buy Price).
    
    Category 1: High Quality (High stakes flips)
    {high_quality}
    
    Category 2: Low Price (Quick flips)
    {low_price}
    
    Category 3: Young Potential (Speculative flips)
    {young_potential}
    
    Please output a Telegram message in Markdown format.
    Structure:
    
    💸 *Day Trade Opportunities* 💸
    
    � *Best High Value Flip*
    [Player Name/ID]
    � Buy: [Price] | 📈 Est: [Value]
    🤑 *Profit:* [Value Diff] | 🚀 *ROI:* [ROI]%
    💡 *Strategy:* [1 sentence on why this is a safe/good flip]
    🔗 [Link]
    
    ⚡ *Quick Budget Flip*
    [Player Name/ID]
    � Buy: [Price] | 📈 Est: [Value]
    🤑 *Profit:* [Value Diff] | 🚀 *ROI:* [ROI]%
    💡 *Strategy:* [1 sentence on profit margin]
    🔗 [Link]
    
    💎 *High Margin Speculation* (Young Potential)
    [Player Name/ID]
    � Buy: [Price] | 📈 Est: [Value]
    🤑 *Profit:* [Value Diff] | 🚀 *ROI:* [ROI]%
    💡 *Strategy:* [1 sentence on resale value]
    🔗 [Link]
    
    ⚠️ *Note:* Buy Price = max(Asking Price, Bids Avg). Profit is estimated.
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

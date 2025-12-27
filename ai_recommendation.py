Import os
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
        
        # Return all data (Gemini Flash has large context window)
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
    
    # Gather data
    high_quality = get_sheet_data("High Quality")
    low_price = get_sheet_data("Low Price")
    young_potential = get_sheet_data("Young Potential")
    
    # Get Team Funds
    team_info = get_sheet_data("Team Info")
    current_funds = "Unknown"
    if team_info:
        current_funds = team_info[-1].get("Available Funds", "Unknown")

    # Get Current Time for the AI to reference
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Construct Prompt
    prompt = f"""
    You are a ruthless Day Trader in the Planetarium Manager transfer market. 
    Your ONLY goal is IMMEDIATE PROFIT. 
    
    💰 **CURRENT TEAM FUNDS: {current_funds}** 💰
    ⏰ **CURRENT DATE/TIME: {current_time}** ⏰
    
    **STRICT CONSTRAINT: DEADLINE WITHIN 24 HOURS**
    You must ONLY recommend players whose transfer deadline is LESS THAN 24 HOURS from the current time provided above.
    - If the player's deadline is more than 24 hours away, IGNORE THEM completely, regardless of profit.
    - If a specific deadline column isn't clear, look for "Time Left", "Deadline", or "Ends" fields.
    
    Analyze the following transfer targets and LIST THE TOP 5 FLIPS from EACH category that meet the time constraint.
    
    Category 1: High Quality (High stakes flips)
    {high_quality}
    
    Category 2: Low Price (Quick flips)
    {low_price}
    
    Category 3: Young Potential (Speculative flips)
    {young_potential}
    
    Please output a Telegram message in Markdown format.
    Structure:
    
    💸 *Day Trade Opportunities (Expiring < 24h)* 💸
    
    💰 *High Value Flips*
    1. [Player Name/ID]
       📉 Buy: [Price] | 📈 Est: [Value] | 🤑 Profit: [Value Diff]
       ⏱️ Ends: [Deadline/Time Left]
       💡 [Very short strategy note]
       🔗 [Link]
    ... (Select 5 best options)
    
    ⚡ *Quick Budget Flips*
    1. [Player Name/ID]
       📉 Buy: [Price] | 📈 Est: [Value] | 🤑 Profit: [Value Diff]
       ⏱️ Ends: [Deadline/Time Left]
       💡 [Very short strategy note]
       🔗 [Link]
    ... (Select 5 best options)
    
    💎 *High Margin Speculation* (Young Potential)
    1. [Player Name/ID]
       📉 Buy: [Price] | 📈 Est: [Value] | 🤑 Profit: [Value Diff]
       ⏱️ Ends: [Deadline/Time Left]
       💡 [Very short strategy note]
       🔗 [Link]
    ... (Select 5 best options)
    
    ⚠️ *Note:* Buy Price = max(Asking Price, Bids Avg). Profit is estimated. Only showing auctions ending soon.
    
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
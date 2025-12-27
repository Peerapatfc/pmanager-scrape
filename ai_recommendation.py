import os
import requests
import gspread
import google.generativeai as genai
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from datetime import datetime, timedelta # <--- Added datetime

# ... [Keep your existing get_sheet_data and send_telegram_message functions exactly as they are] ...

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

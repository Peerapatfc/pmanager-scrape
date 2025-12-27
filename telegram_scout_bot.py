import os
import time
import requests
import json
from dotenv import load_dotenv

# Load config
load_dotenv()
# Use a specific token for the Scout Bot
TELEGRAM_BOT_TOKEN = os.getenv("SCOUT_BOT_TOKEN") 
# Optional: Use a specific chat ID or reuse the main one
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "Peerapatfc/pmanager-scrape")

def get_updates(offset=None):
    if not TELEGRAM_BOT_TOKEN:
        print("Error: SCOUT_BOT_TOKEN not found.")
        return None
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"Error getting updates: {e}")
        return None

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

def trigger_github_workflow(workflow_file, inputs):
    """Trigger the GitHub Action workflow via API"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{workflow_file}/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "ref": "main",
        "inputs": inputs
    }
    
    print(f"Triggering {workflow_file} with inputs: {inputs}")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 204:
        print("Successfully triggered workflow!")
        return True
    else:
        print(f"Failed to trigger workflow: {response.status_code} - {response.text}")
        return False

def main():
    if not TELEGRAM_BOT_TOKEN or not GITHUB_TOKEN:
        print("Error: SCOUT_BOT_TOKEN and GITHUB_TOKEN must be set in .env")
        return

    print(f"🕵️‍♂️ Scout Bot started. Listening for commands on repo: {GITHUB_REPO}...")
    offset = None
    
    while True:
        updates = get_updates(offset)
        
        if updates and "result" in updates:
            for update in updates["result"]:
                offset = update["update_id"] + 1
                
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"].strip()
                    
                    print(f"Received: {text}")

                    # Support both /scout and just the URL for this dedicated bot
                    if text.startswith("/scout") or "pmanager.org" in text:
                        
                        target = text
                        if text.startswith("/scout"):
                             parts = text.split(maxsplit=1)
                             if len(parts) > 1:
                                 target = parts[1]
                             else:
                                 send_message(chat_id, "⚠️ Usage: /scout <TeamID or URL>")
                                 continue
                        
                        send_message(chat_id, f"🕵️‍♂️ Opponent Scout triggered for: {target}")
                        
                        success = trigger_github_workflow(
                            "opponent_scout.yml", 
                            {"scout_target": target}
                        )
                        
                        if success:
                            send_message(chat_id, "✅ Scouting started! Check Google Sheets in a few minutes.")
                        else:
                            send_message(chat_id, "❌ Failed to trigger scraper. Check console.")
                            
                    elif text == "/start" or text == "/help":
                         send_message(chat_id, "👋 I am the dedicated Scout Bot.\nSend me a Team URL or ID (e.g., 35126) or use /scout <target> to scrape data.")

        time.sleep(1)

if __name__ == "__main__":
    main()

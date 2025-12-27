import os
import time
import requests
import json
from dotenv import load_dotenv

# Load config
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# Format: "owner/repo" e.g. "Peerapatfc/pmanager-scrape"
GITHUB_REPO = os.getenv("GITHUB_REPO", "Peerapatfc/pmanager-scrape") 

def get_updates(offset=None):
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

def trigger_github_workflow(inputs):
    """Trigger the GitHub Action workflow via API"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/scraper.yml/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "ref": "main", # Branch to run on
        "inputs": inputs
    }
    
    print(f"Triggering GitHub Action with inputs: {inputs}")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 204:
        print("Successfully triggered workflow!")
        return True
    else:
        print(f"Failed to trigger workflow: {response.status_code} - {response.text}")
        return False

def main():
    if not TELEGRAM_BOT_TOKEN or not GITHUB_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN and GITHUB_TOKEN must be set in .env")
        return

    print(f"Bot started. Listening for commands on repo: {GITHUB_REPO}...")
    offset = None
    
    while True:
        updates = get_updates(offset)
        
        if updates and "result" in updates:
            for update in updates["result"]:
                offset = update["update_id"] + 1
                
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"].strip()
                    
                    # Security check: Only allow your chat ID? (Optional but recommended)
                    # if str(chat_id) != str(TELEGRAM_CHAT_ID):
                    #     continue

                    print(f"Received: {text}")

                    if text.startswith("/scout"):
                        parts = text.split(maxsplit=1)
                        if len(parts) > 1:
                            target = parts[1]
                            send_message(chat_id, f"🕵️‍♂️ Starting Opponent Scout for: {target}\nCheck GitHub Actions for progress...")
                            
                            success = trigger_github_workflow({
                                "scraper_type": "opponent_scout",
                                "scout_target": target
                            })
                            
                            if not success:
                                send_message(chat_id, "❌ Failed to trigger scraper. Check bot logs.")
                        else:
                            send_message(chat_id, "⚠️ Usage: /scout <TeamID or URL>")
                            
                    elif text == "/status":
                        send_message(chat_id, "✅ Bot is running and listening.")
                        
        time.sleep(1)

if __name__ == "__main__":
    main()

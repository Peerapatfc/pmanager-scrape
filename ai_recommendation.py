from datetime import datetime, timedelta
from src.config import config
from src.core.logger import logger
from src.core.utils import parse_deadline, clean_currency
from src.services.gsheets import SheetManager
from src.services.telegram import TelegramBot

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
        buy = f"{int(p.get('asking_price', 0)):,}"
        sell = f"{int(p.get('forecast_sell', 0)):,}"
        profit = p.get('forecast_sell', 0)
        deadline = p.get('deadline', 'N/A')
        
        # Emoji based on profit
        profit_icon = "🤑" if profit > 10000000 else "💵"
        
        entry = (
            f"{i}. *{name}*\n"
            f"   📉 Buy: {buy} | {profit_icon} Profit: {sell}\n"
            f"   ⏱️ Ends: {deadline}\n"
            f"   🔗 Link: https://www.pmanager.org/comprar_jog_lista.asp?jg_id={pid}\n"
        )
        msg += entry + "\n"
        
    msg += "⚠️ *Auto-generated based on (Est. Value/2 * 0.8) - Buy Price*"
    return msg

def main():
    config.validate()
    
    # Set Reference Time (Thailand Time: UTC+7)
    # Using the same logic as direct utils if needed, but here explicit is fine
    now_th = datetime.utcnow() + timedelta(hours=7)
    
    sheet_manager = SheetManager()
    bot = TelegramBot()

    # 1. Gather Data
    transfer_data = sheet_manager.get_all_records(config.SHEET_NAME_TRANSFER_INFO)
    if not transfer_data:
        logger.warning("No transfer data found.")
        return

    # 2. Get Team Funds
    # Note: "Team Info" sheet name might need to be added to config if used often. 
    # Hardcoding for now as verified in old script.
    team_info = sheet_manager.get_all_records("Team Info")
    current_funds = 0
    funds_str = "0"
    
    if team_info and len(team_info) >= 1:
         row = team_info[0]
         funds_raw = row.get("Available Funds", "0")
         funds_str = str(funds_raw)
         current_funds = clean_currency(funds_raw)

    logger.info(f"Current Funds: {current_funds:,}")
    logger.info(f"Current Time (TH): {now_th}")

    # 3. Filter Candidates
    candidates = []
    dropped_stats = {"budget": 0, "profit": 0, "time": 0, "parse_error": 0}
    
    for i, p in enumerate(transfer_data):
        try:
            buy_price = int(p.get("asking_price", 0))
            forecast_profit = int(p.get("forecast_sell", 0))
            deadline_str = str(p.get("deadline", ""))
            
            # Criteria 1: Affordable
            if buy_price > current_funds:
                dropped_stats["budget"] += 1
                continue
                
            # Criteria 2: Profitable
            if forecast_profit <= 0:
                dropped_stats["profit"] += 1
                continue
                
            # Criteria 3: Time Check (Future + Within 12 Hours)
            deadline_dt = parse_deadline(deadline_str) # Returns TH Time
            
            if not deadline_dt:
                dropped_stats["parse_error"] += 1
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
            else:
                dropped_stats["time"] += 1
                
        except Exception as e:
            # logger.debug(f"Skipping row error: {e}")
            continue

    # 4. Sort by Profit (Descending)
    candidates.sort(key=lambda x: int(x.get("forecast_sell", 0)), reverse=True)
    
    logger.info(f"Filter Summary: Passed={len(candidates)}, Dropped={dropped_stats}")

    # 5. Send Message
    if not candidates:
        # Send debug info to Telegram if empty
        debug_msg = f"📉 *Market Update* ({now_th.strftime('%H:%M')})\n\n"
        debug_msg += "No profitable flips found within budget right now.\n\n"
        debug_msg += "*Filter Stats:*\n"
        debug_msg += f"❌ Budget: {dropped_stats['budget']}\n"
        debug_msg += f"❌ No Profit: {dropped_stats['profit']}\n"
        debug_msg += f"❌ Time (>12h or Past): {dropped_stats['time']}\n"
        debug_msg += f"❌ Parse Error: {dropped_stats['parse_error']}\n"
        debug_msg += f"🔍 *Total Checked:* {len(transfer_data)}"
        bot.send_message(debug_msg)
    else:
        msg = generate_message(candidates, funds_str, now_th)
        logger.info("Sending Telegram notification...")
        bot.send_message(msg)

if __name__ == "__main__":
    main()

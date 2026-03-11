from datetime import datetime, timedelta
from src.config import config
from src.core.logger import logger
from src.core.utils import parse_deadline, clean_currency
from src.services.supabase_client import SupabaseManager
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
        profit_val = p.get('net_profit', 0)
        profit_str = f"{int(profit_val):,}"
        deadline = p.get('deadline', 'N/A')
        
        profit_icon = "🤑" if profit_val > 10000000 else "💵"
        
        entry = (
            f"{i}. *{name}*\n"
            f"   📉 Buy: {buy} | {profit_icon} Profit: {profit_str}\n"
            f"   ⏱️ Ends: {deadline}\n"
            f"   🔗 Link: https://www.pmanager.org/comprar_jog_lista.asp?jg_id={pid}\n"
        )
        msg += entry + "\n"
        
    msg += "⚠️ *Auto-generated based on (Est. Value/2 * 0.8) - Buy Price*"
    return msg

def main():
    config.validate()
    
    now_th = datetime.utcnow() + timedelta(hours=7)
    
    db = SupabaseManager()
    bot = TelegramBot()

    # 1. Gather Data
    transfer_data = db.get_all_transfer_listings()
    if not transfer_data:
        logger.warning("No transfer data found.")
        return

    # 2. Get Team Funds
    team_info = db.get_team_info()
    current_funds = 0
    funds_str = "0"
    
    if team_info:
         funds_raw = team_info.get("available_funds", "0")
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
            
            if buy_price > current_funds or buy_price > 30000000:
                dropped_stats["budget"] += 1
                continue
                
            net_profit = 0
            if "forecast_profit" in p and str(p["forecast_profit"]).strip():
                 net_profit = int(float(p["forecast_profit"]))
            
            p["net_profit"] = net_profit
            
            if net_profit <= 0:
                dropped_stats["profit"] += 1
                continue
                
            deadline_dt = parse_deadline(deadline_str)
            
            if not deadline_dt:
                dropped_stats["parse_error"] += 1
                continue
                
            diff = deadline_dt - now_th
            total_seconds = diff.total_seconds()
            
            if 0 < total_seconds < (12 * 3600):
                p["deadline"] = deadline_dt.strftime("%d/%m %H:%M")
                candidates.append(p)
            else:
                dropped_stats["time"] += 1
                
        except Exception as e:
            continue

    # 4. Sort by Profit (Descending)
    candidates.sort(key=lambda x: int(x.get("net_profit", 0)), reverse=True)
    
    logger.info(f"Filter Summary: Passed={len(candidates)}, Dropped={dropped_stats}")

    # 5. Send Message
    if not candidates:
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

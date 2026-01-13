import re
from datetime import datetime, timedelta

def parse_deadline(deadline_str):
    """
    Parse 'Today at 10:19' or 'Tomorrow at ...' -> UTC+7 Datetime
    """
    if not deadline_str or not isinstance(deadline_str, str):
        return None
    
    txt = deadline_str.lower().strip()
    match = re.search(r'(\d{1,2}):(\d{2})', txt)
    if not match:
        return None
        
    hour = int(match.group(1))
    minute = int(match.group(2))
    
    # Base calculation using UTC then converting to TH time
    utc_now = datetime.utcnow()
    
    if "today" in txt:
        target_utc = utc_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    elif "tomorrow" in txt:
        target_utc = (utc_now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    else:
        return None
    
    # Return TH time (UTC+7)
    return target_utc + timedelta(hours=7)

def clean_currency(value_str):
    """
    Convert string like '1.000.000 baht' to int 1000000
    """
    if not value_str:
        return 0
    clean = re.sub(r'[^\d]', '', str(value_str))
    return int(clean) if clean else 0

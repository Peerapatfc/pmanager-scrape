import logging
import sys

def setup_logger(name="PManagerScraper", level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        # Console Handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File Handler (Optional)
        # fh = logging.FileHandler('scraper.log')
        # fh.setFormatter(formatter)
        # logger.addHandler(fh)
    
    return logger

logger = setup_logger()

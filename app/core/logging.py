import logging
import sys
from pathlib import Path

def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create logger
    logger = logging.getLogger("deep-research")
    return logger

def get_logger(name=None):
    """Get a logger instance by name"""
    if name is None:
        return logger
    return logging.getLogger(name)

# Global logger instance
logger = setup_logging() 
import os
import logging
from dotenv import load_dotenv

load_dotenv()

def setup_logging():
    """Setup basic logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_env_var(key, default=None):
    return os.environ.get(key, default)

logger = setup_logging()
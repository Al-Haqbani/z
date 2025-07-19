import logging
import os

LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'runtime.log')

level_name = os.getenv('EMPLOLEAKS_LOG_LEVEL', 'INFO').upper()
level = getattr(logging, level_name, logging.INFO)

logging.basicConfig(
    level=level,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('emploleaks')

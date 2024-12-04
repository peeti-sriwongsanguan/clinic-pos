from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent
    STATIC_DIR = BASE_DIR / 'static'

    # Directory paths - converted to Path objects
    DATABASE_PATH = BASE_DIR / 'data' / 'clinic_pos.db'
    BACKUP_DIR = BASE_DIR / 'backups'
    LOG_DIR = BASE_DIR / 'logs'
    RECEIPT_DIR = BASE_DIR / 'receipts'

    # Static file paths
    STATIC_ASSETS = STATIC_DIR / 'assets'
    TEMPLATES_DIR = STATIC_ASSETS / 'templates'

    # Company details from environment variables
    COMPANY_NAME = os.getenv('COMPANY_NAME', 'Your Beauty Clinic')
    COMPANY_ADDRESS = os.getenv('COMPANY_ADDRESS', 'Your Address')
    COMPANY_PHONE = os.getenv('COMPANY_PHONE', 'Your Phone')
    COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', 'your@email.com')

    @staticmethod
    def ensure_directories():
        """Ensure all required directories exist"""
        dirs = [
            Config.BASE_DIR / 'data',
            Config.BACKUP_DIR,
            Config.LOG_DIR,
            Config.RECEIPT_DIR,
            Config.STATIC_DIR,
            Config.STATIC_ASSETS,
            Config.TEMPLATES_DIR
        ]
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
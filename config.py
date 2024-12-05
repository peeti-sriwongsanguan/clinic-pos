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

    # Environment-based configuration
    ENV = os.getenv('APP_ENV', 'development')

    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'beauty_clinic')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # S3 configuration for file storage
    S3_BUCKET = os.getenv('S3_BUCKET')
    AWS_REGION = os.getenv('AWS_REGION', 'east-1')

    # API configuration
    API_BASE_URL = os.getenv('API_BASE_URL')

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

    @staticmethod
    def get_database_url():
        if Config.ENV == 'development':
            return f"sqlite:///{Config.DATABASE_PATH}"
        return f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
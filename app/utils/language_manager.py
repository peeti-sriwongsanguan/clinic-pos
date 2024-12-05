import json
import logging
from typing import Dict, Optional
from functools import lru_cache
from pathlib import Path


class LanguageManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.current_language = 'en'  # Default to English
        self._load_translations()

    def _load_translations(self):
        """Load translations from database and cache them"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT language_code, key, value 
                    FROM translations 
                    WHERE language_code IN ('en', 'th')
                ''')
                self.translations = {}
                for lang_code, key, value in cursor.fetchall():
                    if lang_code not in self.translations:
                        self.translations[lang_code] = {}
                    self.translations[lang_code][key] = value
        except Exception as e:
            logging.error(f"Error loading translations: {e}")
            self._load_fallback_translations()

    def _load_fallback_translations(self):
        """Load translations from JSON files as fallback"""
        try:
            base_path = Path(__file__).parent.parent / 'resources' / 'translations'
            self.translations = {}

            for lang in ['en', 'th']:
                file_path = base_path / f'{lang}.json'
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[lang] = json.load(f)
        except Exception as e:
            logging.error(f"Error loading fallback translations: {e}")
            self.translations = self._get_default_translations()

    def _get_default_translations(self) -> Dict:
        """Provide minimal default translations"""
        return {
            'en': {
                'app_name': 'Beauty Clinic POS',
                'patient': 'Patient',
                'doctor': 'Doctor',
                # Add more default translations
            },
            'th': {
                'app_name': 'ระบบคลินิกความงาม',
                'patient': 'ผู้ป่วย',
                'doctor': 'แพทย์',
                # Add more default translations
            }
        }

    def set_language(self, language_code: str):
        """Change current language"""
        if language_code in self.translations:
            self.current_language = language_code
        else:
            logging.error(f"Unsupported language: {language_code}")

    def get_text(self, key: str, default: Optional[str] = None) -> str:
        """Get translated text for a key"""
        try:
            return self.translations[self.current_language].get(key, default or key)
        except Exception:
            return default or key

    @lru_cache(maxsize=1000)
    def get_cached_text(self, key: str, default: Optional[str] = None) -> str:
        """Cached version of get_text for frequently used translations"""
        return self.get_text(key, default)

    def refresh_translations(self):
        """Refresh translations from database"""
        self._load_translations()
        self.get_cached_text.cache_clear()
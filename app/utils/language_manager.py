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
                'language': 'Language',
                'patients': 'Patients',
                'doctor_notes': 'Doctor Notes',
                'clinic_name': 'Wellness by BFF',
                'doctor': 'Doctor',
                "search": "Search",
                "add_new_patient": "Add New Patient",
                "edit_patient": "Edit Patient",
                "delete_patient": "Delete Patient",
                "refresh": "Refresh",
                'name': 'Name',
                'phone': 'Phone',
                'email': 'Email',
                'last_visit': 'Last Visit',
                'notes': 'Notes',
                'save': 'Save',
                'cancel': 'Cancel',
                'medical_history': 'Medical History',
                'error_loading_patient': 'Error loading patient data',
                'patient_not_found': 'Patient not found',
                'select_patient_to_edit': 'Please select a patient to edit'
                # Add more default translations
            },
            'th': {
                'app_name': 'ระบบคลินิกความงาม',
                'language': 'ภาษา',
                'patients': 'ผู้ป่วย',
                'doctor_notes': 'บันทึกแพทย์',
                'clinic_name': 'เวลเนส บาย บีเอฟเอฟ',
                'doctor': 'แพทย์',
                "search": "ค้นหา",
                "add_new_patient": "เพิ่มผู้ป่วยใหม่",
                "edit_patient": "แก้ไขข้อมูลผู้ป่วย",
                "delete_patient": "ลบข้อมูลผู้ป่วย",
                "refresh": "รีเฟรช",
                'name': 'ชื่อ',
                'phone': 'โทรศัพท์',
                'email': 'อีเมล',
                'last_visit': 'เข้ารับการรักษาล่าสุด',
                'notes': 'บันทึก',
                'save': 'บันทึก',
                'cancel': 'ยกเลิก',
                'medical_history': 'ประวัติการรักษา',
                'error_loading_patient': 'เกิดข้อผิดพลาดในการโหลดข้อมูลผู้ป่วย',
                'patient_not_found': 'ไม่พบข้อมูลผู้ป่วย',
                'select_patient_to_edit': 'กรุณาเลือกผู้ป่วยที่ต้องการแก้ไข'
                # Add more default translations
            }
        }

    def set_language(self, language_code: str):
        """Change current language"""
        if language_code in self.translations:
            self.current_language = language_code
            return True
        else:
            logging.error(f"Unsupported language: {language_code}")
            return False

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
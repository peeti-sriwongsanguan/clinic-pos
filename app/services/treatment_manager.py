from datetime import datetime
from typing import List, Dict, Optional
import logging
from pathlib import Path
import json


class TreatmentManager:
    def __init__(self, db_manager, storage_service):
        self.db = db_manager
        self.storage = storage_service

    def create_treatment_record(self, data: Dict) -> str:
        """Create a new treatment record"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                record_id = str(uuid.uuid4())

                # Handle photo uploads if any
                before_photos = self._upload_photos(data.get('before_photos', []))
                after_photos = self._upload_photos(data.get('after_photos', []))

                cursor.execute('''
                    INSERT INTO treatment_records (
                        id, patient_id, doctor_id, service_id,
                        treatment_date, chief_complaint, diagnosis,
                        treatment_plan, treatment_notes,
                        next_appointment_notes, before_photos,
                        after_photos, followup_required,
                        created_at, modified_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record_id,
                    data['patient_id'],
                    data['doctor_id'],
                    data['service_id'],
                    data['treatment_date'],
                    data.get('chief_complaint'),
                    data.get('diagnosis'),
                    data.get('treatment_plan'),
                    data.get('treatment_notes'),
                    data.get('next_appointment_notes'),
                    ','.join(before_photos) if before_photos else None,
                    ','.join(after_photos) if after_photos else None,
                    data.get('followup_required', False),
                    datetime.now(),
                    datetime.now()
                ))

                return record_id

            except Exception as e:
                logging.error(f"Error creating treatment record: {e}")
                raise

    def update_progress(self, record_id: str, progress_data: Dict) -> str:
        """Add a progress update to a treatment"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                progress_id = str(uuid.uuid4())
                photos = self._upload_photos(progress_data.get('photos', []))

                cursor.execute('''
                    INSERT INTO treatment_progress (
                        id, treatment_record_id, progress_date,
                        progress_notes, complications, patient_feedback,
                        doctor_notes, photos, satisfaction_level,
                        created_at, modified_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    progress_id,
                    record_id,
                    progress_data['progress_date'],
                    progress_data.get('progress_notes'),
                    progress_data.get('complications'),
                    progress_data.get('patient_feedback'),
                    progress_data.get('doctor_notes'),
                    ','.join(photos) if photos else None,
                    progress_data.get('satisfaction_level'),
                    datetime.now(),
                    datetime.now()
                ))

                return progress_id

            except Exception as e:
                logging.error(f"Error updating treatment progress: {e}")
                raise

    def get_patient_treatment_history(self, patient_id: str) -> List[Dict]:
        """Get complete treatment history for a patient"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Get all treatment records
                cursor.execute('''
                    SELECT tr.*, s.name as service_name, 
                           staff.name as doctor_name
                    FROM treatment_records tr
                    JOIN services s ON tr.service_id = s.id
                    JOIN staff ON tr.doctor_id = staff.id
                    WHERE tr.patient_id = ?
                    ORDER BY tr.treatment_date DESC
                ''', (patient_id,))

                treatment_records = []
                for record in cursor.fetchall():
                    record_dict = dict(record)

                    # Get progress updates for each treatment
                    cursor.execute('''
                        SELECT * FROM treatment_progress
                        WHERE treatment_record_id = ?
                        ORDER BY progress_date DESC
                    ''', (record_dict['id'],))

                    progress_updates = [dict(p) for p in cursor.fetchall()]
                    record_dict['progress_updates'] = progress_updates
                    treatment_records.append(record_dict)

                return treatment_records

            except Exception as e:
                logging.error(f"Error retrieving treatment history: {e}")
                return []

    def get_treatment_templates(self, service_id: Optional[str] = None) -> List[Dict]:
        """Get available treatment note templates"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if service_id:
                    cursor.execute('''
                        SELECT * FROM treatment_templates
                        WHERE service_id = ? AND is_active = 1
                    ''', (service_id,))
                else:
                    cursor.execute('''
                        SELECT * FROM treatment_templates
                        WHERE is_active = 1
                    ''')

                return [dict(row) for row in cursor.fetchall()]

            except Exception as e:
                logging.error(f"Error retrieving templates: {e}")
                return []

    def _upload_photos(self, photos: List) -> List[str]:
        """Upload photos to storage and return URLs"""
        uploaded_urls = []
        for photo in photos:
            try:
                url = self.storage.upload_file(photo['path'],
                                               f"treatments/{datetime.now().strftime('%Y/%m/%d')}/{photo['name']}")
                uploaded_urls.append(url)
            except Exception as e:
                logging.error(f"Error uploading photo: {e}")
        return uploaded_urls
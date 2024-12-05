import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging
from decimal import Decimal
from contextlib import contextmanager
from pathlib import Path

from config import Config
from .model import Patient, Service, Transaction, TransactionItem, Appointment, Staff


class DatabaseManager:
    def __init__(self):
        self.setup_logging()
        self.initialize_database()

    def setup_logging(self):
        logging.basicConfig(
            filename=Config.LOG_DIR / f'db_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Database error: {str(e)}")
            raise
        finally:
            conn.close()

    def initialize_database(self):
        """Initialize the database with tables if they don't exist"""
        with self.get_connection() as conn:
            try:
                # Read schema from file
                schema_path = Path(__file__).parent / 'schema.sql'
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())
                logging.info("Database initialized successfully")
            except Exception as e:
                logging.error(f"Error initializing database: {str(e)}")
                raise

    # Patient management methods
    # def add_patient(self, patient: Patient) -> str:
    #     with self.get_connection() as conn:
    #         cursor = conn.cursor()
    #         patient_id = str(uuid.uuid4())
    #         cursor.execute('''
    #             INSERT INTO patients (
    #                 id, name, phone, email, address, created_at,
    #                 medical_history, notes, birth_date, gender,
    #                 emergency_contact
    #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #         ''', (
    #             patient_id, patient.name, patient.phone, patient.email,
    #             patient.address, datetime.now(), patient.medical_history,
    #             patient.notes, patient.birth_date, patient.gender,
    #             patient.emergency_contact
    #         ))
    #         return patient_id

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            result = cursor.execute(
                'SELECT * FROM patients WHERE id = ?',
                (patient_id,)
            )
            row = result.fetchone()
            return Patient(**dict(row)) if row else None

    # def search_patients(self, query: str) -> List[Patient]:
    #     with self.get_connection() as conn:
    #         cursor = conn.cursor()
    #         result = cursor.execute('''
    #             SELECT * FROM patients
    #             WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
    #         ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    #         return [Patient(**dict(row)) for row in result.fetchall()]

    # Service management methods
    def add_service(self, service: Service) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            service_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO services (
                    id, name, price, description, category,
                    duration, active, created_at, modified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                service_id, service.name, float(service.price),
                service.description, service.category, service.duration,
                service.active, datetime.now(), datetime.now()
            ))
            return service_id

    def get_services_by_category(self, category: str) -> List[Service]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            result = cursor.execute(
                'SELECT * FROM services WHERE category = ? AND active = 1',
                (category,)
            )
            return [Service(**dict(row)) for row in result.fetchall()]

    # Transaction management methods
    def create_transaction(self, transaction: Transaction) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            transaction_id = str(uuid.uuid4())

            # Insert main transaction
            cursor.execute('''
                INSERT INTO transactions (
                    id, patient_id, total_amount, payment_method,
                    transaction_date, status, notes, discount_amount,
                    tax_amount, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction_id, transaction.patient_id,
                float(transaction.total_amount),
                transaction.payment_method, transaction.transaction_date,
                transaction.status, transaction.notes,
                float(transaction.discount_amount),
                float(transaction.tax_amount), transaction.created_by
            ))

            # Insert transaction items
            for item in transaction.items:
                cursor.execute('''
                    INSERT INTO transaction_items (
                        id, transaction_id, service_id, quantity,
                        price, discount, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()), transaction_id,
                    item.service_id, item.quantity,
                    float(item.price), float(item.discount),
                    item.notes
                ))

            return transaction_id

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get main transaction
            result = cursor.execute(
                'SELECT * FROM transactions WHERE id = ?',
                (transaction_id,)
            )
            trans_row = result.fetchone()
            if not trans_row:
                return None

            # Get transaction items
            items_result = cursor.execute(
                'SELECT * FROM transaction_items WHERE transaction_id = ?',
                (transaction_id,)
            )
            items = [TransactionItem(**dict(row)) for row in items_result]

            # Create transaction object
            trans_dict = dict(trans_row)
            trans_dict['items'] = items
            return Transaction(**trans_dict)

    # Appointment management methods
    def create_appointment(self, appointment: Appointment) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            appointment_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO appointments (
                    id, patient_id, service_id, start_time,
                    end_time, status, notes, created_at, modified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                appointment_id, appointment.patient_id,
                appointment.service_id, appointment.start_time,
                appointment.end_time, appointment.status,
                appointment.notes, datetime.now(), datetime.now()
            ))
            return appointment_id

    def get_appointments_by_date(self, date: datetime) -> List[Appointment]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            start_of_day = date.replace(hour=0, minute=0, second=0)
            end_of_day = date.replace(hour=23, minute=59, second=59)

            result = cursor.execute('''
                SELECT * FROM appointments 
                WHERE start_time BETWEEN ? AND ?
                ORDER BY start_time
            ''', (start_of_day, end_of_day))

            return [Appointment(**dict(row)) for row in result.fetchall()]

    # Staff management methods
    def add_staff(self, staff: Staff) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            staff_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO staff (
                    id, name, email, phone, role,
                    active, created_at, modified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                staff_id, staff.name, staff.email, staff.phone,
                staff.role, staff.active, datetime.now(), datetime.now()
            ))
            return staff_id

    def get_active_staff(self) -> List[Staff]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            result = cursor.execute('SELECT * FROM staff WHERE active = 1')
            return [Staff(**dict(row)) for row in result.fetchall()]

    def get_all_patients(self) -> List[Patient]:
        """Retrieve all patients from the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                result = cursor.execute('''
                    SELECT * FROM patients 
                    ORDER BY name ASC
                ''')
                return [Patient(**dict(row)) for row in result.fetchall()]
            except Exception as e:
                logging.error(f"Error retrieving patients: {e}")
                return []

    def add_patient(self, patient: Patient) -> str:
        """Add a new patient to the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                patient_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO patients (
                        id, name, phone, email, address, created_at,
                        medical_history, notes, birth_date, gender,
                        emergency_contact
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    patient_id,
                    patient.name,
                    patient.phone,
                    patient.email,
                    patient.address,
                    patient.created_at,
                    patient.medical_history,
                    patient.notes,
                    patient.birth_date,
                    patient.gender,
                    patient.emergency_contact
                ))
                logging.info(f"Added new patient with ID: {patient_id}")
                return patient_id
            except Exception as e:
                logging.error(f"Error adding patient: {e}")
                raise

    def update_patient(self, patient: Patient) -> bool:
        """Update an existing patient's information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE patients 
                    SET name = ?, phone = ?, email = ?, address = ?,
                        medical_history = ?, notes = ?, birth_date = ?,
                        gender = ?, emergency_contact = ?
                    WHERE id = ?
                ''', (
                    patient.name,
                    patient.phone,
                    patient.email,
                    patient.address,
                    patient.medical_history,
                    patient.notes,
                    patient.birth_date,
                    patient.gender,
                    patient.emergency_contact,
                    patient.id
                ))
                logging.info(f"Updated patient with ID: {patient.id}")
                return True
            except Exception as e:
                logging.error(f"Error updating patient: {e}")
                return False

    def delete_patient(self, patient_id: str) -> bool:
        """Delete a patient from the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
                logging.info(f"Deleted patient with ID: {patient_id}")
                return True
            except Exception as e:
                logging.error(f"Error deleting patient: {e}")
                return False

    def search_patients(self, query: str) -> List[Patient]:
        """Search for patients based on name, phone, or email"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                result = cursor.execute('''
                    SELECT * FROM patients 
                    WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
                    ORDER BY name ASC
                ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
                return [Patient(**dict(row)) for row in result.fetchall()]
            except Exception as e:
                logging.error(f"Error searching patients: {e}")
                return []

    def get_patient_history(self, patient_id: str) -> dict:
        """Get a patient's complete history including treatments and appointments"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Get patient details
                patient = self.get_patient(patient_id)
                if not patient:
                    return None

                # Get treatments/transactions
                transactions = cursor.execute('''
                    SELECT * FROM transactions 
                    WHERE patient_id = ? 
                    ORDER BY transaction_date DESC
                ''', (patient_id,))

                # Get appointments
                appointments = cursor.execute('''
                    SELECT * FROM appointments 
                    WHERE patient_id = ? 
                    ORDER BY start_time DESC
                ''', (patient_id,))

                return {
                    'patient': patient,
                    'transactions': [dict(row) for row in transactions],
                    'appointments': [dict(row) for row in appointments]
                }
            except Exception as e:
                logging.error(f"Error retrieving patient history: {e}")
                return None
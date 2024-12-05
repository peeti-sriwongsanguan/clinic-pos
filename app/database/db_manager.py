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
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        """Initialize database connection and setup tables"""
        logger.debug("Initializing DatabaseManager")
        try:
            self.conn = sqlite3.connect('clinic.db')
            self.conn.row_factory = sqlite3.Row

            # Create tables
            self.create_tables()

            # Add test data if database is empty
            self.initialize_test_data()

            logger.debug("Database initialization complete")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def create_tables(self):
        """Create necessary database tables"""
        cursor = self.conn.cursor()

        try:
            # Patients table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT,
                    address TEXT,
                    birth_date TEXT,
                    gender TEXT,
                    emergency_contact TEXT,
                    medical_history TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Doctor notes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doctor_notes (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    medical_history TEXT,
                    progress_notes TEXT,
                    recommendations TEXT,
                    next_steps TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            ''')

            # Photos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patient_photos (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    photo_path TEXT NOT NULL,
                    photo_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            ''')

            self.conn.commit()
            logger.debug("Tables created successfully")

        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            self.conn.rollback()
            raise

    def initialize_test_data(self):
        """Initialize database with test data if empty"""
        try:
            cursor = self.conn.cursor()
            logger.debug("Checking database content...")

            # Delete all existing test data first
            cursor.execute("DELETE FROM doctor_notes")
            cursor.execute("DELETE FROM patients")
            self.conn.commit()

            logger.debug("Adding test data...")
            # Add test patients
            test_patients = [
                {
                    "name": "Test Patient",
                    "phone": "123-456-7890",
                    "email": "test@example.com",
                    "medical_history": "Initial visit with general checkup"
                },
                {
                    "name": "John Doe",
                    "phone": "098-765-4321",
                    "email": "john@example.com",
                    "medical_history": "Regular patient since 2023"
                },
                {
                    "name": "Jane Smith",
                    "phone": "111-222-3333",
                    "email": "jane@example.com",
                    "medical_history": "New patient"
                }
            ]

            added_patients = []
            for patient in test_patients:
                patient_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO patients (
                        id, name, phone, email, medical_history, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    patient_id,
                    patient["name"],
                    patient["phone"],
                    patient["email"],
                    patient["medical_history"],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                added_patients.append((patient_id, patient["name"]))

            # Add test notes for each patient
            for patient_id, patient_name in added_patients:
                cursor.execute('''
                    INSERT INTO doctor_notes (
                        id, patient_id, medical_history, progress_notes,
                        recommendations, next_steps, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()),
                    patient_id,
                    f"Initial medical history for {patient_name}",
                    "Progress is good",
                    "Continue current treatment",
                    "Follow up in 2 weeks",
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))

            self.conn.commit()
            logger.debug(f"Added {len(test_patients)} test patients with notes")

        except Exception as e:
            logger.error(f"Error initializing test data: {e}")
            self.conn.rollback()
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

    def add_patient(self, patient_data):
        """Add a new patient to the database
        Args:
            patient_data (dict): Dictionary containing patient information
        Returns:
            str: ID of the newly created patient
        """
        logger.debug(f"Adding new patient: {patient_data}")
        try:
            cursor = self.conn.cursor()

            # Execute the insert
            cursor.execute('''
                INSERT INTO patients (
                    id, name, phone, email, address,
                    birth_date, gender, emergency_contact,
                    medical_history, notes, created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_data['id'],
                patient_data['name'],
                patient_data['phone'],
                patient_data['email'],
                patient_data['address'],
                patient_data['birth_date'],
                patient_data['gender'],
                patient_data['emergency_contact'],
                patient_data['medical_history'],
                patient_data['notes'],
                patient_data['created_at'],
                patient_data['updated_at']
            ))

            # Add initial doctor notes if medical history exists
            if patient_data.get('medical_history'):
                notes_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO doctor_notes (
                        id, patient_id, medical_history,
                        created_at
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    notes_id,
                    patient_data['id'],
                    patient_data['medical_history'],
                    patient_data['created_at']
                ))

            # Commit the transaction
            self.conn.commit()
            logger.info(f"Successfully added patient with ID: {patient_data['id']}")

            return patient_data['id']

        except Exception as e:
            logger.error(f"Error adding patient: {e}")
            self.conn.rollback()
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

    def get_patient_last_visit(self, patient_id):
        """Get patient's last visit date"""
        logger.debug(f"DB: Getting last visit for patient {patient_id}")

        try:
            cursor = self.conn.cursor()

            query = """
                SELECT MAX(visit_date) as last_visit
                FROM (
                    SELECT created_at as visit_date
                    FROM doctor_notes
                    WHERE patient_id = ?
                    UNION ALL
                    SELECT created_at as visit_date
                    FROM patient_photos
                    WHERE patient_id = ?
                ) visits
            """

            cursor.execute(query, (patient_id, patient_id))
            result = cursor.fetchone()

            if result and result['last_visit']:
                logger.debug(f"DB: Found last visit date: {result['last_visit']}")
                return datetime.strptime(result['last_visit'], '%Y-%m-%d %H:%M:%S')

            logger.debug("DB: No visits found")
            return None

        except Exception as e:
            logger.error(f"DB: Error getting last visit: {e}")
            return None

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

    def search_patients(self, search_term):
        """Search patients by name or phone number"""
        logger.debug(f"DB: Searching for patients with term: {search_term}")

        try:
            cursor = self.conn.cursor()
            search_pattern = f"%{search_term}%"

            query = """
                SELECT id, name, phone, email, address, medical_history, created_at
                FROM patients 
                WHERE name LIKE ? OR phone LIKE ?
                ORDER BY name
            """

            cursor.execute(query, (search_pattern, search_pattern))
            rows = cursor.fetchall()
            logger.debug(f"DB: Found {len(rows)} matching patients")

            # Convert rows to list of Patient-like objects
            patients = []
            for row in rows:
                row_dict = dict(row)  # Convert sqlite3.Row to dictionary first
                patient = type('Patient', (), {
                    'id': row_dict['id'],
                    'name': row_dict['name'],
                    'phone': row_dict['phone'],
                    'email': row_dict['email'],
                    'address': row_dict.get('address'),
                    'medical_history': row_dict.get('medical_history'),
                    'created_at': row_dict.get('created_at')
                })
                logger.debug(f"DB: Found patient: {patient.name}")
                patients.append(patient)

            return patients

        except Exception as e:
            logger.error(f"DB: Error searching patients: {e}")
            return []

    def get_patient_by_name(self, name):
        """Get patient by exact name"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM patients WHERE name = ?', (name,))
            row = cursor.fetchone()
            if row:
                # Convert row to dictionary
                row_dict = dict(row)
                # Return dictionary directly
                return row_dict
            return None
        except Exception as e:
            logger.error(f"Error getting patient by name: {e}")
            return None

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

    def get_patient_notes(self, patient_id):
        """Get the most recent notes for a patient"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM doctor_notes
                WHERE patient_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (patient_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting patient notes: {e}")
            return None

    def save_doctor_notes(self, notes_data):
        """Save doctor's notes"""
        try:
            cursor = self.conn.cursor()
            notes_data['id'] = str(uuid.uuid4())

            cursor.execute('''
                INSERT INTO doctor_notes (
                    id, patient_id, medical_history, progress_notes,
                    recommendations, next_steps, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                notes_data['id'],
                notes_data['patient_id'],
                notes_data.get('medical_history', ''),
                notes_data.get('progress_notes', ''),
                notes_data.get('recommendations', ''),
                notes_data.get('next_steps', ''),
                notes_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            ))

            self.conn.commit()

        except Exception as e:
            logger.error(f"Error saving doctor notes: {e}")
            self.conn.rollback()
            raise

    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()
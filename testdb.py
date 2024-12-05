import logging
from app.database.db_manager import DatabaseManager
from app.database.model import Patient
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_database():
    try:
        logger.debug("Initializing database connection...")
        db = DatabaseManager()

        # Test creating a patient
        test_patient = Patient(
            id="",
            name="Test Patient",
            phone="1234567890",
            email="test@example.com",
            address="Test Address",
            created_at=datetime.now()
        )

        logger.debug("Adding test patient...")
        patient_id = db.add_patient(test_patient)
        logger.debug(f"Test patient added with ID: {patient_id}")

        # Test retrieving the patient
        logger.debug("Retrieving test patient...")
        retrieved_patient = db.get_patient(patient_id)
        logger.debug(f"Retrieved patient: {retrieved_patient}")

        return True

    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_database()
    print(f"Database test {'succeeded' if success else 'failed'}")
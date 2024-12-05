from pathlib import Path
import sys
import logging
from config import Config

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def setup_environment():
    """Setup the environment before running the application"""
    try:
        # Ensure all required directories exist
        logger.debug("Creating required directories...")
        Config.ensure_directories()

        # Add project root to Python path
        project_root = Path(__file__).resolve().parent
        sys.path.append(str(project_root))
        logger.debug(f"Added {project_root} to Python path")

    except Exception as e:
        logger.error(f"Error in setup_environment: {e}")
        raise


def main():
    """Main entry point of the application"""
    try:
        # Setup environment
        logger.debug("Setting up environment...")
        setup_environment()

        # Import here after environment setup
        logger.debug("Importing BeautyClinicPOS...")
        from app.gui.main_window import BeautyClinicPOS

        # Initialize and run the application
        logger.debug("Initializing BeautyClinicPOS...")
        app = BeautyClinicPOS()
        logger.debug("Starting main loop...")
        app.root.mainloop()

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    try:
        logger.debug("Starting application...")
        main()
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        raise
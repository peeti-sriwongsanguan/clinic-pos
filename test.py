import sys
from pathlib import Path
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    try:
        # Add the project root directory to Python path
        project_root = Path(__file__).resolve().parent
        sys.path.append(str(project_root))
        logger.debug(f"Project root added to path: {project_root}")

        logger.debug("Importing BeautyClinicPOS...")
        from app.gui.main_window import BeautyClinicPOS

        logger.debug("Creating BeautyClinicPOS instance...")
        app = BeautyClinicPOS()

        logger.debug("Starting mainloop...")
        app.root.mainloop()

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
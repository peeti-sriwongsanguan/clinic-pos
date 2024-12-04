from pathlib import Path
import sys
from config import Config


def setup_environment():
    """Setup the environment before running the application"""
    # Ensure all required directories exist
    Config.ensure_directories()

    # Add project root to Python path
    project_root = Path(__file__).resolve().parent
    sys.path.append(str(project_root))


def main():
    """Main entry point of the application"""
    # Setup environment
    setup_environment()

    # Import here after environment setup
    from app.gui.main_window import BeautyClinicPOS
    # from app.gui.theme_config import ThemeConfig

    # Initialize and run the application
    app = BeautyClinicPOS()
    app.root.mainloop()


if __name__ == "__main__":
    main()
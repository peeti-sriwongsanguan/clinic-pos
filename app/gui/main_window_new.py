import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import logging

from app.gui.theme_config import ThemeConfig
from app.utils.language_manager import LanguageManager
from app.database.db_manager import DatabaseManager

# Import tab classes
from app.gui.tabs.doctor_notes_tab import DoctorNotesTab
from app.gui.tabs.patients_tab import PatientsTab
# from app.gui.tabs.reports_tab import ReportsTab

logger = logging.getLogger(__name__)

class BeautyClinicPOS:
    def __init__(self):
        logger.debug("Initializing BeautyClinicPOS...")

        # Initialize database and language manager first
        try:
            logger.debug("Initializing database connection...")
            self.db = DatabaseManager()
            self.lang = LanguageManager(self.db)
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            messagebox.showerror(
                "Database Error",
                "Failed to connect to database. The application will run with limited functionality."
            )
            self.db = None

        # Create main window
        logger.debug("Creating root window...")
        self.root = tk.Tk()

        try:
            # Setup window appearance
            self.setup_window()
            self.create_styles()
            self.setup_header()
            self.setup_branding()
            self.setup_gui()

            logger.debug("Successfully initialized BeautyClinicPOS")
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            raise

    def setup_window(self):
        """Configure main window settings"""
        self.root.title("Beauty Clinic POS")
        self.root.geometry("1280x800")
        self.root.configure(bg=ThemeConfig.PRIMARY_PINK)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

    def create_styles(self):
        """Create ttk styles for the application"""
        style = ttk.Style()

        # Main theme
        style.configure(
            "Custom.TFrame",
            background=ThemeConfig.PRIMARY_PINK
        )

        # Header styles
        style.configure(
            "Header.TFrame",
            background=ThemeConfig.WHITE
        )

        style.configure(
            "ClinicName.TLabel",
            background=ThemeConfig.WHITE,
            font=ThemeConfig.TITLE_FONT,
            foreground=ThemeConfig.DARK_PINK
        )

        # Button style
        style.configure(
            "Custom.TButton",
            background=ThemeConfig.SECONDARY_PINK,
            foreground=ThemeConfig.WHITE,
            font=ThemeConfig.MAIN_FONT,
            padding=10
        )

        # Label style
        style.configure(
            "Custom.TLabel",
            background=ThemeConfig.PRIMARY_PINK,
            font=ThemeConfig.MAIN_FONT
        )

    def setup_header(self):
        """Setup header with logo and language selection"""
        header_frame = ttk.Frame(self.root, style='Header.TFrame')
        header_frame.pack(fill='x', padx=10, pady=5)

        # Left side - Logo
        left_frame = ttk.Frame(header_frame)
        left_frame.pack(side='left', fill='y')



        try:
            logo_path = os.path.join('static', 'assets', 'logo.jpeg')
            logo_img = Image.open(logo_path)
            logo_height = 60
            aspect_ratio = logo_img.width / logo_img.height
            logo_width = int(logo_height * aspect_ratio)
            logo_img = logo_img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

            self.logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = ttk.Label(left_frame, image=self.logo_photo, background=ThemeConfig.WHITE)
            logo_label.pack(side='left', padx=5)
        except Exception as e:
            logger.error(f"Error loading logo: {e}")

        # Right side - Language selection
        right_frame = ttk.Frame(header_frame)
        right_frame.pack(side='right', fill='y')

        lang_frame = ttk.Frame(right_frame)
        lang_frame.pack(side='right', padx=10)

        self.lang_label = ttk.Label(
            lang_frame,
            text=self.lang.get_text("language"),
            style='Header.TLabel'
        )
        self.lang_label.pack(side='left')

        # Language dropdown with proper values
        self.language_var = tk.StringVar(value=self.lang.current_language)  # Use current language
        lang_options = {
            'en': 'English',
            'th': 'ไทย'
        }

        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.language_var,
            values=list(lang_options.keys()),
            state='readonly',
            width=10
        )
        lang_combo.pack(side='left', padx=5)
        lang_combo.bind('<<ComboboxSelected>>', self.change_language)

    def setup_branding(self):
        """Setup clinic branding in header"""
        # Create header frame
        self.header_frame = tk.Frame(
            self.root,
            bg=ThemeConfig.WHITE,
            height=100
        )
        self.header_frame.pack(fill='x', pady=0)

        # Load and display logo
        try:
            logo_path = os.path.join('static', 'assets', 'logo.jpeg')
            logo_img = Image.open(logo_path)
            logo_height = 80
            aspect_ratio = logo_img.width / logo_img.height
            logo_width = int(logo_height * aspect_ratio)
            logo_img = logo_img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

            self.logo_photo = ImageTk.PhotoImage(logo_img)
            self.logo_label = tk.Label(
                self.header_frame,
                image=self.logo_photo,
                bg=ThemeConfig.WHITE
            )
            self.logo_label.pack(side='left', padx=20, pady=10)

            # Add clinic name next to logo
            clinic_name = tk.Label(
                self.header_frame,
                text="Wellness by BFF",
                font=ThemeConfig.TITLE_FONT,
                bg=ThemeConfig.WHITE,
                fg=ThemeConfig.DARK_PINK
            )
            clinic_name.pack(side='left', padx=10)

        except Exception as e:
            logger.error(f"Error loading logo: {e}")
            self.logo_label = tk.Label(
                self.header_frame,
                text="WELLNESS BY BFF",
                font=ThemeConfig.TITLE_FONT,
                bg=ThemeConfig.WHITE,
                fg=ThemeConfig.DARK_PINK
            )
            self.logo_label.pack(side='left', padx=20, pady=10)

    def setup_gui(self):
        """Setup main GUI components and tabs"""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)

        # Create tab frames
        self.patients_frame = ttk.Frame(self.notebook)
        self.doctor_notes_frame = ttk.Frame(self.notebook)

        # Initialize tab contents with proper class instances
        self.patients = PatientsTab(self.patients_frame, self.db, self.lang)
        self.doctor_notes = DoctorNotesTab(self.doctor_notes_frame, self.db, self.lang)

        # Add tabs with proper references
        self.notebook.add(self.patients_frame, text=self.lang.get_text("patients"))
        self.notebook.add(self.doctor_notes_frame, text=self.lang.get_text("doctor_notes"))

        # self.reports = ReportsTab(self.reports_tab, self.db, self.lang)
        # Store references to tab indices
        self.tab_indices = {
            'patients': self.notebook.add(self.patients_frame, text=self.lang.get_text("patients")),
            'doctor_notes': self.notebook.add(self.doctor_notes_frame, text=self.lang.get_text("doctor_notes"))
        }

    def change_language(self, event=None):
        """Change the application language"""
        try:
            selected_lang = self.language_var.get()
            logger.debug(f"Changing language to: {selected_lang}")

            # Check if language is supported before changing
            if selected_lang in ['en', 'th']:
                self.lang.set_language(selected_lang)
                self.update_ui_texts()
                logger.debug(f"Successfully changed language to: {selected_lang}")
            else:
                logger.error(f"Unsupported language selected: {selected_lang}")
                messagebox.showerror(
                    "Error",
                    "Selected language is not supported."
                )
                # Reset to current language
                self.language_var.set(self.lang.current_language)

        except Exception as e:
            logger.error(f"Error changing language: {e}", exc_info=True)
            messagebox.showerror(
                "Error",
                "Failed to change language. Please try again."
            )
            # Reset to current language
            self.language_var.set(self.lang.current_language)

    def set_language(self, language_code: str):
        """Change current language"""
        if language_code in self.translations:
            self.current_language = language_code
            return True
        else:
            logging.error(f"Unsupported language: {language_code}")
            return False

    def update_ui_texts(self):
        """Update UI texts when language changes"""
        try:
            # Update window title
            self.root.title(self.lang.get_text("app_name"))

            # Update notebook tab texts
            if hasattr(self, 'notebook'):
                self.notebook.tab(self.patients_frame, text=self.lang.get_text("patients"))
                self.notebook.tab(self.doctor_notes_frame, text=self.lang.get_text("doctor_notes"))

            # Update clinic name
            if hasattr(self, 'clinic_name'):
                self.clinic_name.configure(text=self.lang.get_text("clinic_name"))

            # Update language label
            if hasattr(self, 'lang_label'):
                self.lang_label.configure(text=self.lang.get_text("language"))

            # Update patients tab
            if hasattr(self, 'patients'):
                if hasattr(self.patients, 'update_ui_text'):
                    self.patients.update_ui_text()

            # Update doctor notes tab
            if hasattr(self, 'doctor_notes'):
                if hasattr(self.doctor_notes, 'refresh_notes'):
                    self.doctor_notes.refresh_notes()

            logger.debug("Successfully updated UI texts for language change")

        except Exception as e:
            logger.error(f"Error updating UI texts: {e}", exc_info=True)


    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = BeautyClinicPOS()
    app.root.mainloop()
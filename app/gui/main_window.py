import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
from datetime import datetime
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from app.gui.theme_config import ThemeConfig
from app.utils.language_manager import LanguageManager
from app.utils.invoice_generator import InvoiceGenerator
from app.database.db_manager import DatabaseManager
from app.database.model import Patient, Service, Transaction, TransactionItem
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
            messagebox.showerror("Database Error",
                                 "Failed to connect to database. The application will run with limited functionality.")
            self.db = None

        # Create main window
        logger.debug("Creating root window...")
        self.root = tk.Tk()

        try:
            # Initialize other components
            self.invoice_generator = InvoiceGenerator()

            # Setup window appearance
            self.setup_window()
            self.create_styles()

            # Setup UI components in correct order
            self.setup_header()
            self.setup_branding()
            self.setup_gui()

            # Initialize state variables
            self.current_patient = None
            self.cart_items = []

            logger.debug("Successfully initialized BeautyClinicPOS")
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            raise

    def setup_patient_search_frame(self):
        """Setup the patient search frame with enhanced functionality"""
        search_frame = ttk.Frame(self.patient_frame)
        search_frame.pack(fill='x', padx=5, pady=5)

        # Search entry
        ttk.Label(search_frame, text="Search Patient:").pack(side='left', padx=5)
        self.patient_search_var = tk.StringVar()
        self.patient_search_var.trace('w', self.on_patient_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.patient_search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Add New Patient button
        add_patient_btn = ttk.Button(
            search_frame,
            text="Add New Patient",
            command=self.show_add_patient_form,
            style="Custom.TButton"
        )
        add_patient_btn.pack(side='right', padx=5)

    def on_patient_search(self, *args):
        """Handle patient search with improved feedback"""
        search_term = self.patient_search_var.get()

        # Clear previous results
        self.clear_patient_results()

        if len(search_term) < 2:
            self.show_search_message("Enter at least 2 characters to search")
            return

        try:
            patients = self.db.search_patients(search_term)
            if patients:
                self.display_patient_results(patients)
            else:
                self.show_no_results_found()
        except Exception as e:
            logger.error(f"Search error: {e}")
            self.show_search_message("An error occurred during search", "error")

    def show_add_patient_form(self):
        """Show the add patient form in a new window"""
        self.add_patient_window = tk.Toplevel(self.root)
        self.add_patient_window.title("Add New Patient")
        self.add_patient_window.geometry("600x800")

        # Make it modal
        self.add_patient_window.transient(self.root)
        self.add_patient_window.grab_set()

        # Create a frame with pink theme
        main_frame = ttk.Frame(self.add_patient_window, style='Custom.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Patient Registration Form",
            font=("Helvetica", 16, "bold"),
            style="Custom.TLabel"
        )
        title_label.pack(pady=(0, 20))

        # Form fields
        fields = [
            ("Name*:", "name"),
            ("Phone*:", "phone"),
            ("Email:", "email"),
            ("Address:", "address"),
            ("Birth Date:", "birth_date"),
            ("Gender:", "gender"),
            ("Emergency Contact:", "emergency_contact")
        ]

        self.patient_form_vars = {}

        for label_text, field_name in fields:
            frame = ttk.Frame(main_frame)
            frame.pack(fill='x', pady=5)

            ttk.Label(
                frame,
                text=label_text,
                style="Custom.TLabel"
            ).pack(side='left', width=120)

            if field_name == "gender":
                var = tk.StringVar()
                combo = ttk.Combobox(
                    frame,
                    textvariable=var,
                    values=["Female", "Male", "Other"],
                    state="readonly"
                )
                combo.pack(side='left', fill='x', expand=True)
                self.patient_form_vars[field_name] = var
            elif field_name == "birth_date":
                var = tk.StringVar()
                entry = ttk.Entry(frame, textvariable=var)
                entry.pack(side='left', fill='x', expand=True)
                entry.insert(0, "YYYY-MM-DD")
                entry.bind('<FocusIn>', lambda e: self.on_date_focus_in(e, entry))
                self.patient_form_vars[field_name] = var
            else:
                var = tk.StringVar()
                ttk.Entry(
                    frame,
                    textvariable=var
                ).pack(side='left', fill='x', expand=True)
                self.patient_form_vars[field_name] = var

        # Medical History
        ttk.Label(
            main_frame,
            text="Medical History:",
            style="Custom.TLabel"
        ).pack(anchor='w', pady=(10, 5))

        self.medical_history_text = tk.Text(main_frame, height=4)
        self.medical_history_text.pack(fill='x', pady=5)

        # Notes
        ttk.Label(
            main_frame,
            text="Notes:",
            style="Custom.TLabel"
        ).pack(anchor='w', pady=(10, 5))

        self.notes_text = tk.Text(main_frame, height=4)
        self.notes_text.pack(fill='x', pady=5)

        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', pady=20)

        ttk.Button(
            buttons_frame,
            text="Save",
            command=self.save_new_patient,
            style="Custom.TButton"
        ).pack(side='right', padx=5)

        ttk.Button(
            buttons_frame,
            text="Cancel",
            command=self.add_patient_window.destroy,
            style="Custom.TButton"
        ).pack(side='right', padx=5)

        # Required fields note
        ttk.Label(
            main_frame,
            text="* Required fields",
            font=("Helvetica", 10, "italic"),
            style="Custom.TLabel"
        ).pack(pady=10)

    def save_new_patient(self):
        """Save the new patient data"""
        # Validate required fields
        required_fields = ['name', 'phone']
        for field in required_fields:
            if not self.patient_form_vars[field].get().strip():
                messagebox.showerror(
                    "Validation Error",
                    f"{field.capitalize()} is required!"
                )
                return

        try:
            # Create patient object
            patient_data = {
                'name': self.patient_form_vars['name'].get().strip(),
                'phone': self.patient_form_vars['phone'].get().strip(),
                'email': self.patient_form_vars['email'].get().strip(),
                'address': self.patient_form_vars['address'].get().strip(),
                'birth_date': self.patient_form_vars['birth_date'].get().strip(),
                'gender': self.patient_form_vars['gender'].get(),
                'emergency_contact': self.patient_form_vars['emergency_contact'].get().strip(),
                'medical_history': self.medical_history_text.get('1.0', tk.END).strip(),
                'notes': self.notes_text.get('1.0', tk.END).strip(),
                'created_at': datetime.now()
            }

            # Save to database
            patient_id = self.db.add_patient(Patient(**patient_data))

            # Show success message
            messagebox.showinfo(
                "Success",
                "Patient added successfully!"
            )

            # Close the form and refresh search
            self.add_patient_window.destroy()
            self.patient_search_var.set(patient_data['name'])  # Trigger search with new patient's name

        except Exception as e:
            logger.error(f"Error saving patient: {e}")
            messagebox.showerror(
                "Error",
                "An error occurred while saving the patient information."
            )

    def on_date_focus_in(self, event, entry):
        """Clear the date placeholder when entry is focused"""
        if entry.get() == "YYYY-MM-DD":
            entry.delete(0, tk.END)

    def clear_patient_results(self):
        """Clear the patient search results"""
        for widget in self.patient_info_frame.winfo_children():
            widget.destroy()

    def show_search_message(self, message, message_type="info"):
        """Show a message in the patient results area"""
        label = ttk.Label(
            self.patient_info_frame,
            text=message,
            style="Custom.TLabel"
        )
        label.pack(pady=10)

    def show_no_results_found(self):
        """Show no results message with add patient suggestion"""
        frame = ttk.Frame(self.patient_info_frame)
        frame.pack(fill='x', pady=10)

        ttk.Label(
            frame,
            text="No patients found.",
            style="Custom.TLabel"
        ).pack(pady=(0, 5))

        ttk.Button(
            frame,
            text="Add New Patient",
            command=self.show_add_patient_form,
            style="Custom.TButton"
        ).pack()

    def display_patient_results(self, patients):
        """Display the found patients as clickable buttons"""
        for patient in patients:
            patient_frame = ttk.Frame(self.patient_info_frame)
            patient_frame.pack(fill='x', pady=2)

            # Patient info button
            ttk.Button(
                patient_frame,
                text=f"{patient.name} - {patient.phone}",
                command=lambda p=patient: self.select_patient(p),
                style="Custom.TButton"
            ).pack(side='left', fill='x', expand=True)

            # Edit button
            ttk.Button(
                patient_frame,
                text="Edit",
                command=lambda p=patient: self.edit_patient(p),
                style="Custom.TButton"
            ).pack(side='right', padx=5)









    def update_patient_search_results(self, patients):
        """Update the patient search results display"""
        try:
            # Clear previous results
            for widget in self.patient_info_frame.winfo_children():
                widget.destroy()

            # Display results
            for patient in patients:
                patient_button = ttk.Button(
                    self.patient_info_frame,
                    text=f"{patient.name} - {patient.phone}",
                    command=lambda p=patient: self.select_patient(p)
                )
                patient_button.pack(fill='x', padx=5, pady=2)
        except Exception as e:
            logger.error(f"Error updating patient search results: {e}")

    def select_patient(self, patient):
        """Handle patient selection"""
        try:
            self.current_patient = patient
            # Update UI to show selected patient
            self.update_patient_display()
        except Exception as e:
            logger.error(f"Error selecting patient: {e}")
            messagebox.showerror("Error",
                                 "An error occurred while selecting the patient.")

    def update_patient_display(self):
        """Update the display with selected patient information"""
        if not self.current_patient:
            return

        try:
            # Clear previous info
            for widget in self.patient_info_frame.winfo_children():
                widget.destroy()

            # Show patient info
            info_text = f"""
            Name: {self.current_patient.name}
            Phone: {self.current_patient.phone}
            Email: {self.current_patient.email or 'N/A'}
            """

            ttk.Label(
                self.patient_info_frame,
                text=info_text,
                style="Custom.TLabel"
            ).pack(padx=5, pady=5)
        except Exception as e:
            logger.error(f"Error updating patient display: {e}")

    def setup_window(self):
        self.root.title("Beauty Clinic POS")
        self.root.geometry("1280x800")
        self.root.configure(bg=ThemeConfig.PRIMARY_PINK)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Add a test label to see if window appears
        test_label = tk.Label(self.root, text="Beauty Clinic POS is starting...", font=('Helvetica', 16))
        test_label.pack(pady=20)


    def setup_branding(self):
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
            print(f"Error loading logo: {e}")
            self.logo_label = tk.Label(
                self.header_frame,
                text="WELLNESS BY BFF",
                font=ThemeConfig.TITLE_FONT,
                bg=ThemeConfig.WHITE,
                fg=ThemeConfig.DARK_PINK
            )
            self.logo_label.pack(side='left', padx=20, pady=10)

    def create_styles(self):
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

        style.configure(
            "Header.TLabel",
            background=ThemeConfig.WHITE,
            font=ThemeConfig.MAIN_FONT
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

        # Entry style
        style.configure(
            "Custom.TEntry",
            fieldbackground=ThemeConfig.WHITE,
            font=ThemeConfig.MAIN_FONT
        )

    def setup_header(self):
        """Setup header with logo and language selection"""
        header_frame = ttk.Frame(self.root, style='Header.TFrame')
        header_frame.pack(fill='x', padx=10, pady=5)

        # Left side - Logo and clinic name
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

        # Clinic name
        clinic_label = ttk.Label(
            left_frame,
            text="Wellness by BFF",
            style='ClinicName.TLabel'
        )
        clinic_label.pack(side='left', padx=10)

        # Right side - Controls
        right_frame = ttk.Frame(header_frame)
        right_frame.pack(side='right', fill='y')

        # Language selection
        lang_frame = ttk.Frame(right_frame)
        lang_frame.pack(side='right', padx=10)

        ttk.Label(
            lang_frame,
            text=self.lang.get_text("language"),
            style='Header.TLabel'
        ).pack(side='left')

        self.lang_var = tk.StringVar(value='en')
        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=['en', 'th'],
            state='readonly',
            width=10
        )
        lang_combo.pack(side='left', padx=5)
        lang_combo.bind('<<ComboboxSelected>>', self.change_language)

        # User info/login
        user_frame = ttk.Frame(right_frame)
        user_frame.pack(side='right', padx=10)

    def change_language(self, event=None):
        """Handle language change"""
        new_lang = self.lang_var.get()
        self.lang.set_language(new_lang)
        self.update_ui_texts()

    def update_ui_texts(self):
        """Update all UI texts after language change"""
        # Update tab texts
        tab_texts = {
            0: "pos",
            1: "patients",
            2: "treatments",
            3: "doctor_notes",
            4: "services",
            5: "appointments",
            6: "reports",
            7: "settings"
        }

        for index, text_key in tab_texts.items():
            self.notebook.tab(index, text=self.lang.get_text(text_key))

        # Update other UI elements
        self.refresh_all_displays()

    def refresh_all_displays(self):
        """Refresh all displays after language change"""
        if hasattr(self, 'current_patient') and self.current_patient:
            self.update_patient_display()
        self.update_cart_display()
        self.refresh_patient_list()
        self.refresh_services_list()

    def setup_gui(self):
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)

        # Create different tabs
        self.pos_tab = ttk.Frame(self.notebook)
        self.patients_tab = ttk.Frame(self.notebook)
        self.treatments_tab = ttk.Frame(self.notebook)
        self.doctor_notes_tab = ttk.Frame(self.notebook)
        self.services_tab = ttk.Frame(self.notebook)
        self.appointments_tab = ttk.Frame(self.notebook)
        self.reports_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)

        # Add tabs with language support
        self.notebook.add(self.pos_tab, text=self.lang.get_text("pos"))
        self.notebook.add(self.patients_tab, text=self.lang.get_text("patients"))
        self.notebook.add(self.treatments_tab, text=self.lang.get_text("treatments"))
        self.notebook.add(self.doctor_notes_tab, text=self.lang.get_text("doctor_notes"))
        self.notebook.add(self.services_tab, text=self.lang.get_text("services"))
        self.notebook.add(self.appointments_tab, text=self.lang.get_text("appointments"))
        self.notebook.add(self.reports_tab, text=self.lang.get_text("reports"))
        self.notebook.add(self.settings_tab, text=self.lang.get_text("settings"))

        # Setup each tab
        self.setup_pos_tab()
        self.setup_patients_tab()
        self.setup_treatments_tab()
        self.setup_doctor_notes_tab()
        self.setup_services_tab()
        self.setup_appointments_tab()
        self.setup_reports_tab()
        self.setup_settings_tab()

    def setup_pos_tab(self):
        # Left frame for patient selection and services
        left_frame = ttk.Frame(self.pos_tab)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        # Patient selection
        patient_frame = ttk.LabelFrame(left_frame, text="Patient Information")
        patient_frame.pack(fill='x', padx=5, pady=5)

        # Patient search
        search_frame = ttk.Frame(patient_frame)
        search_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(search_frame, text="Search Patient:").pack(side='left', padx=5)
        self.patient_search_var = tk.StringVar()
        self.patient_search_var.trace('w', self.on_patient_search)
        patient_search = ttk.Entry(search_frame, textvariable=self.patient_search_var)
        patient_search.pack(side='left', fill='x', expand=True, padx=5)

        # Patient info display
        self.patient_info_frame = ttk.Frame(patient_frame)
        self.patient_info_frame.pack(fill='x', padx=5, pady=5)

        # Services selection
        services_frame = ttk.LabelFrame(left_frame, text="Services")
        services_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Service categories
        categories_frame = ttk.Frame(services_frame)
        categories_frame.pack(fill='x', padx=5, pady=5)

        # Service list
        self.services_list = ttk.Treeview(services_frame, columns=('name', 'price', 'duration'),
                                          show='headings')
        self.services_list.heading('name', text='Service Name')
        self.services_list.heading('price', text='Price')
        self.services_list.heading('duration', text='Duration')
        self.services_list.pack(fill='both', expand=True, padx=5, pady=5)

        # Right frame for cart and payment
        right_frame = ttk.Frame(self.pos_tab)
        right_frame.pack(side='right', fill='both', padx=5, pady=5)

        # Cart
        cart_frame = ttk.LabelFrame(right_frame, text="Cart")
        cart_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.cart_list = ttk.Treeview(cart_frame,
                                      columns=('service', 'quantity', 'price', 'total'),
                                      show='headings')
        self.cart_list.heading('service', text='Service')
        self.cart_list.heading('quantity', text='Qty')
        self.cart_list.heading('price', text='Price')
        self.cart_list.heading('total', text='Total')
        self.cart_list.pack(fill='both', expand=True, padx=5, pady=5)

        # Cart totals
        totals_frame = ttk.Frame(cart_frame)
        totals_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(totals_frame, text="Subtotal:").pack(side='left')
        self.subtotal_var = tk.StringVar(value="฿0.00")
        ttk.Label(totals_frame, textvariable=self.subtotal_var).pack(side='left', padx=5)

        # Payment
        payment_frame = ttk.LabelFrame(right_frame, text="Payment")
        payment_frame.pack(fill='x', padx=5, pady=5)

        # Payment method selection
        ttk.Label(payment_frame, text="Payment Method:").pack(padx=5, pady=2)
        self.payment_method = ttk.Combobox(payment_frame,
                                           values=['Cash', 'Credit Card', 'Transfer'])
        self.payment_method.pack(fill='x', padx=5, pady=2)

        # Process payment button
        ttk.Button(payment_frame, text="Process Payment",
                   command=self.process_payment).pack(fill='x', padx=5, pady=5)

    def setup_patients_tab(self):
        # Search frame
        search_frame = ttk.Frame(self.patients_tab)
        search_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side='left', padx=5)
        self.patient_list_search = ttk.Entry(search_frame)
        self.patient_list_search.pack(side='left', fill='x', expand=True, padx=5)

        # Patient list
        self.patient_list = ttk.Treeview(self.patients_tab,
                                         columns=('name', 'phone', 'email'),
                                         show='headings')
        self.patient_list.heading('name', text='Name')
        self.patient_list.heading('phone', text='Phone')
        self.patient_list.heading('email', text='Email')
        self.patient_list.pack(fill='both', expand=True, padx=10, pady=5)

        # Buttons frame
        buttons_frame = ttk.Frame(self.patients_tab)
        buttons_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(buttons_frame, text="Add Patient",
                   command=self.show_add_patient_dialog).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Edit Patient",
                   command=self.show_edit_patient_dialog).pack(side='left', padx=5)

    def setup_services_tab(self):
        # Services list
        self.services_tree = ttk.Treeview(self.services_tab,
                                          columns=('name', 'price', 'duration', 'category'),
                                          show='headings')
        self.services_tree.heading('name', text='Service Name')
        self.services_tree.heading('price', text='Price')
        self.services_tree.heading('duration', text='Duration')
        self.services_tree.heading('category', text='Category')
        self.services_tree.pack(fill='both', expand=True, padx=10, pady=5)

        # Buttons
        buttons_frame = ttk.Frame(self.services_tab)
        buttons_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(buttons_frame, text="Add Service",
                   command=self.show_add_service_dialog).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Edit Service",
                   command=self.show_edit_service_dialog).pack(side='left', padx=5)

    def setup_appointments_tab(self):
        # Calendar view
        calendar_frame = ttk.Frame(self.appointments_tab)
        calendar_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Appointments list
        self.appointments_list = ttk.Treeview(self.appointments_tab,
                                              columns=('time', 'patient', 'service', 'status'),
                                              show='headings')
        self.appointments_list.heading('time', text='Time')
        self.appointments_list.heading('patient', text='Patient')
        self.appointments_list.heading('service', text='Service')
        self.appointments_list.heading('status', text='Status')
        self.appointments_list.pack(fill='both', expand=True, padx=10, pady=5)

    def setup_reports_tab(self):
        # Report types selection
        report_types = ttk.LabelFrame(self.reports_tab, text="Report Type")
        report_types.pack(fill='x', padx=10, pady=5)

        self.report_type = tk.StringVar(value="daily")
        ttk.Radiobutton(report_types, text="Daily", variable=self.report_type,
                        value="daily").pack(side='left', padx=5)
        ttk.Radiobutton(report_types, text="Monthly", variable=self.report_type,
                        value="monthly").pack(side='left', padx=5)
        ttk.Radiobutton(report_types, text="Custom", variable=self.report_type,
                        value="custom").pack(side='left', padx=5)

        # Date selection
        dates_frame = ttk.Frame(self.reports_tab)
        dates_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(dates_frame, text="Generate Report",
                   command=self.generate_report).pack(side='right', padx=5)

    # Event handlers
    def on_patient_search(self, *args):
        search_term = self.patient_search_var.get()
        if len(search_term) >= 3:
            patients = self.db.search_patients(search_term)
            # Update patient search results display

    def process_payment(self):
        if not self.current_patient or not self.cart_items:
            messagebox.showerror("Error", "Please select a patient and add services to cart")
            return

        try:
            # Create transaction
            transaction = Transaction(
                id="",  # Will be generated by DB
                patient_id=self.current_patient.id,
                total_amount=self.calculate_total(),
                payment_method=self.payment_method.get(),
                transaction_date=datetime.now(),
                status="completed",
                items=self.cart_items
            )

            # Save to database
            transaction_id = self.db.create_transaction(transaction)

            # Generate invoice
            self.generate_invoice(transaction_id)

            # Clear cart
            self.clear_cart()

            messagebox.showinfo("Success", "Payment processed successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Error processing payment: {str(e)}")

    def show_add_patient_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Patient")
        dialog.geometry("400x500")
        dialog.transient(self.root)

        # Patient information fields
        ttk.Label(dialog, text="Name:").pack(padx=5, pady=2)
        name_entry = ttk.Entry(dialog)
        name_entry.pack(fill='x', padx=5, pady=2)

        ttk.Label(dialog, text="Phone:").pack(padx=5, pady=2)
        phone_entry = ttk.Entry(dialog)
        phone_entry.pack(fill='x', padx=5, pady=2)

        ttk.Label(dialog, text="Email:").pack(padx=5, pady=2)
        email_entry = ttk.Entry(dialog)
        email_entry.pack(fill='x', padx=5, pady=2)

        ttk.Label(dialog, text="Address:").pack(padx=5, pady=2)
        address_entry = ttk.Entry(dialog)
        address_entry.pack(fill='x', padx=5, pady=2)

        ttk.Label(dialog, text="Medical History:").pack(padx=5, pady=2)
        medical_history = tk.Text(dialog, height=4)
        medical_history.pack(fill='x', padx=5, pady=2)

        def save_patient():
            try:
                patient = Patient(
                    id="",  # Will be generated by DB
                    name=name_entry.get(),
                    phone=phone_entry.get(),
                    email=email_entry.get(),
                    address=address_entry.get(),
                    created_at=datetime.now(),
                    medical_history=medical_history.get("1.0", tk.END).strip()
                )

                self.db.add_patient(patient)
                messagebox.showinfo("Success", "Patient added successfully")
                dialog.destroy()
                self.refresh_patient_list()

            except Exception as e:
                messagebox.showerror("Error", f"Error adding patient: {str(e)}")

        ttk.Button(dialog, text="Save", command=save_patient).pack(pady=10)

    def show_edit_patient_dialog(self):
        selection = self.patient_list.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a patient to edit")
            return

        patient_id = self.patient_list.item(selection[0])['values'][0]
        patient = self.db.get_patient(patient_id)

        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Patient")
        dialog.geometry("400x500")
        dialog.transient(self.root)

        # Populate fields with patient data
        # Similar to add_patient_dialog but with pre-filled values

    def show_add_service_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Service")
        dialog.geometry("400x400")
        dialog.transient(self.root)

        ttk.Label(dialog, text="Service Name:").pack(padx=5, pady=2)
        name_entry = ttk.Entry(dialog)
        name_entry.pack(fill='x', padx=5, pady=2)

        ttk.Label(dialog, text="Price:").pack(padx=5, pady=2)
        price_entry = ttk.Entry(dialog)
        price_entry.pack(fill='x', padx=5, pady=2)

        ttk.Label(dialog, text="Duration (minutes):").pack(padx=5, pady=2)
        duration_entry = ttk.Entry(dialog)
        duration_entry.pack(fill='x', padx=5, pady=2)

        ttk.Label(dialog, text="Category:").pack(padx=5, pady=2)
        category_combobox = ttk.Combobox(dialog, values=[
            "Anti-Aging",
            "Facial Treatment",
            "Body Treatment",
            "Skin Care"
        ])
        category_combobox.pack(fill='x', padx=5, pady=2)

        ttk.Label(dialog, text="Description:").pack(padx=5, pady=2)
        description_text = tk.Text(dialog, height=4)
        description_text.pack(fill='x', padx=5, pady=2)

        def save_service():
            try:
                service = Service(
                    id="",  # Will be generated by DB
                    name=name_entry.get(),
                    price=Decimal(price_entry.get()),
                    duration=int(duration_entry.get()),
                    category=category_combobox.get(),
                    description=description_text.get("1.0", tk.END).strip()
                )

                self.db.add_service(service)
                messagebox.showinfo("Success", "Service added successfully")
                dialog.destroy()
                self.refresh_services_list()

            except Exception as e:
                messagebox.showerror("Error", f"Error adding service: {str(e)}")

        ttk.Button(dialog, text="Save", command=save_service).pack(pady=10)

    def show_edit_service_dialog(self):
        selection = self.services_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a service to edit")
            return

        service_id = self.services_tree.item(selection[0])['values'][0]
        service = self.db.get_service(service_id)
        # Similar to add_service_dialog but with pre-filled values

    def generate_report(self):
        report_type = self.report_type.get()
        try:
            if report_type == "daily":
                transactions = self.db.get_daily_transactions(datetime.now())
            elif report_type == "monthly":
                transactions = self.db.get_monthly_transactions(datetime.now())
            else:
                # Custom date range logic here
                pass

            # Generate report using the transactions
            self.generate_report_pdf(transactions)
            messagebox.showinfo("Success", "Report generated successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Error generating report: {str(e)}")

    def add_to_cart(self, service_id):
        service = self.db.get_service(service_id)
        if service:
            item = TransactionItem(
                id="",
                transaction_id="",
                service_id=service_id,
                quantity=1,
                price=service.price
            )
            self.cart_items.append(item)
            self.update_cart_display()

    def update_cart_display(self):
        self.cart_list.delete(*self.cart_list.get_children())
        total = Decimal('0')

        for item in self.cart_items:
            service = self.db.get_service(item.service_id)
            item_total = item.price * item.quantity
            total += item_total

            self.cart_list.insert('', 'end', values=(
                service.name,
                item.quantity,
                f"฿{item.price:,.2f}",
                f"฿{item_total:,.2f}"
            ))

        self.subtotal_var.set(f"฿{total:,.2f}")

    def clear_cart(self):
        self.cart_items = []
        self.update_cart_display()

    def setup_pos_tab(self):
        """Setup enhanced POS tab with multilingual support"""
        # Create main containers
        left_frame = ttk.Frame(self.pos_tab)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        right_frame = ttk.Frame(self.pos_tab)
        right_frame.pack(side='right', fill='both', padx=5, pady=5)

        # === Left Side ===
        # Patient Selection Section
        patient_frame = ttk.LabelFrame(
            left_frame,
            text=self.lang.get_text("patient_info")
        )
        patient_frame.pack(fill='x', padx=5, pady=5)

        # Patient Search
        search_frame = ttk.Frame(patient_frame)
        search_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(
            search_frame,
            text=self.lang.get_text("search_patient")
        ).pack(side='left', padx=5)

        self.patient_search_var = tk.StringVar()
        self.patient_search_var.trace('w', self.on_patient_search)
        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.patient_search_var
        )
        search_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Quick add patient button
        ttk.Button(
            search_frame,
            text=self.lang.get_text("add_new_patient"),
            command=self.show_add_patient_form,
            style="Custom.TButton"
        ).pack(side='right', padx=5)

        # Patient info display
        self.patient_info_frame = ttk.Frame(patient_frame)
        self.patient_info_frame.pack(fill='x', padx=5, pady=5)

        # Services Section with Categories
        services_frame = ttk.LabelFrame(
            left_frame,
            text=self.lang.get_text("services")
        )
        services_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Service categories buttons
        categories_frame = ttk.Frame(services_frame)
        categories_frame.pack(fill='x', padx=5, pady=5)

        categories = [
            "anti_aging", "facial", "body", "skin_care"
        ]

        for category in categories:
            ttk.Button(
                categories_frame,
                text=self.lang.get_text(f"category_{category}"),
                command=lambda c=category: self.filter_services(c)
            ).pack(side='left', padx=2)

        # Services list
        self.services_list = ttk.Treeview(
            services_frame,
            columns=('name', 'price', 'duration', 'doctor'),
            show='headings'
        )

        # Configure columns
        self.services_list.heading('name', text=self.lang.get_text("service_name"))
        self.services_list.heading('price', text=self.lang.get_text("price"))
        self.services_list.heading('duration', text=self.lang.get_text("duration"))
        self.services_list.heading('doctor', text=self.lang.get_text("doctor"))

        self.services_list.pack(fill='both', expand=True, padx=5, pady=5)
        self.services_list.bind('<Double-1>', self.add_service_to_cart)

        # === Right Side ===
        # Cart Section
        cart_frame = ttk.LabelFrame(
            right_frame,
            text=self.lang.get_text("cart")
        )
        cart_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Cart list
        self.cart_list = ttk.Treeview(
            cart_frame,
            columns=('service', 'doctor', 'quantity', 'price', 'total'),
            show='headings'
        )

        # Configure cart columns
        self.cart_list.heading('service', text=self.lang.get_text("service"))
        self.cart_list.heading('doctor', text=self.lang.get_text("doctor"))
        self.cart_list.heading('quantity', text=self.lang.get_text("quantity"))
        self.cart_list.heading('price', text=self.lang.get_text("price"))
        self.cart_list.heading('total', text=self.lang.get_text("total"))

        self.cart_list.pack(fill='both', expand=True, padx=5, pady=5)

        # Cart controls
        cart_controls = ttk.Frame(cart_frame)
        cart_controls.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            cart_controls,
            text=self.lang.get_text("remove_selected"),
            command=self.remove_from_cart
        ).pack(side='left', padx=5)

        ttk.Button(
            cart_controls,
            text=self.lang.get_text("clear_cart"),
            command=self.clear_cart
        ).pack(side='left', padx=5)

        # Totals display
        totals_frame = ttk.Frame(cart_frame)
        totals_frame.pack(fill='x', padx=5, pady=5)

        # Subtotal
        ttk.Label(
            totals_frame,
            text=self.lang.get_text("subtotal")
        ).pack(side='left')

        self.subtotal_var = tk.StringVar(value="฿0.00")
        ttk.Label(
            totals_frame,
            textvariable=self.subtotal_var
        ).pack(side='left', padx=5)

        # Payment Section
        payment_frame = ttk.LabelFrame(
            right_frame,
            text=self.lang.get_text("payment")
        )
        payment_frame.pack(fill='x', padx=5, pady=5)

        # Payment method
        ttk.Label(
            payment_frame,
            text=self.lang.get_text("payment_method")
        ).pack(padx=5, pady=2)

        self.payment_method = ttk.Combobox(
            payment_frame,
            values=[
                self.lang.get_text("cash"),
                self.lang.get_text("credit_card"),
                self.lang.get_text("transfer")
            ],
            state='readonly'
        )
        self.payment_method.pack(fill='x', padx=5, pady=2)

        # Process payment button
        ttk.Button(
            payment_frame,
            text=self.lang.get_text("process_payment"),
            command=self.process_payment,
            style="Custom.TButton"
        ).pack(fill='x', padx=5, pady=5)

    def add_service_to_cart(self, event=None):
        """Enhanced add to cart with doctor selection"""
        selection = self.services_list.selection()
        if not selection:
            return

        service_id = self.services_list.item(selection[0])['values'][0]

        # Show doctor selection dialog
        doctor = self.select_doctor_dialog(service_id)
        if not doctor:
            return

        service = self.db.get_service(service_id)
        if service:
            item = TransactionItem(
                id="",
                transaction_id="",
                service_id=service_id,
                doctor_id=doctor.id,
                quantity=1,
                price=service.price
            )
            self.cart_items.append(item)
            self.update_cart_display()

    def select_doctor_dialog(self, service_id):
        """Show dialog to select doctor for service"""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.lang.get_text("select_doctor"))
        dialog.transient(self.root)
        dialog.grab_set()

        # Get available doctors for this service
        doctors = self.db.get_doctors_for_service(service_id)
        selected_doctor = None

        def on_select():
            nonlocal selected_doctor
            selection = doctors_list.curselection()
            if selection:
                selected_doctor = doctors[selection[0]]
                dialog.destroy()

        # Create doctors list
        doctors_list = tk.Listbox(dialog, height=6)
        doctors_list.pack(padx=10, pady=5, fill='both', expand=True)

        for doctor in doctors:
            doctors_list.insert(tk.END, doctor.name)

        # Buttons
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(
            buttons_frame,
            text=self.lang.get_text("select"),
            command=on_select
        ).pack(side='right', padx=5)

        ttk.Button(
            buttons_frame,
            text=self.lang.get_text("cancel"),
            command=dialog.destroy
        ).pack(side='right', padx=5)

        dialog.wait_window()
        return selected_doctor

    def process_payment(self):
        """Enhanced payment processing with appointment creation"""
        if not self.current_patient or not self.cart_items:
            messagebox.showerror(
                "Error",
                self.lang.get_text("select_patient_and_services")
            )
            return

        try:
            # Create transaction
            transaction = Transaction(
                id="",
                patient_id=self.current_patient.id,
                total_amount=self.calculate_total(),
                payment_method=self.payment_method.get(),
                transaction_date=datetime.now(),
                status="completed",
                items=self.cart_items
            )

            # Save to database
            transaction_id = self.db.create_transaction(transaction)

            # Create appointments for each service
            for item in self.cart_items:
                self.create_appointment(
                    patient_id=self.current_patient.id,
                    service_id=item.service_id,
                    doctor_id=item.doctor_id
                )

            # Generate invoice
            self.generate_invoice(transaction_id)

            # Clear cart
            self.clear_cart()

            messagebox.showinfo(
                "Success",
                self.lang.get_text("payment_successful")
            )

        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("payment_error")
            )

    def refresh_patient_list(self):
        self.patient_list.delete(*self.patient_list.get_children())
        patients = self.db.get_all_patients()
        for patient in patients:
            self.patient_list.insert('', 'end', values=(
                patient.name,
                patient.phone,
                patient.email
            ))

    def refresh_services_list(self):
        self.services_tree.delete(*self.services_tree.get_children())
        services = self.db.get_all_services()
        for service in services:
            self.services_tree.insert('', 'end', values=(
                service.name,
                f"฿{service.price:,.2f}",
                f"{service.duration} mins",
                service.category
            ))

    def filter_services(self, category):
        """Filter services list by category"""
        try:
            services = self.db.get_services_by_category(category)
            self.services_list.delete(*self.services_list.get_children())

            for service in services:
                self.services_list.insert('', 'end', values=(
                    service.id,  # Hidden ID
                    service.name,
                    f"฿{service.price:,.2f}",
                    f"{service.duration} mins"
                ))
        except Exception as e:
            logger.error(f"Error filtering services: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_filtering_services")
            )

    def remove_from_cart(self):
        """Remove selected item from cart"""
        selection = self.cart_list.selection()
        if not selection:
            return

        try:
            for item in selection:
                item_values = self.cart_list.item(item)['values']
                # Find and remove the corresponding cart item
                self.cart_items = [i for i in self.cart_items if i.service_id != item_values[0]]

            self.update_cart_display()
        except Exception as e:
            logger.error(f"Error removing item from cart: {e}")

    def update_cart_display(self):
        """Update the cart display with current items"""
        try:
            self.cart_list.delete(*self.cart_list.get_children())
            total = Decimal('0')

            for item in self.cart_items:
                service = self.db.get_service(item.service_id)
                doctor = self.db.get_staff(item.doctor_id)
                item_total = item.price * item.quantity
                total += item_total

                self.cart_list.insert('', 'end', values=(
                    service.name,
                    doctor.name if doctor else '',
                    item.quantity,
                    f"฿{item.price:,.2f}",
                    f"฿{item_total:,.2f}"
                ))

            self.subtotal_var.set(f"฿{total:,.2f}")
        except Exception as e:
            logger.error(f"Error updating cart display: {e}")

    def create_appointment(self, patient_id: str, service_id: str, doctor_id: str):
        """Create an appointment for the service"""
        try:
            service = self.db.get_service(service_id)
            current_time = datetime.now()

            # Find next available slot
            appointment = {
                'patient_id': patient_id,
                'service_id': service_id,
                'doctor_id': doctor_id,
                'start_time': current_time,  # You might want to implement proper scheduling
                'end_time': current_time + timedelta(minutes=service.duration),
                'status': 'scheduled'
            }

            self.db.create_appointment(appointment)
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_creating_appointment")
            )

    def calculate_total(self) -> Decimal:
        """Calculate total amount for all items in cart"""
        return sum(item.price * item.quantity for item in self.cart_items)

    def setup_treatments_tab(self):
        """Setup treatments tracking tab"""
        # Create main containers
        left_frame = ttk.Frame(self.treatments_tab)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        right_frame = ttk.Frame(self.treatments_tab)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Left side - Patient Selection and History
        # Patient Search
        search_frame = ttk.LabelFrame(left_frame, text=self.lang.get_text("search_patient"))
        search_frame.pack(fill='x', padx=5, pady=5)

        self.treatment_patient_search = ttk.Entry(search_frame)
        self.treatment_patient_search.pack(fill='x', padx=5, pady=5)
        self.treatment_patient_search.bind('<KeyRelease>', self.search_treatment_patient)

        # Treatment History
        history_frame = ttk.LabelFrame(left_frame, text=self.lang.get_text("treatment_history"))
        history_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Treatment history tree
        columns = ('date', 'service', 'doctor', 'status')
        self.treatment_history_tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show='headings'
        )

        # Configure columns
        self.treatment_history_tree.heading('date', text=self.lang.get_text("date"))
        self.treatment_history_tree.heading('service', text=self.lang.get_text("service"))
        self.treatment_history_tree.heading('doctor', text=self.lang.get_text("doctor"))
        self.treatment_history_tree.heading('status', text=self.lang.get_text("status"))

        self.treatment_history_tree.pack(fill='both', expand=True, padx=5, pady=5)
        self.treatment_history_tree.bind('<<TreeviewSelect>>', self.load_treatment_details)

        # Right side - Treatment Details
        details_frame = ttk.LabelFrame(right_frame, text=self.lang.get_text("treatment_details"))
        details_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Before/After Photos
        photos_frame = ttk.Frame(details_frame)
        photos_frame.pack(fill='x', padx=5, pady=5)

        # Before photo
        before_frame = ttk.LabelFrame(photos_frame, text=self.lang.get_text("before"))
        before_frame.pack(side='left', fill='both', expand=True, padx=5)

        self.before_photo_label = ttk.Label(before_frame, text="No photo")
        self.before_photo_label.pack(padx=5, pady=5)

        ttk.Button(
            before_frame,
            text=self.lang.get_text("add_photo"),
            command=lambda: self.add_treatment_photo("before")
        ).pack(padx=5, pady=5)

        # After photo
        after_frame = ttk.LabelFrame(photos_frame, text=self.lang.get_text("after"))
        after_frame.pack(side='right', fill='both', expand=True, padx=5)

        self.after_photo_label = ttk.Label(after_frame, text="No photo")
        self.after_photo_label.pack(padx=5, pady=5)

        ttk.Button(
            after_frame,
            text=self.lang.get_text("add_photo"),
            command=lambda: self.add_treatment_photo("after")
        ).pack(padx=5, pady=5)

        # Treatment Notes
        notes_frame = ttk.LabelFrame(details_frame, text=self.lang.get_text("treatment_notes"))
        notes_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Notes sections
        sections = [
            ('chief_complaint', 3),
            ('diagnosis', 3),
            ('treatment_plan', 4),
            ('notes', 4),
            ('follow_up', 2)
        ]

        self.treatment_note_widgets = {}

        for section, height in sections:
            section_frame = ttk.Frame(notes_frame)
            section_frame.pack(fill='x', pady=2)

            ttk.Label(
                section_frame,
                text=self.lang.get_text(f"treatment_{section}")
            ).pack(anchor='w')

            text_widget = tk.Text(section_frame, height=height)
            text_widget.pack(fill='x', pady=2)
            self.treatment_note_widgets[section] = text_widget

        # Buttons
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            button_frame,
            text=self.lang.get_text("save_treatment"),
            command=self.save_treatment_notes
        ).pack(side='right', padx=5)

        ttk.Button(
            button_frame,
            text=self.lang.get_text("print_treatment"),
            command=self.print_treatment_record
        ).pack(side='right', padx=5)

    def search_treatment_patient(self, event=None):
        """Search patient for treatment history"""
        search_term = self.treatment_patient_search.get()
        if len(search_term) < 2:
            return

        try:
            patients = self.db.search_patients(search_term)
            if patients:
                self.show_treatment_patient_selection(patients)
        except Exception as e:
            logger.error(f"Error searching patients: {e}")

    def show_treatment_patient_selection(self, patients):
        """Show dialog to select patient for treatment history"""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.lang.get_text("select_patient"))
        dialog.transient(self.root)
        dialog.grab_set()

        # Create listbox with patients
        listbox = tk.Listbox(dialog, height=10)
        listbox.pack(fill='both', expand=True, padx=5, pady=5)

        for patient in patients:
            listbox.insert(tk.END, f"{patient.name} - {patient.phone}")

        def on_select():
            selection = listbox.curselection()
            if selection:
                patient = patients[selection[0]]
                self.load_patient_treatments(patient)
                dialog.destroy()

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            button_frame,
            text=self.lang.get_text("select"),
            command=on_select
        ).pack(side='right', padx=5)

        ttk.Button(
            button_frame,
            text=self.lang.get_text("cancel"),
            command=dialog.destroy
        ).pack(side='right', padx=5)

    def load_patient_treatments(self, patient):
        """Load treatment history for selected patient"""
        try:
            treatments = self.db.get_patient_treatment_history(patient.id)
            self.treatment_history_tree.delete(*self.treatment_history_tree.get_children())

            for treatment in treatments:
                self.treatment_history_tree.insert('', 'end', values=(
                    treatment.treatment_date.strftime("%Y-%m-%d"),
                    treatment.service_name,
                    treatment.doctor_name,
                    treatment.status
                ))

        except Exception as e:
            logger.error(f"Error loading treatments: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_loading_treatments")
            )

    def load_treatment_details(self, event=None):
        """Load details for selected treatment"""
        selection = self.treatment_history_tree.selection()
        if not selection:
            return

        try:
            item = self.treatment_history_tree.item(selection[0])
            treatment_date = item['values'][0]
            # Load treatment details from database
            treatment = self.db.get_treatment_details(treatment_date)

            # Update notes sections
            for section, widget in self.treatment_note_widgets.items():
                widget.delete('1.0', tk.END)
                widget.insert('1.0', getattr(treatment, section, ''))

            # Update photos
            self.update_treatment_photos(treatment)

        except Exception as e:
            logger.error(f"Error loading treatment details: {e}")

    def save_treatment_notes(self):
        """Save treatment notes to database"""
        selection = self.treatment_history_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_treatment_first")
            )
            return

        try:
            # Get notes from all sections
            notes = {
                section: widget.get('1.0', tk.END).strip()
                for section, widget in self.treatment_note_widgets.items()
            }

            # Save to database
            self.db.update_treatment_notes(
                treatment_id=self.treatment_history_tree.item(selection[0])['values'][0],
                notes=notes
            )

            messagebox.showinfo(
                "Success",
                self.lang.get_text("treatment_saved")
            )

        except Exception as e:
            logger.error(f"Error saving treatment notes: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_saving_treatment")
            )

    def setup_doctor_notes_tab(self):
        """Setup doctor's notes interface"""
        # Create main containers
        left_frame = ttk.Frame(self.doctor_notes_tab)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        right_frame = ttk.Frame(self.doctor_notes_tab)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Patient Selection (Left Side)
        patient_frame = ttk.LabelFrame(left_frame, text=self.lang.get_text("patient_selection"))
        patient_frame.pack(fill='x', padx=5, pady=5)

        # Search
        search_var = tk.StringVar()
        search_var.trace('w', lambda *args: self.search_patients_for_notes(search_var.get()))
        ttk.Entry(patient_frame, textvariable=search_var).pack(fill='x', padx=5, pady=5)

        # Patient list
        self.doctor_notes_patient_list = ttk.Treeview(
            left_frame,
            columns=('name', 'last_visit'),
            show='headings'
        )
        self.doctor_notes_patient_list.heading('name', text=self.lang.get_text("patient_name"))
        self.doctor_notes_patient_list.heading('last_visit', text=self.lang.get_text("last_visit"))
        self.doctor_notes_patient_list.pack(fill='both', expand=True, padx=5, pady=5)
        self.doctor_notes_patient_list.bind('<<TreeviewSelect>>', self.load_patient_notes)

        # Notes Section (Right Side)
        notes_frame = ttk.LabelFrame(right_frame, text=self.lang.get_text("medical_notes"))
        notes_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Medical History
        ttk.Label(notes_frame, text=self.lang.get_text("medical_history")).pack(anchor='w', padx=5, pady=2)
        self.medical_history_text = tk.Text(notes_frame, height=4)
        self.medical_history_text.pack(fill='x', padx=5, pady=2)

        # Treatment Progress
        ttk.Label(notes_frame, text=self.lang.get_text("treatment_progress")).pack(anchor='w', padx=5, pady=2)
        self.progress_text = tk.Text(notes_frame, height=4)
        self.progress_text.pack(fill='x', padx=5, pady=2)

        # Recommendations
        ttk.Label(notes_frame, text=self.lang.get_text("recommendations")).pack(anchor='w', padx=5, pady=2)
        self.recommendations_text = tk.Text(notes_frame, height=4)
        self.recommendations_text.pack(fill='x', padx=5, pady=2)

        # Next Steps
        ttk.Label(notes_frame, text=self.lang.get_text("next_steps")).pack(anchor='w', padx=5, pady=2)
        self.next_steps_text = tk.Text(notes_frame, height=4)
        self.next_steps_text.pack(fill='x', padx=5, pady=2)

        # Photos Section
        photos_frame = ttk.LabelFrame(right_frame, text=self.lang.get_text("progress_photos"))
        photos_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            photos_frame,
            text=self.lang.get_text("add_photos"),
            command=self.add_progress_photos
        ).pack(padx=5, pady=5)

        # Action Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            button_frame,
            text=self.lang.get_text("save_notes"),
            command=self.save_doctor_notes
        ).pack(side='right', padx=5)

        ttk.Button(
            button_frame,
            text=self.lang.get_text("print_notes"),
            command=self.print_doctor_notes
        ).pack(side='right', padx=5)

    def print_treatment_record(self):
        """Print treatment record as PDF"""
        selection = self.treatment_history_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_treatment_first")
            )
            return

        try:
            item = self.treatment_history_tree.item(selection[0])
            treatment_date = item['values'][0]
            treatment = self.db.get_treatment_details(treatment_date)

            # Generate PDF
            filename = f"treatment_record_{treatment_date}.pdf"
            self.generate_treatment_pdf(treatment, filename)

            messagebox.showinfo(
                "Success",
                self.lang.get_text("treatment_printed")
            )
        except Exception as e:
            logger.error(f"Error printing treatment record: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_printing_treatment")
            )

    def generate_treatment_pdf(self, treatment, filename):
        """Generate PDF for treatment record"""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Build the document
        story = []
        styles = getSampleStyleSheet()

        # Add clinic logo and info
        try:
            logo_path = os.path.join('static', 'assets', 'logo.jpeg')
            if os.path.exists(logo_path):
                img = Image(logo_path, width=200, height=100)
                story.append(img)
        except Exception as e:
            logger.error(f"Error adding logo to PDF: {e}")

        # Add clinic name and header
        story.append(Paragraph("Treatment Record", styles['Title']))
        story.append(Spacer(1, 12))

        # Add treatment details
        details = [
            ("Date:", treatment.treatment_date.strftime("%Y-%m-%d")),
            ("Patient:", treatment.patient_name),
            ("Doctor:", treatment.doctor_name),
            ("Service:", treatment.service_name)
        ]

        for label, value in details:
            text = f"<b>{label}</b> {value}"
            story.append(Paragraph(text, styles['Normal']))

        story.append(Spacer(1, 12))

        # Add treatment notes sections
        sections = [
            ('Chief Complaint', treatment.chief_complaint),
            ('Diagnosis', treatment.diagnosis),
            ('Treatment Plan', treatment.treatment_plan),
            ('Notes', treatment.notes),
            ('Follow-up', treatment.follow_up)
        ]

        for title, content in sections:
            story.append(Paragraph(title, styles['Heading2']))
            story.append(Paragraph(content or "N/A", styles['Normal']))
            story.append(Spacer(1, 12))

        # Build PDF
        doc.build(story)

    def add_treatment_photo(self, photo_type):
        """Add before/after photo to treatment"""
        from tkinter import filedialog

        selection = self.treatment_history_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_treatment_first")
            )
            return

        try:
            # Get photo file
            filetypes = [
                ('Image files', '*.jpg *.jpeg *.png'),
                ('All files', '*.*')
            ]
            filename = filedialog.askopenfilename(
                title=self.lang.get_text("select_photo"),
                filetypes=filetypes
            )

            if filename:
                # Save photo to storage and update database
                treatment_id = self.treatment_history_tree.item(selection[0])['values'][0]
                photo_path = self.save_treatment_photo(filename, treatment_id, photo_type)
                self.db.update_treatment_photo(treatment_id, photo_type, photo_path)

                # Update display
                self.load_treatment_details()

        except Exception as e:
            logger.error(f"Error adding treatment photo: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_adding_photo")
            )

    def save_treatment_photo(self, source_path, treatment_id, photo_type):
        """Save treatment photo to storage"""
        from PIL import Image
        import shutil

        try:
            # Create photos directory if it doesn't exist
            photos_dir = os.path.join('static', 'photos', 'treatments', treatment_id)
            os.makedirs(photos_dir, exist_ok=True)

            # Generate destination path
            file_ext = os.path.splitext(source_path)[1]
            dest_filename = f"{photo_type}{file_ext}"
            dest_path = os.path.join(photos_dir, dest_filename)

            # Copy and optimize photo
            with Image.open(source_path) as img:
                # Resize if too large
                max_size = (1200, 1200)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                # Save optimized version
                img.save(dest_path, quality=85, optimize=True)

            return dest_path

        except Exception as e:
            logger.error(f"Error saving treatment photo: {e}")
            raise

    def update_treatment_photos(self, treatment):
        """Update photo displays for treatment"""
        try:
            # Update before photo
            if treatment.before_photo:
                self.display_treatment_photo(treatment.before_photo, self.before_photo_label)
            else:
                self.before_photo_label.config(text="No photo")

            # Update after photo
            if treatment.after_photo:
                self.display_treatment_photo(treatment.after_photo, self.after_photo_label)
            else:
                self.after_photo_label.config(text="No photo")

        except Exception as e:
            logger.error(f"Error updating treatment photos: {e}")

    def display_treatment_photo(self, photo_path, label):
        """Display treatment photo in label"""
        try:
            # Load and resize photo
            image = Image.open(photo_path)
            # Calculate size to fit in label (e.g., 200x200)
            image.thumbnail((200, 200), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)

            # Update label
            label.config(image=photo)
            label.image = photo  # Keep reference

        except Exception as e:
            logger.error(f"Error displaying treatment photo: {e}")
            label.config(text="Error loading photo")

    def search_patients_for_notes(self, search_term: str):
        """Search patients for doctor notes"""
        if len(search_term) < 2:
            return

        try:
            patients = self.db.search_patients(search_term)
            self.doctor_notes_patient_list.delete(*self.doctor_notes_patient_list.get_children())

            for patient in patients:
                last_visit = self.db.get_patient_last_visit(patient.id)
                self.doctor_notes_patient_list.insert('', 'end', values=(
                    patient.name,
                    last_visit.strftime("%Y-%m-%d") if last_visit else "No visits"
                ))
        except Exception as e:
            logger.error(f"Error searching patients for notes: {e}")

    def load_patient_notes(self, event=None):
        """Load notes for selected patient"""
        selection = self.doctor_notes_patient_list.selection()
        if not selection:
            return

        try:
            patient_name = self.doctor_notes_patient_list.item(selection[0])['values'][0]
            patient = self.db.get_patient_by_name(patient_name)

            if patient:
                # Clear existing notes
                self.medical_history_text.delete('1.0', tk.END)
                self.progress_text.delete('1.0', tk.END)
                self.recommendations_text.delete('1.0', tk.END)
                self.next_steps_text.delete('1.0', tk.END)

                # Load patient's medical history
                self.medical_history_text.insert('1.0', patient.medical_history or '')

                # Load latest treatment notes
                latest_treatment = self.db.get_latest_treatment(patient.id)
                if latest_treatment:
                    self.progress_text.insert('1.0', latest_treatment.progress_notes or '')
                    self.recommendations_text.insert('1.0', latest_treatment.recommendations or '')
                    self.next_steps_text.insert('1.0', latest_treatment.next_steps or '')

        except Exception as e:
            logger.error(f"Error loading patient notes: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_loading_notes")
            )

    def save_doctor_notes(self):
        """Save doctor's notes to database"""
        selection = self.doctor_notes_patient_list.selection()
        if not selection:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_patient_first")
            )
            return

        try:
            patient_name = self.doctor_notes_patient_list.item(selection[0])['values'][0]
            patient = self.db.get_patient_by_name(patient_name)

            if patient:
                # Update medical history
                self.db.update_patient_medical_history(
                    patient.id,
                    self.medical_history_text.get('1.0', tk.END).strip()
                )

                # Create new treatment notes
                notes_data = {
                    'patient_id': patient.id,
                    'progress_notes': self.progress_text.get('1.0', tk.END).strip(),
                    'recommendations': self.recommendations_text.get('1.0', tk.END).strip(),
                    'next_steps': self.next_steps_text.get('1.0', tk.END).strip(),
                    'created_at': datetime.now()
                }

                self.db.add_treatment_notes(notes_data)

                messagebox.showinfo(
                    "Success",
                    self.lang.get_text("notes_saved")
                )

        except Exception as e:
            logger.error(f"Error saving doctor notes: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_saving_notes")
            )

    def print_doctor_notes(self):
        """Print doctor's notes as PDF"""
        selection = self.doctor_notes_patient_list.selection()
        if not selection:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_patient_first")
            )
            return

        try:
            patient_name = self.doctor_notes_patient_list.item(selection[0])['values'][0]
            patient = self.db.get_patient_by_name(patient_name)

            if patient:
                # Prepare notes data
                notes_data = {
                    'patient_name': patient.name,
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'medical_history': self.medical_history_text.get('1.0', tk.END).strip(),
                    'progress_notes': self.progress_text.get('1.0', tk.END).strip(),
                    'recommendations': self.recommendations_text.get('1.0', tk.END).strip(),
                    'next_steps': self.next_steps_text.get('1.0', tk.END).strip()
                }

                # Generate PDF
                filename = f"doctor_notes_{patient.name}_{datetime.now().strftime('%Y%m%d')}.pdf"
                self.generate_doctor_notes_pdf(notes_data, filename)

                messagebox.showinfo(
                    "Success",
                    self.lang.get_text("notes_printed")
                )

        except Exception as e:
            logger.error(f"Error printing doctor notes: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_printing_notes")
            )

    def generate_doctor_notes_pdf(self, notes_data: dict, filename: str):
        """Generate PDF for doctor's notes"""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Add clinic info
        story.append(Paragraph(self.lang.get_text("clinic_name"), styles['Title']))
        story.append(Spacer(1, 12))

        # Add patient info and date
        story.append(Paragraph(f"Patient: {notes_data['patient_name']}", styles['Normal']))
        story.append(Paragraph(f"Date: {notes_data['date']}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Add notes sections
        sections = [
            ("Medical History", notes_data['medical_history']),
            ("Progress Notes", notes_data['progress_notes']),
            ("Recommendations", notes_data['recommendations']),
            ("Next Steps", notes_data['next_steps'])
        ]

        for title, content in sections:
            story.append(Paragraph(title, styles['Heading2']))
            story.append(Paragraph(content or "N/A", styles['Normal']))
            story.append(Spacer(1, 12))

        doc.build(story)

    def add_progress_photos(self):
        """Add progress photos to patient record"""
        selection = self.doctor_notes_patient_list.selection()
        if not selection:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_patient_first")
            )
            return

        try:
            from tkinter import filedialog

            filetypes = [
                ('Image files', '*.jpg *.jpeg *.png'),
                ('All files', '*.*')
            ]

            filenames = filedialog.askopenfilenames(
                title=self.lang.get_text("select_photos"),
                filetypes=filetypes
            )

            if filenames:
                patient_name = self.doctor_notes_patient_list.item(selection[0])['values'][0]
                patient = self.db.get_patient_by_name(patient_name)

                if patient:
                    # Save each photo
                    photo_paths = []
                    for filename in filenames:
                        photo_path = self.save_progress_photo(filename, patient.id)
                        photo_paths.append(photo_path)

                    # Update database
                    self.db.add_progress_photos(patient.id, photo_paths)

                    messagebox.showinfo(
                        "Success",
                        self.lang.get_text("photos_added")
                    )

        except Exception as e:
            logger.error(f"Error adding progress photos: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_adding_photos")
            )

    def save_progress_photo(self, source_path: str, patient_id: str) -> str:
        """Save progress photo to storage"""
        from PIL import Image
        import shutil

        try:
            # Create photos directory if it doesn't exist
            photos_dir = os.path.join('static', 'photos', 'progress', patient_id)
            os.makedirs(photos_dir, exist_ok=True)

            # Generate destination path
            file_ext = os.path.splitext(source_path)[1]
            dest_filename = f"progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
            dest_path = os.path.join(photos_dir, dest_filename)

            # Copy and optimize photo
            with Image.open(source_path) as img:
                # Resize if too large
                max_size = (1200, 1200)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                # Save optimized version
                img.save(dest_path, quality=85, optimize=True)

            return dest_path

        except Exception as e:
            logger.error(f"Error saving progress photo: {e}")
            raise

    def setup_settings_tab(self):
        """Setup settings and configuration tab"""
        # Create notebook for settings categories
        settings_notebook = ttk.Notebook(self.settings_tab)
        settings_notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # General Settings
        general_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(general_frame, text=self.lang.get_text("general_settings"))

        # Company Information
        company_frame = ttk.LabelFrame(general_frame, text=self.lang.get_text("company_info"))
        company_frame.pack(fill='x', padx=5, pady=5)

        company_fields = [
            ("company_name", "Clinic Name"),
            ("company_address", "Address"),
            ("company_phone", "Phone"),
            ("company_email", "Email"),
            ("company_tax_id", "Tax ID")
        ]

        self.company_vars = {}
        for field_id, label in company_fields:
            frame = ttk.Frame(company_frame)
            frame.pack(fill='x', padx=5, pady=2)
            # Fix: Create a fixed-width label using label width instead of pack width
            label_widget = ttk.Label(frame, text=self.lang.get_text(label), width=20)
            label_widget.pack(side='left')
            var = tk.StringVar()
            ttk.Entry(frame, textvariable=var).pack(side='left', fill='x', expand=True)
            self.company_vars[field_id] = var

        # User Management
        users_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(users_frame, text=self.lang.get_text("user_management"))

        # User list
        self.users_tree = ttk.Treeview(
            users_frame,
            columns=('username', 'role', 'status'),
            show='headings'
        )
        self.users_tree.heading('username', text=self.lang.get_text("username"))
        self.users_tree.heading('role', text=self.lang.get_text("role"))
        self.users_tree.heading('status', text=self.lang.get_text("status"))
        self.users_tree.pack(fill='both', expand=True, padx=5, pady=5)

        # User management buttons
        user_buttons = ttk.Frame(users_frame)
        user_buttons.pack(fill='x', padx=5, pady=5)
        ttk.Button(
            user_buttons,
            text=self.lang.get_text("add_user"),
            command=self.show_add_user_dialog
        ).pack(side='left', padx=5)

        # Services Management
        services_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(services_frame, text=self.lang.get_text("services_management"))

        # Categories frame
        categories_frame = ttk.LabelFrame(services_frame, text=self.lang.get_text("categories"))
        categories_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            categories_frame,
            text=self.lang.get_text("manage_categories"),
            command=self.show_categories_dialog
        ).pack(padx=5, pady=5)

        # Commission Settings
        commission_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(commission_frame, text=self.lang.get_text("commission_settings"))

        # Commission rates tree
        self.commission_tree = ttk.Treeview(
            commission_frame,
            columns=('service', 'staff', 'rate'),
            show='headings'
        )
        self.commission_tree.heading('service', text=self.lang.get_text("service"))
        self.commission_tree.heading('staff', text=self.lang.get_text("staff"))
        self.commission_tree.heading('rate', text=self.lang.get_text("rate"))
        self.commission_tree.pack(fill='both', expand=True, padx=5, pady=5)

        commission_buttons = ttk.Frame(commission_frame)
        commission_buttons.pack(fill='x', padx=5, pady=5)
        ttk.Button(
            commission_buttons,
            text=self.lang.get_text("set_commission"),
            command=self.show_commission_dialog
        ).pack(side='left', padx=5)

        # Backup Settings
        backup_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(backup_frame, text=self.lang.get_text("backup_settings"))

        # Backup location
        backup_path_frame = ttk.LabelFrame(backup_frame, text=self.lang.get_text("backup_location"))
        backup_path_frame.pack(fill='x', padx=5, pady=5)

        self.backup_path_var = tk.StringVar()
        ttk.Entry(backup_path_frame, textvariable=self.backup_path_var).pack(side='left', fill='x', expand=True, padx=5,
                                                                             pady=5)
        ttk.Button(
            backup_path_frame,
            text=self.lang.get_text("browse"),
            command=self.select_backup_location
        ).pack(side='right', padx=5)

        # Backup schedule
        schedule_frame = ttk.LabelFrame(backup_frame, text=self.lang.get_text("backup_schedule"))
        schedule_frame.pack(fill='x', padx=5, pady=5)

        self.backup_schedule_var = tk.StringVar(value="daily")
        ttk.Radiobutton(
            schedule_frame,
            text=self.lang.get_text("daily"),
            value="daily",
            variable=self.backup_schedule_var
        ).pack(padx=5, pady=2)
        ttk.Radiobutton(
            schedule_frame,
            text=self.lang.get_text("weekly"),
            value="weekly",
            variable=self.backup_schedule_var
        ).pack(padx=5, pady=2)

        # Save settings button
        ttk.Button(
            self.settings_tab,
            text=self.lang.get_text("save_settings"),
            command=self.save_settings
        ).pack(side='bottom', padx=5, pady=10)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = BeautyClinicPOS()
    app.root.mainloop()
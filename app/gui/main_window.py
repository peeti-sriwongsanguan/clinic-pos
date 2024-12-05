import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
from datetime import datetime
from decimal import Decimal
import logging

from app.gui.theme_config import ThemeConfig
from app.utils.invoice_generator import InvoiceGenerator
from app.database.db_manager import DatabaseManager
from app.database.model import Patient, Service, Transaction, TransactionItem

logger = logging.getLogger(__name__)


class BeautyClinicPOS:
    def __init__(self):
        logger.debug("Initializing BeautyClinicPOS...")

        # Initialize database first
        try:
            logger.debug("Initializing database connection...")
            self.db = DatabaseManager()
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
            self.setup_window()
            self.setup_branding()
            self.create_styles()
            self.setup_gui()
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
        logger.debug("Configuring window properties...")
        self.root.title("Beauty Clinic POS")
        self.root.geometry("1280x800")

        # Add a test label to see if window appears
        test_label = tk.Label(self.root, text="Beauty Clinic POS is starting...", font=('Helvetica', 16))
        test_label.pack(pady=20)
    def setup_window(self):
        self.root.title("Beauty Clinic POS")
        self.root.geometry("1280x800")
        self.root.configure(bg=ThemeConfig.PRIMARY_PINK)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

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

        # Configure main theme
        style.configure(
            "Custom.TFrame",
            background=ThemeConfig.PRIMARY_PINK
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

    def setup_gui(self):
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)

        # Create different tabs
        self.pos_tab = ttk.Frame(self.notebook)
        self.patients_tab = ttk.Frame(self.notebook)
        self.services_tab = ttk.Frame(self.notebook)
        self.reports_tab = ttk.Frame(self.notebook)
        self.appointments_tab = ttk.Frame(self.notebook)

        # Add tabs to notebook
        self.notebook.add(self.pos_tab, text="POS")
        self.notebook.add(self.patients_tab, text="Patients")
        self.notebook.add(self.services_tab, text="Services")
        self.notebook.add(self.appointments_tab, text="Appointments")
        self.notebook.add(self.reports_tab, text="Reports")

        # Setup each tab
        self.setup_pos_tab()
        self.setup_patients_tab()
        self.setup_services_tab()
        self.setup_appointments_tab()
        self.setup_reports_tab()

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

    def calculate_total(self) -> Decimal:
        return sum(item.price * item.quantity for item in self.cart_items)

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

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = BeautyClinicPOS()
    app.root.mainloop()
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PatientsTab:
    def __init__(self, parent, db, lang):
        self.parent = parent
        self.db = db
        self.lang = lang
        self.setup_tab()
        self.patient_list = ttk.Treeview(
            self.parent,
            columns=('name', 'phone', 'email', 'last_visit'),
            show='headings'
        )

        self.patient_list.heading('name', text=self.lang.get_text("name"))
        self.patient_list.heading('phone', text=self.lang.get_text("phone"))
        self.patient_list.heading('email', text=self.lang.get_text("email"))
        self.patient_list.heading('last_visit', text=self.lang.get_text("last_visit"))

    def setup_tab(self):
        # Search frame
        search_frame = ttk.Frame(self.parent)
        search_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(search_frame, text=self.lang.get_text("search")).pack(side='left', padx=5)
        self.patient_search_var = tk.StringVar()
        self.patient_search_var.trace('w', self.on_patient_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.patient_search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Add New Patient button
        ttk.Button(
            search_frame,
            text=self.lang.get_text("add_new_patient"),
            command=self.show_add_patient_form
        ).pack(side='right', padx=5)

        # Patient list
        self.patient_list = ttk.Treeview(
            self.parent,
            columns=('name', 'phone', 'email', 'last_visit'),
            show='headings'
        )

        # Configure columns
        self.patient_list.heading('name', text=self.lang.get_text("name"))
        self.patient_list.heading('phone', text=self.lang.get_text("phone"))
        self.patient_list.heading('email', text=self.lang.get_text("email"))
        self.patient_list.heading('last_visit', text=self.lang.get_text("last_visit"))

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.patient_list.yview)
        self.patient_list.configure(yscrollcommand=scrollbar.set)

        # Pack list and scrollbar
        self.patient_list.pack(side='left', fill='both', expand=True, padx=10, pady=5)
        scrollbar.pack(side='right', fill='y')

        # Buttons frame
        buttons_frame = ttk.Frame(self.parent)
        buttons_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(
            buttons_frame,
            text=self.lang.get_text("edit_patient"),
            command=self.show_edit_patient_dialog
        ).pack(side='left', padx=5)

        self.refresh_patient_list()

    def show_add_patient_form(self):
        """Show the add patient form"""
        dialog = tk.Toplevel(self.parent)
        dialog.title(self.lang.get_text("add_new_patient"))
        dialog.geometry("600x800")
        dialog.transient(self.parent)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, style='Custom.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Form fields
        fields = [
            ("name", "Name*:"),
            ("phone", "Phone*:"),
            ("email", "Email:"),
            ("address", "Address:"),
            ("birth_date", "Birth Date:"),
            ("gender", "Gender:"),
            ("emergency_contact", "Emergency Contact:")
        ]

        self.patient_form_vars = {}

        for field_name, label_text in fields:
            frame = ttk.Frame(main_frame)
            frame.pack(fill='x', pady=5)

            ttk.Label(frame, text=label_text).pack(side='left', width=120)

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
            else:
                var = tk.StringVar()
                ttk.Entry(frame, textvariable=var).pack(side='left', fill='x', expand=True)
                self.patient_form_vars[field_name] = var

        # Medical History
        ttk.Label(main_frame, text="Medical History:").pack(anchor='w', pady=(10, 5))
        self.medical_history_text = tk.Text(main_frame, height=4)
        self.medical_history_text.pack(fill='x', pady=5)

        # Notes
        ttk.Label(main_frame, text="Notes:").pack(anchor='w', pady=(10, 5))
        self.notes_text = tk.Text(main_frame, height=4)
        self.notes_text.pack(fill='x', pady=5)

        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', pady=20)

        ttk.Button(
            buttons_frame,
            text=self.lang.get_text("save"),
            command=self.save_new_patient
        ).pack(side='right', padx=5)

        ttk.Button(
            buttons_frame,
            text=self.lang.get_text("cancel"),
            command=dialog.destroy
        ).pack(side='right', padx=5)

        # Required fields note
        ttk.Label(
            main_frame,
            text="* Required fields",
            font=("Helvetica", 10, "italic")
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
            self.db.add_patient(patient_data)

            # Show success message
            messagebox.showinfo(
                "Success",
                self.lang.get_text("patient_added_successfully")
            )

            # Close the form and refresh list
            self.refresh_patient_list()
            self.dialog.destroy()

        except Exception as e:
            logger.error(f"Error saving patient: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_saving_patient")
            )

    def show_edit_patient_dialog(self):
        """Show dialog to edit patient"""
        selection = self.patient_list.selection()
        if not selection:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_patient_to_edit")
            )
            return

        try:
            patient_id = self.patient_list.item(selection[0])['values'][0]
            patient = self.db.get_patient(patient_id)

            dialog = tk.Toplevel(self.parent)
            dialog.title(self.lang.get_text("edit_patient"))
            dialog.geometry("600x800")
            dialog.transient(self.parent)
            dialog.grab_set()

            main_frame = ttk.Frame(dialog, style='Custom.TFrame')
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)

            # Form fields
            fields = [
                ("name", "Name*:", patient.name),
                ("phone", "Phone*:", patient.phone),
                ("email", "Email:", patient.email or ""),
                ("address", "Address:", patient.address or ""),
                ("birth_date", "Birth Date:", patient.birth_date or ""),
                ("gender", "Gender:", patient.gender or ""),
                ("emergency_contact", "Emergency Contact:", patient.emergency_contact or "")
            ]

            self.edit_form_vars = {}

            for field_name, label_text, value in fields:
                frame = ttk.Frame(main_frame)
                frame.pack(fill='x', pady=5)

                ttk.Label(frame, text=label_text).pack(side='left', width=120)

                if field_name == "gender":
                    var = tk.StringVar(value=value)
                    combo = ttk.Combobox(
                        frame,
                        textvariable=var,
                        values=["Female", "Male", "Other"],
                        state="readonly"
                    )
                    combo.pack(side='left', fill='x', expand=True)
                    self.edit_form_vars[field_name] = var
                else:
                    var = tk.StringVar(value=value)
                    ttk.Entry(frame, textvariable=var).pack(side='left', fill='x', expand=True)
                    self.edit_form_vars[field_name] = var

            # Medical History
            ttk.Label(main_frame, text="Medical History:").pack(anchor='w', pady=(10, 5))
            self.edit_medical_history_text = tk.Text(main_frame, height=4)
            self.edit_medical_history_text.pack(fill='x', pady=5)
            if patient.medical_history:
                self.edit_medical_history_text.insert('1.0', patient.medical_history)

            # Notes
            ttk.Label(main_frame, text="Notes:").pack(anchor='w', pady=(10, 5))
            self.edit_notes_text = tk.Text(main_frame, height=4)
            self.edit_notes_text.pack(fill='x', pady=5)
            if patient.notes:
                self.edit_notes_text.insert('1.0', patient.notes)

            # Buttons
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill='x', pady=20)

            ttk.Button(
                buttons_frame,
                text=self.lang.get_text("save"),
                command=lambda: self.save_edited_patient(patient.id)
            ).pack(side='right', padx=5)

            ttk.Button(
                buttons_frame,
                text=self.lang.get_text("cancel"),
                command=dialog.destroy
            ).pack(side='right', padx=5)

        except Exception as e:
            logger.error(f"Error showing edit dialog: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_loading_patient")
            )

    def save_edited_patient(self, patient_id):
        """Save edited patient data"""
        # Validate required fields
        required_fields = ['name', 'phone']
        for field in required_fields:
            if not self.edit_form_vars[field].get().strip():
                messagebox.showerror(
                    "Validation Error",
                    f"{field.capitalize()} is required!"
                )
                return

        try:
            # Create patient object
            patient_data = {
                'id': patient_id,
                'name': self.edit_form_vars['name'].get().strip(),
                'phone': self.edit_form_vars['phone'].get().strip(),
                'email': self.edit_form_vars['email'].get().strip(),
                'address': self.edit_form_vars['address'].get().strip(),
                'birth_date': self.edit_form_vars['birth_date'].get().strip(),
                'gender': self.edit_form_vars['gender'].get(),
                'emergency_contact': self.edit_form_vars['emergency_contact'].get().strip(),
                'medical_history': self.edit_medical_history_text.get('1.0', tk.END).strip(),
                'notes': self.edit_notes_text.get('1.0', tk.END).strip(),
                'updated_at': datetime.now()
            }

            # Save to database
            self.db.update_patient(patient_data)

            # Show success message
            messagebox.showinfo(
                "Success",
                self.lang.get_text("patient_updated_successfully")
            )

            # Close the form and refresh list
            self.refresh_patient_list()
            self.dialog.destroy()

        except Exception as e:
            logger.error(f"Error updating patient: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_updating_patient")
            )

    def on_patient_search(self, *args):
        """Handle patient search"""
        search_term = self.patient_search_var.get()
        if len(search_term) >= 2:
            try:
                patients = self.db.search_patients(search_term)
                self.update_patient_list(patients)
            except Exception as e:
                logger.error(f"Error searching patients: {e}")

    def update_patient_list(self, patients):
        """Update the patient list display"""
        self.patient_list.delete(*self.patient_list.get_children())
        for patient in patients:
            last_visit = self.db.get_patient_last_visit(patient.id)
            self.patient_list.insert('', 'end', values=(
                patient.name,
                patient.phone,
                patient.email or '',
                last_visit.strftime("%Y-%m-%d") if last_visit else "No visits"
            ))

    def refresh_patient_list(self):
        """Refresh the entire patient list"""
        try:
            patients = self.db.get_all_patients()
            self.patient_list.delete(*self.patient_list.get_children())
            for patient in patients:
                last_visit = self.db.get_patient_last_visit(patient.id)
                self.patient_list.insert('', 'end', values=(
                    patient.name,
                    patient.phone,
                    patient.email or '',
                    last_visit.strftime("%Y-%m-%d") if last_visit else "No visits"
                ))
        except Exception as e:
            logger.error(f"Error refreshing patient list: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_refreshing_list")
            )
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class PatientsTab:
    def __init__(self, parent, db, lang):
        self.parent = parent
        self.db = db
        self.lang = lang
        self.setup_tab()

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

        # Add Refresh button
        ttk.Button(
            search_frame,
            text=self.lang.get_text("refresh"),
            command=self.refresh_patient_list
        ).pack(side='right', padx=5)

        # Patient list frame
        list_frame = ttk.Frame(self.parent)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Create patient list with scrollbar
        self.patient_list = ttk.Treeview(
            list_frame,
            columns=('id', 'name', 'phone', 'email', 'last_visit'),
            show='headings'
        )

        # Configure columns
        self.patient_list.heading('id', text="ID")
        self.patient_list.heading('name', text=self.lang.get_text("name"))
        self.patient_list.heading('phone', text=self.lang.get_text("phone"))
        self.patient_list.heading('email', text=self.lang.get_text("email"))
        self.patient_list.heading('last_visit', text=self.lang.get_text("last_visit"))

        # Set column widths
        self.patient_list.column('id', width=0, stretch=False)  # Hide ID column
        self.patient_list.column('name', width=150)
        self.patient_list.column('phone', width=120)
        self.patient_list.column('email', width=150)
        self.patient_list.column('last_visit', width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.patient_list.yview)
        self.patient_list.configure(yscrollcommand=scrollbar.set)

        # Pack list and scrollbar
        self.patient_list.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Buttons frame
        buttons_frame = ttk.Frame(self.parent)
        buttons_frame.pack(fill='x', padx=10, pady=5)

        # Edit button
        ttk.Button(
            buttons_frame,
            text=self.lang.get_text("edit_patient"),
            command=self.show_edit_patient_dialog
        ).pack(side='left', padx=5)

        # Delete button
        ttk.Button(
            buttons_frame,
            text=self.lang.get_text("delete_patient"),
            command=self.delete_selected_patient
        ).pack(side='left', padx=5)

        # Initial refresh
        self.refresh_patient_list()

    def show_add_patient_form(self):
        """Show dialog to add new patient"""
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

            label = ttk.Label(frame, text=label_text)
            label.pack(side='left')
            # Set minimum width for label
            label.configure(width=15)

            if field_name == "gender":
                var = tk.StringVar()
                combo = ttk.Combobox(
                    frame,
                    textvariable=var,
                    values=["Female", "Male", "Other"],
                    state="readonly"
                )
                combo.pack(side='left', fill='x', expand=True, padx=5)
                self.patient_form_vars[field_name] = var
            else:
                var = tk.StringVar()
                ttk.Entry(frame, textvariable=var).pack(side='left', fill='x', expand=True, padx=5)
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
            command=lambda: self.save_new_patient(dialog)
        ).pack(side='right', padx=5)

        ttk.Button(
            buttons_frame,
            text=self.lang.get_text("cancel"),
            command=dialog.destroy
        ).pack(side='right', padx=5)

    def save_new_patient(self, dialog):
        """Save new patient data"""
        required_fields = ['name', 'phone']
        for field in required_fields:
            if not self.patient_form_vars[field].get().strip():
                messagebox.showerror(
                    "Validation Error",
                    f"{field.capitalize()} is required!"
                )
                return

        try:
            # Create patient data
            patient_id = str(uuid.uuid4())
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            patient_data = {
                'id': patient_id,
                'name': self.patient_form_vars['name'].get().strip(),
                'phone': self.patient_form_vars['phone'].get().strip(),
                'email': self.patient_form_vars['email'].get().strip(),
                'address': self.patient_form_vars['address'].get().strip(),
                'birth_date': self.patient_form_vars['birth_date'].get().strip(),
                'gender': self.patient_form_vars['gender'].get(),
                'emergency_contact': self.patient_form_vars['emergency_contact'].get().strip(),
                'medical_history': self.medical_history_text.get('1.0', tk.END).strip(),
                'notes': self.notes_text.get('1.0', tk.END).strip(),
                'created_at': now,
                'updated_at': now
            }

            # Save to database
            self.db.add_patient(patient_data)

            # Show success message and close dialog
            messagebox.showinfo(
                "Success",
                self.lang.get_text("patient_added_successfully")
            )
            dialog.destroy()

            # Refresh the list
            self.refresh_patient_list()

        except Exception as e:
            logger.error(f"Error saving patient: {e}", exc_info=True)
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_saving_patient")
            )

    def refresh_patient_list(self):
        """Refresh the patient list"""
        self.update_ui_text()
        logger.debug("Starting patient list refresh")
        try:
            # Clear current list
            self.patient_list.delete(*self.patient_list.get_children())

            # Get all patients
            patients = self.db.get_all_patients()
            logger.debug(f"Retrieved {len(patients)} patients from database")

            if not patients:
                logger.debug("No patients found")
                return

            # Add each patient to the list
            for patient in patients:
                try:
                    # Get last visit
                    patient_id = patient['id']
                    logger.debug(f"Processing patient {patient['name']} ({patient_id})")

                    last_visit = self.db.get_patient_last_visit(patient_id)
                    last_visit_str = last_visit.strftime("%Y-%m-%d") if last_visit else "No visits"

                    # Insert into list
                    self.patient_list.insert('', 'end', values=(
                        patient_id,  # Hidden ID column
                        patient['name'],
                        patient['phone'],
                        patient.get('email', ''),
                        last_visit_str
                    ))
                    logger.debug(f"Added patient {patient['name']} to list")

                except Exception as e:
                    logger.error(f"Error processing patient {patient.get('name', 'Unknown')}: {e}")
                    continue

            logger.debug("Patient list refresh completed successfully")

        except Exception as e:
            logger.error(f"Error refreshing patient list: {e}", exc_info=True)
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_refreshing_list")
            )

    def on_patient_search(self, *args):
        """Handle patient search"""
        search_term = self.patient_search_var.get()
        if len(search_term) >= 2:
            try:
                # Clear current list
                self.patient_list.delete(*self.patient_list.get_children())

                # Search for patients
                patients = self.db.search_patients(search_term)
                logger.debug(f"Found {len(patients)} patients matching '{search_term}'")

                # Display results
                for patient in patients:
                    # Convert patient object to dictionary if needed
                    patient_data = patient if isinstance(patient, dict) else {
                        'id': patient.id,
                        'name': patient.name,
                        'phone': patient.phone,
                        'email': getattr(patient, 'email', '')
                    }

                    last_visit = self.db.get_patient_last_visit(patient_data['id'])
                    last_visit_str = last_visit.strftime("%Y-%m-%d") if last_visit else "No visits"

                    self.patient_list.insert('', 'end', values=(
                        patient_data['id'],
                        patient_data['name'],
                        patient_data['phone'],
                        patient_data.get('email', ''),
                        last_visit_str
                    ))

            except Exception as e:
                logger.error(f"Error searching patients: {e}", exc_info=True)
                messagebox.showerror(
                    "Error",
                    self.lang.get_text("error_searching_patients")
                )

    def show_edit_patient_dialog(self):
        """Show dialog to edit selected patient"""
        selection = self.patient_list.selection()
        if not selection:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_patient_to_edit")
            )
            return

        try:
            # Get selected patient ID (first column)
            values = self.patient_list.item(selection[0])['values']
            patient_id = values[0]

            # Get full patient data
            patient = self.db.get_patient(patient_id)
            if not patient:
                raise ValueError("Patient not found")

            # Create dialog
            dialog = tk.Toplevel(self.parent)
            dialog.title(self.lang.get_text("edit_patient"))
            dialog.geometry("600x800")
            dialog.transient(self.parent)
            dialog.grab_set()

            main_frame = ttk.Frame(dialog, style='Custom.TFrame')
            main_frame.pack(fill='both', expand=True, padx=20, pady=20)

            # Form fields
            fields = [
                ("name", "Name*:", patient.get('name', '')),
                ("phone", "Phone*:", patient.get('phone', '')),
                ("email", "Email:", patient.get('email', '')),
                ("address", "Address:", patient.get('address', '')),
                ("birth_date", "Birth Date:", patient.get('birth_date', '')),
                ("gender", "Gender:", patient.get('gender', '')),
                ("emergency_contact", "Emergency Contact:", patient.get('emergency_contact', ''))
            ]

            self.edit_form_vars = {}
            for field_name, label_text, value in fields:
                frame = ttk.Frame(main_frame)
                frame.pack(fill='x', pady=5)

                label = ttk.Label(frame, text=label_text)
                label.pack(side='left')
                label.configure(width=15)

                if field_name == "gender":
                    var = tk.StringVar(value=value)
                    combo = ttk.Combobox(
                        frame,
                        textvariable=var,
                        values=["Female", "Male", "Other"],
                        state="readonly"
                    )
                    combo.pack(side='left', fill='x', expand=True, padx=5)
                    self.edit_form_vars[field_name] = var
                else:
                    var = tk.StringVar(value=value)
                    ttk.Entry(frame, textvariable=var).pack(side='left', fill='x', expand=True, padx=5)
                    self.edit_form_vars[field_name] = var

            # Medical History
            ttk.Label(main_frame, text="Medical History:").pack(anchor='w', pady=(10, 5))
            self.edit_medical_history_text = tk.Text(main_frame, height=4)
            self.edit_medical_history_text.pack(fill='x', pady=5)
            if patient.get('medical_history'):
                self.edit_medical_history_text.insert('1.0', patient['medical_history'])

            # Notes
            ttk.Label(main_frame, text="Notes:").pack(anchor='w', pady=(10, 5))
            self.edit_notes_text = tk.Text(main_frame, height=4)
            self.edit_notes_text.pack(fill='x', pady=5)
            if patient.get('notes'):
                self.edit_notes_text.insert('1.0', patient['notes'])

            # Buttons
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill='x', pady=20)

            ttk.Button(
                buttons_frame,
                text=self.lang.get_text("save"),
                command=lambda: self.save_edited_patient(patient_id, dialog)
            ).pack(side='right', padx=5)

            ttk.Button(
                buttons_frame,
                text=self.lang.get_text("cancel"),
                command=dialog.destroy
            ).pack(side='right', padx=5)

        except Exception as e:
            logger.error(f"Error showing edit dialog: {e}", exc_info=True)
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_loading_patient")
            )

    def save_edited_patient(self, patient_id, dialog):
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
            # Prepare updated patient data
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
                'updated_at': now
            }

            # Update database
            self.db.update_patient(patient_data)

            # Show success message
            messagebox.showinfo(
                "Success",
                self.lang.get_text("patient_updated_successfully")
            )

            # Close dialog and refresh list
            dialog.destroy()
            self.refresh_patient_list()

        except Exception as e:
            logger.error(f"Error updating patient: {e}", exc_info=True)
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_updating_patient")
            )

    def delete_selected_patient(self):
        """Delete the selected patient"""
        selection = self.patient_list.selection()
        if not selection:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_patient_to_delete")
            )
            return

        try:
            # Get selected patient details
            values = self.patient_list.item(selection[0])['values']
            patient_id = values[0]  # ID is in first column
            patient_name = values[1]  # Name is in second column

            # Confirm deletion
            if not messagebox.askyesno(
                    "Confirm Delete",
                    f"Are you sure you want to delete patient: {patient_name}?"
            ):
                return

            # Delete from database
            if self.db.delete_patient(patient_id):
                # Remove from treeview
                self.patient_list.delete(selection[0])
                messagebox.showinfo(
                    "Success",
                    self.lang.get_text("patient_deleted_successfully")
                )
            else:
                messagebox.showerror(
                    "Error",
                    self.lang.get_text("error_deleting_patient")
                )

        except Exception as e:
            logger.error(f"Error deleting patient: {e}", exc_info=True)
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_deleting_patient")
            )

    def update_ui_text(self):
        """Update all UI text elements with current language"""
        try:
            # Update search label
            if hasattr(self, 'search_label'):
                self.search_label.configure(text=self.lang.get_text("search"))

            # Update buttons
            for widget in self.parent.winfo_children():
                if isinstance(widget, ttk.Button):
                    if "add_new_patient" in str(widget):
                        widget.configure(text=self.lang.get_text("add_new_patient"))
                    elif "refresh" in str(widget):
                        widget.configure(text=self.lang.get_text("refresh"))
                    elif "edit_patient" in str(widget):
                        widget.configure(text=self.lang.get_text("edit_patient"))
                    elif "delete_patient" in str(widget):
                        widget.configure(text=self.lang.get_text("delete_patient"))

            # Update treeview headers
            if hasattr(self, 'patient_list'):
                self.patient_list.heading('name', text=self.lang.get_text("name"))
                self.patient_list.heading('phone', text=self.lang.get_text("phone"))
                self.patient_list.heading('email', text=self.lang.get_text("email"))
                self.patient_list.heading('last_visit', text=self.lang.get_text("last_visit"))

        except Exception as e:
            logger.error(f"Error updating patient tab UI texts: {e}", exc_info=True)



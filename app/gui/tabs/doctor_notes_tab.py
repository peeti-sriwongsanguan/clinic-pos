import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
import logging
from PIL import Image, ImageTk
import uuid

logger = logging.getLogger(__name__)


class DoctorNotesTab(ttk.Frame):
    def __init__(self, parent, db, lang):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.lang = lang
        self.photo_references = []  # Keep photo references
        self.text_widgets = {}  # Dictionary to store text widgets
        self.current_patient = None
        self.pack(fill='both', expand=True)
        self.setup_tab()

    def setup_tab(self):
        """Setup doctor's notes interface"""
        # Create main containers
        left_frame = ttk.Frame(self)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        right_frame = ttk.Frame(self)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Patient Selection (Left Side)
        self.setup_patient_selection(left_frame)

        # Photos Section (Below patient list)
        self.setup_photo_section(left_frame)

        # Notes Section (Right Side)
        self.setup_notes_section(right_frame)

        # Create buttons
        self.setup_action_buttons(right_frame)

    def refresh_notes(self):
        """Refresh doctor notes tab display and translations"""
        try:
            # Refresh labels and button texts
            if hasattr(self, 'search_label'):
                self.search_label.config(text=self.lang.get_text("search"))

            if hasattr(self, 'patient_list'):
                # Refresh column headings
                self.patient_list.heading('name', text=self.lang.get_text("name"))
                self.patient_list.heading('phone', text=self.lang.get_text("phone"))
                self.patient_list.heading('last_visit', text=self.lang.get_text("last_visit"))

            # Refresh any buttons
            for widget in self.parent.winfo_children():
                if isinstance(widget, ttk.Button):
                    if 'search' in str(widget):
                        widget.config(text=self.lang.get_text("search"))
                    elif 'add' in str(widget):
                        widget.config(text=self.lang.get_text("add_new_patient"))

            # Refresh current search results if any
            if hasattr(self, 'patient_search_var'):
                search_term = self.patient_search_var.get()
                if search_term and len(search_term) >= 2:
                    self.on_patient_search()

        except Exception as e:
            logger.error(f"Error refreshing doctor notes: {e}", exc_info=True)

    def setup_patient_selection(self, parent):
        """Setup patient selection section"""
        # Patient Selection Frame
        patient_frame = ttk.LabelFrame(parent, text=self.lang.get_text("patient_selection"))
        patient_frame.pack(fill='x', padx=5, pady=5)

        # Search and Add Patient Frame
        search_frame = ttk.Frame(patient_frame)
        search_frame.pack(fill='x', padx=5, pady=5)

        # Search Label and Entry
        ttk.Label(search_frame, text=self.lang.get_text("search")).pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.search_patients_for_notes(self.search_var.get()))
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side='left', fill='x', expand=True, padx=5)

        # Add New Patient Button
        ttk.Button(
            search_frame,
            text=self.lang.get_text("add_new_patient"),
            command=self.show_add_patient_form
        ).pack(side='right', padx=5)

        # Patient list with scrollbar
        list_frame = ttk.Frame(patient_frame)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Add scrollbar
        y_scrollbar = ttk.Scrollbar(list_frame)
        y_scrollbar.pack(side='right', fill='y')

        # Create Treeview with scrollbar
        self.patient_list = ttk.Treeview(
            list_frame,
            columns=('name', 'phone', 'last_visit'),
            show='headings',
            yscrollcommand=y_scrollbar.set
        )

        # Configure columns
        self.patient_list.heading('name', text=self.lang.get_text("patient_name"))
        self.patient_list.heading('phone', text=self.lang.get_text("phone"))
        self.patient_list.heading('last_visit', text=self.lang.get_text("last_visit"))

        self.patient_list.column('name', width=150)
        self.patient_list.column('phone', width=120)
        self.patient_list.column('last_visit', width=100)

        # Pack list and scrollbar
        self.patient_list.pack(side='left', fill='both', expand=True)
        y_scrollbar.config(command=self.patient_list.yview)

        # Bind selection event
        self.patient_list.bind('<<TreeviewSelect>>', self.load_patient_notes)

    def show_add_patient_form(self):
        """Show dialog to add new patient"""
        dialog = tk.Toplevel(self)
        dialog.title(self.lang.get_text("add_new_patient"))
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog)
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
        for field_id, label_text in fields:
            frame = ttk.Frame(main_frame)
            frame.pack(fill='x', pady=5)

            label = ttk.Label(frame, text=label_text)
            label.pack(side='left')
            # Set minimum width for label using minwidth instead of width
            label.configure(width=15)

            if field_id == "gender":
                var = tk.StringVar()
                combo = ttk.Combobox(
                    frame,
                    textvariable=var,
                    values=["Female", "Male", "Other"],
                    state="readonly"
                )
                combo.pack(side='left', fill='x', expand=True, padx=5)
                self.patient_form_vars[field_id] = var
            else:
                var = tk.StringVar()
                entry = ttk.Entry(frame, textvariable=var)
                entry.pack(side='left', fill='x', expand=True, padx=5)
                self.patient_form_vars[field_id] = var

        # Medical History
        med_frame = ttk.LabelFrame(main_frame, text=self.lang.get_text("medical_history"))
        med_frame.pack(fill='x', pady=10)
        self.medical_history_text = tk.Text(med_frame, height=4)
        self.medical_history_text.pack(fill='x', padx=5, pady=5)

        # Notes
        notes_frame = ttk.LabelFrame(main_frame, text=self.lang.get_text("notes"))
        notes_frame.pack(fill='x', pady=10)
        self.notes_text = tk.Text(notes_frame, height=4)
        self.notes_text.pack(fill='x', padx=5, pady=5)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)

        ttk.Button(
            button_frame,
            text=self.lang.get_text("save"),
            command=lambda: self.save_new_patient(dialog)
        ).pack(side='right', padx=5)

        ttk.Button(
            button_frame,
            text=self.lang.get_text("cancel"),
            command=dialog.destroy
        ).pack(side='right', padx=5)

    def save_new_patient(self, dialog):
        """Save new patient data"""
        logger.debug("Starting save_new_patient process")

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
            # Create patient data
            patient_id = str(uuid.uuid4())
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Prepare data for database
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

            logger.debug(f"Prepared patient data: {patient_data}")

            # Save to database
            self.db.add_patient(patient_data)
            logger.info(f"Successfully added new patient with ID: {patient_id}")

            # Show success message
            messagebox.showinfo(
                "Success",
                self.lang.get_text("patient_added_successfully")
            )

            # Close the form and refresh the search
            dialog.destroy()
            self.search_var.set(patient_data['name'])  # Trigger search with new patient's name

        except Exception as e:
            logger.error(f"Error saving patient: {e}", exc_info=True)
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_saving_patient")
            )

    def search_patients_for_notes(self, search_term):
        """Search patients for notes"""
        logger.debug(f"Searching for patients with term: {search_term}")

        # Clear current patient info when starting a new search
        self.clear_patient_info()

        if len(search_term) < 2:
            return

        try:
            # Search for patients
            patients = self.db.search_patients(search_term)
            logger.debug(f"Found {len(patients)} patients")

            # Clear current list
            self.patient_list.delete(*self.patient_list.get_children())

            if patients:
                for patient in patients:
                    # Get last visit
                    last_visit = self.db.get_patient_last_visit(patient.id)
                    last_visit_str = last_visit.strftime("%Y-%m-%d") if last_visit else "No visits"

                    # Insert into treeview
                    self.patient_list.insert('', 'end', values=(
                        patient.name,
                        patient.phone,
                        last_visit_str
                    ))
        except Exception as e:
            logger.error(f"Error searching patients: {e}", exc_info=True)

    def clear_patient_info(self):
        """Clear all patient information displays"""
        # Clear patient list
        self.patient_list.delete(*self.patient_list.get_children())

        # Clear patient info label
        if hasattr(self, 'patient_info_label'):
            self.patient_info_label.config(text="")

        # Clear all text widgets
        for widget in self.text_widgets.values():
            widget.delete('1.0', tk.END)

        # Clear photos if they exist
        if hasattr(self, 'before_preview'):
            self.before_preview.config(image="")
            self.after_preview.config(image="")
            self.before_date.config(text="")
            self.after_date.config(text="")

        # Reset current patient
        self.current_patient = None
    def load_patient_notes(self, event=None):
        """Load selected patient's notes"""
        selection = self.patient_list.selection()
        if not selection:
            return

        try:
            # Get selected values
            values = self.patient_list.item(selection[0])['values']
            patient_name = values[0]

            # Get patient data
            patient_dict = self.db.get_patient_by_name(patient_name)
            if not patient_dict:
                return

            # Store current patient as an object with attributes
            self.current_patient = type('Patient', (), patient_dict)

            # Update displays
            self.update_patient_info(self.current_patient)

            # Load existing notes
            notes = self.db.get_patient_notes(self.current_patient.id)
            if notes:
                for section in ['medical_history', 'progress_notes', 'recommendations', 'next_steps']:
                    if section in self.text_widgets and notes.get(section):
                        self.text_widgets[section].delete('1.0', tk.END)
                        self.text_widgets[section].insert('1.0', notes.get(section, ''))

        except Exception as e:
            logger.error(f"Error loading patient notes: {e}", exc_info=True)
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_loading_notes")
            )

    def update_patient_info(self, patient):
        """Update patient info display"""
        try:
            last_visit = self.db.get_patient_last_visit(patient.id)
            last_visit_str = last_visit.strftime("%Y-%m-%d") if last_visit else "No previous visits"

            info_text = f"""
                    Patient: {patient.name}
                    Phone: {patient.phone}
                    Email: {patient.email or 'N/A'}
                    Last Visit: {last_visit_str}
            """
            self.patient_info_label.config(text=info_text)
        except Exception as e:
            logger.error(f"Error updating patient info: {e}")

    def load_existing_notes(self, patient):
        """Load existing notes for patient"""
        try:
            notes = self.db.get_patient_notes(patient.id)
            if notes:
                for section in self.text_widgets:
                    self.text_widgets[section].delete('1.0', tk.END)
                    if hasattr(notes, section):
                        self.text_widgets[section].insert('1.0', getattr(notes, section) or '')
        except Exception as e:
            logger.error(f"Error loading notes: {e}")

    def setup_photo_section(self, parent):
        """Setup photo preview section with before/after comparison"""
        photo_frame = ttk.LabelFrame(parent, text=self.lang.get_text("progress_photos"))
        photo_frame.pack(fill='x', padx=5, pady=5)

        # Before/After comparison frame
        comparison_frame = ttk.Frame(photo_frame)
        comparison_frame.pack(fill='x', padx=5, pady=5)

        # Before photo
        before_frame = ttk.LabelFrame(comparison_frame, text=self.lang.get_text("before"))
        before_frame.pack(side='left', fill='both', expand=True, padx=5)

        self.before_preview = ttk.Label(before_frame)
        self.before_preview.pack(padx=5, pady=5)
        self.before_date = ttk.Label(before_frame, text="")
        self.before_date.pack()

        # After photo
        after_frame = ttk.LabelFrame(comparison_frame, text=self.lang.get_text("after"))
        after_frame.pack(side='right', fill='both', expand=True, padx=5)

        self.after_preview = ttk.Label(after_frame)
        self.after_preview.pack(padx=5, pady=5)
        self.after_date = ttk.Label(after_frame, text="")
        self.after_date.pack()

        # Photo controls
        controls_frame = ttk.Frame(photo_frame)
        controls_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            controls_frame,
            text=self.lang.get_text("add_photos"),
            command=self.add_progress_photos
        ).pack(side='left', padx=5)

        ttk.Button(
            controls_frame,
            text=self.lang.get_text("view_all_photos"),
            command=self.view_all_photos
        ).pack(side='left', padx=5)

        ttk.Button(
            controls_frame,
            text=self.lang.get_text("select_comparison"),
            command=self.select_comparison_photos
        ).pack(side='left', padx=5)

    def add_progress_photos(self):
        """Add progress photos to patient record"""
        if not self.current_patient:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_patient_first")
            )
            return

        try:
            filetypes = [
                ('Image files', '*.jpg *.jpeg *.png'),
                ('All files', '*.*')
            ]

            filenames = filedialog.askopenfilenames(
                title=self.lang.get_text("select_photos"),
                filetypes=filetypes
            )

            if filenames:
                photo_paths = []
                for filename in filenames:
                    photo_path = self.save_photo(filename)
                    photo_paths.append(photo_path)

                # Update database
                self.db.add_patient_photos(self.current_patient.id, photo_paths)
                self.load_patient_photos(self.current_patient)

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

    def save_photo(self, source_path):
        """Save photo to storage with optimizations"""
        try:
            # Create photos directory if it doesn't exist
            photos_dir = os.path.join('static', 'photos', 'progress', str(self.current_patient.id))
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
            logger.error(f"Error saving photo: {e}")
            raise

    def view_all_photos(self):
        """Show all patient photos in a new window"""
        if not self.current_patient:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_patient_first")
            )
            return

        photos = self.db.get_patient_photos(self.current_patient.id)
        if not photos:
            messagebox.showinfo(
                "Info",
                self.lang.get_text("no_photos")
            )
            return

        # Create photo viewer window
        viewer = tk.Toplevel(self)
        viewer.title(self.lang.get_text("photo_viewer"))
        viewer.geometry("800x600")

        # Create scrollable frame
        canvas = tk.Canvas(viewer)
        scrollbar = ttk.Scrollbar(viewer, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add photos to grid
        row = 0
        col = 0
        for photo_path in sorted(photos, key=lambda x: os.path.basename(x).split('_')[1], reverse=True):
            if os.path.exists(photo_path):
                photo_frame = self.create_photo_frame(scrollable_frame, photo_path)
                photo_frame.grid(row=row, column=col, padx=5, pady=5)

                col += 1
                if col > 2:  # 3 photos per row
                    col = 0
                    row += 1

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_photo_frame(self, parent, photo_path):
        """Create a frame containing photo and date"""
        frame = ttk.Frame(parent)

        try:
            with Image.open(photo_path) as img:
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photo_references.append(photo)

                label = ttk.Label(frame, image=photo)
                label.image = photo
                label.pack()

            # Add date from filename
            date_str = os.path.basename(photo_path).split('_')[1]
            date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
            ttk.Label(frame, text=date).pack()

        except Exception as e:
            logger.error(f"Error creating photo frame: {e}")
            ttk.Label(frame, text="Error loading photo").pack()

        return frame

    def setup_notes_section(self, parent):
        """Setup the notes section with all text fields"""
        notes_frame = ttk.Frame(parent)
        notes_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Patient info display
        info_frame = ttk.LabelFrame(notes_frame, text=self.lang.get_text("patient_info"))
        info_frame.pack(fill='x', padx=5, pady=5)
        self.patient_info_label = ttk.Label(info_frame, text="")
        self.patient_info_label.pack(fill='x', padx=5, pady=5)

        # Create text sections
        sections = [
            ("medical_history", "Medical History", 4),
            ("progress_notes", "Progress Notes", 4),
            ("recommendations", "Recommendations", 4),
            ("next_steps", "Next Steps", 4)
        ]

        for section_id, title, height in sections:
            frame = ttk.LabelFrame(notes_frame, text=self.lang.get_text(title))
            frame.pack(fill='x', padx=5, pady=5)

            text_widget = tk.Text(frame, height=height, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)

            text_widget.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

            self.text_widgets[section_id] = text_widget

    def setup_action_buttons(self, parent):
        """Setup action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', padx=5, pady=10)

        # Save button
        ttk.Button(
            button_frame,
            text=self.lang.get_text("save"),
            command=self.save_notes
        ).pack(side='right', padx=5)

        # Print button
        ttk.Button(
            button_frame,
            text=self.lang.get_text("print"),
            command=self.print_notes
        ).pack(side='right', padx=5)

        # Clear button
        ttk.Button(
            button_frame,
            text=self.lang.get_text("clear"),
            command=self.clear_form
        ).pack(side='right', padx=5)

    def select_comparison_photos(self):
        """Show dialog to select before/after photos for comparison"""
        if not self.current_patient:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_patient_first")
            )
            return

        photos = self.db.get_patient_photos(self.current_patient.id)
        if not photos:
            messagebox.showinfo(
                "Info",
                self.lang.get_text("no_photos")
            )
            return

        # Create photo selector window
        selector = tk.Toplevel(self)
        selector.title(self.lang.get_text("select_comparison_photos"))
        selector.geometry("900x600")

        # Create labeled frames for before/after selection
        before_frame = ttk.LabelFrame(selector, text=self.lang.get_text("select_before"))
        before_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        after_frame = ttk.LabelFrame(selector, text=self.lang.get_text("select_after"))
        after_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        # Create scrollable frames
        before_canvas = self.create_scrollable_frame(before_frame)
        after_canvas = self.create_scrollable_frame(after_frame)

        # Clear any previous selections
        self.selected_before = None
        self.selected_after = None

        # Add photos
        sorted_photos = sorted(photos, key=lambda x: os.path.basename(x).split('_')[1], reverse=True)
        for photo_path in sorted_photos:
            if os.path.exists(photo_path):
                self.add_selectable_photo(before_canvas.frame, photo_path, 'before')
                self.add_selectable_photo(after_canvas.frame, photo_path, 'after')

        # Add confirm button
        ttk.Button(
            selector,
            text=self.lang.get_text("confirm_selection"),
            command=lambda: self.apply_photo_selection(selector)
        ).pack(side='bottom', pady=10)

    def create_scrollable_frame(self, parent):
        """Create a scrollable frame"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)

        frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Store frame reference
        canvas.frame = frame
        return canvas

    def add_selectable_photo(self, parent, photo_path, photo_type):
        """Add a selectable photo to the frame"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=5, pady=5)

        try:
            with Image.open(photo_path) as img:
                img.thumbnail((180, 180), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photo_references.append(photo)

                label = ttk.Label(frame, image=photo)
                label.image = photo
                label.pack()

            # Add date label
            date_str = os.path.basename(photo_path).split('_')[1]
            date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
            ttk.Label(frame, text=date).pack()

            # Add select button
            ttk.Button(
                frame,
                text=self.lang.get_text("select"),
                command=lambda: self.select_photo(photo_path, photo_type, date)
            ).pack(pady=5)

        except Exception as e:
            logger.error(f"Error adding selectable photo: {e}")
            ttk.Label(frame, text="Error loading photo").pack()

    def select_photo(self, photo_path, photo_type, date):
        """Handle photo selection"""
        if photo_type == 'before':
            self.selected_before = (photo_path, date)
        else:
            self.selected_after = (photo_path, date)

    def apply_photo_selection(self, dialog):
        """Apply the selected photos to the comparison view"""
        if not self.selected_before or not self.selected_after:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_both_photos")
            )
            return

        try:
            # Update before photo
            with Image.open(self.selected_before[0]) as img:
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photo_references.append(photo)
                self.before_preview.configure(image=photo)
                self.before_preview.image = photo
                self.before_date.configure(text=self.selected_before[1])

            # Update after photo
            with Image.open(self.selected_after[0]) as img:
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photo_references.append(photo)
                self.after_preview.configure(image=photo)
                self.after_preview.image = photo
                self.after_date.configure(text=self.selected_after[1])

            dialog.destroy()

        except Exception as e:
            logger.error(f"Error applying photo selection: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_updating_photos")
            )

    def load_patient_photos(self, patient):
        """Load patient's photos"""
        try:
            photos = self.db.get_patient_photos(patient.id)
            if photos:
                self.update_photo_previews(photos)
        except Exception as e:
            logger.error(f"Error loading photos: {e}")

    def update_photo_previews(self, photos):
        """Update photo preview displays with most recent photos"""
        try:
            # Sort photos by date
            sorted_photos = sorted(photos, key=lambda x: os.path.basename(x).split('_')[1], reverse=True)

            if len(sorted_photos) >= 1:
                # Update before photo (oldest in selection)
                self.update_photo_display(
                    sorted_photos[-1],
                    self.before_preview,
                    self.before_date
                )

            if len(sorted_photos) >= 2:
                # Update after photo (most recent)
                self.update_photo_display(
                    sorted_photos[0],
                    self.after_preview,
                    self.after_date
                )
        except Exception as e:
            logger.error(f"Error updating photo previews: {e}")

    def update_photo_display(self, photo_path, preview_label, date_label):
        """Update a single photo display"""
        try:
            with Image.open(photo_path) as img:
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photo_references.append(photo)
                preview_label.configure(image=photo)
                preview_label.image = photo

                # Update date label
                date_str = os.path.basename(photo_path).split('_')[1]
                date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
                date_label.configure(text=date)
        except Exception as e:
            logger.error(f"Error updating photo display: {e}")

    def save_notes(self):
        """Save the current notes"""
        if not self.current_patient:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_patient_first")
            )
            return

        try:
            notes_data = {
                'patient_id': self.current_patient.id,
                'created_at': datetime.now()
            }

            # Collect text from all sections
            for section, widget in self.text_widgets.items():
                notes_data[section] = widget.get('1.0', tk.END).strip()

            self.db.save_doctor_notes(notes_data)
            messagebox.showinfo(
                "Success",
                self.lang.get_text("notes_saved")
            )

        except Exception as e:
            logger.error(f"Error saving notes: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_saving_notes")
            )

    def clear_form(self):
        """Clear all form fields"""
        for widget in self.text_widgets.values():
            widget.delete('1.0', tk.END)
        self.patient_info_label.config(text="")
        self.current_patient = None
        self.before_preview.config(image="")
        self.after_preview.config(image="")
        self.before_date.config(text="")
        self.after_date.config(text="")

    def print_notes(self):
        """Print current notes as PDF"""
        if not self.current_patient:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_patient_first")
            )
            return

        try:
            # Prepare notes data
            notes_data = {
                'patient_name': self.current_patient.name,
                'date': datetime.now().strftime("%Y-%m-%d")
            }

            # Add text from all sections
            for section, widget in self.text_widgets.items():
                notes_data[section] = widget.get('1.0', tk.END).strip()

            # Generate PDF
            filename = f"doctor_notes_{self.current_patient.name}_{datetime.now().strftime('%Y%m%d')}.pdf"
            self.generate_notes_pdf(notes_data, filename)

            messagebox.showinfo(
                "Success",
                self.lang.get_text("notes_printed")
            )

        except Exception as e:
            logger.error(f"Error printing notes: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_printing_notes")
            )

    def generate_notes_pdf(self, notes_data, filename):
        """Generate PDF for notes"""
        try:
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
            section_titles = {
                'medical_history': "Medical History",
                'progress_notes': "Progress Notes",
                'recommendations': "Recommendations",
                'next_steps': "Next Steps"
            }

            for section, title in section_titles.items():
                content = notes_data.get(section, '')
                if content:
                    story.append(Paragraph(title, styles['Heading2']))
                    story.append(Paragraph(content, styles['Normal']))
                    story.append(Spacer(1, 12))

            doc.build(story)

        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise


from tkinter import filedialog
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)


class InventoryTab(ttk.Frame):
    def __init__(self, parent, db, lang):
        super().__init__(parent)
        self.parent = parent  # Save reference to parent
        self.db = db
        self.lang = lang
        self.setup_tab()

    def setup_tab(self):
        """Setup product inventory management tab"""
        # Create main containers
        top_frame = ttk.Frame(self)  # Changed from self.inventory_tab to self
        top_frame.pack(fill='x', padx=5, pady=5)

        bottom_frame = ttk.Frame(self)  # Changed from self.inventory_tab to self
        bottom_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Top controls
        controls_frame = ttk.LabelFrame(top_frame, text=self.lang.get_text("inventory_controls"))
        controls_frame.pack(fill='x', padx=5, pady=5)

        # Search frame
        search_frame = ttk.Frame(controls_frame)
        search_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(search_frame, text=self.lang.get_text("search")).pack(side='left', padx=5)
        self.inventory_search_var = tk.StringVar()
        self.inventory_search_var.trace('w', self.on_inventory_search)
        ttk.Entry(search_frame, textvariable=self.inventory_search_var).pack(side='left', fill='x', expand=True, padx=5)

        # Filter by category
        category_frame = ttk.Frame(controls_frame)
        category_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(category_frame, text=self.lang.get_text("category")).pack(side='left', padx=5)
        self.category_var = tk.StringVar()
        self.category_combobox = ttk.Combobox(
            category_frame,
            textvariable=self.category_var,
            values=['All'] + self.get_product_categories(),
            state='readonly'
        )
        self.category_combobox.pack(side='left', padx=5)
        self.category_combobox.bind('<<ComboboxSelected>>', self.filter_inventory)

        # Buttons frame
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            button_frame,
            text=self.lang.get_text("add_product"),
            command=self.show_add_product_dialog
        ).pack(side='left', padx=5)

        ttk.Button(
            button_frame,
            text=self.lang.get_text("stock_adjustment"),
            command=self.show_stock_adjustment_dialog
        ).pack(side='left', padx=5)

        ttk.Button(
            button_frame,
            text=self.lang.get_text("export_inventory"),
            command=self.export_inventory
        ).pack(side='right', padx=5)

        # Inventory list
        list_frame = ttk.LabelFrame(bottom_frame, text=self.lang.get_text("inventory_list"))
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create treeview with scrollbar
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame)
        y_scrollbar.pack(side='right', fill='y')

        x_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal')
        x_scrollbar.pack(side='bottom', fill='x')

        # Treeview
        columns = (
            'code', 'name', 'category', 'stock', 'min_stock',
            'unit', 'cost', 'price', 'last_updated'
        )

        self.inventory_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )

        # Configure scrollbars
        y_scrollbar.config(command=self.inventory_tree.yview)
        x_scrollbar.config(command=self.inventory_tree.xview)

        # Configure columns
        column_configs = {
            'code': ('Code', 100),
            'name': ('Product Name', 200),
            'category': ('Category', 100),
            'stock': ('Stock', 80),
            'min_stock': ('Min Stock', 80),
            'unit': ('Unit', 80),
            'cost': ('Cost', 100),
            'price': ('Price', 100),
            'last_updated': ('Last Updated', 150)
        }

        for col, (text, width) in column_configs.items():
            self.inventory_tree.heading(col, text=self.lang.get_text(text))
            self.inventory_tree.column(col, width=width)

        self.inventory_tree.pack(fill='both', expand=True)

        # Bind double-click for editing
        self.inventory_tree.bind('<Double-1>', self.edit_product)

        # Load initial data
        self.refresh_inventory()

    def show_add_product_dialog(self):
        """Show dialog to add new product"""
        dialog = tk.Toplevel(self)  # Changed from self.root to self
        dialog.title(self.lang.get_text("add_product"))
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()

        # Rest of the method remains the same...

    def edit_product(self, event=None):
        """Handle product editing"""
        selection = self.inventory_tree.selection()
        if not selection:
            messagebox.showwarning(
                "Warning",
                self.lang.get_text("select_product_first")
            )
            return

        try:
            # Get product code from selected item
            product_code = self.inventory_tree.item(selection[0])['values'][0]
            product = self.db.get_product(product_code)

            # Create edit dialog
            dialog = tk.Toplevel(self)
            dialog.title(self.lang.get_text("edit_product"))
            dialog.geometry("500x600")
            dialog.transient(self)
            dialog.grab_set()

            # Create main frame
            form_frame = ttk.Frame(dialog)
            form_frame.pack(fill='both', expand=True, padx=20, pady=20)

            # Form fields with current values
            fields = [
                ('code', 'Product Code', product.code),
                ('name', 'Product Name', product.name),
                ('category', 'Category', product.category),
                ('unit', 'Unit', product.unit),
                ('cost', 'Cost', str(product.cost)),
                ('price', 'Price', str(product.price)),
                ('min_stock', 'Minimum Stock', str(product.min_stock))
            ]

            self.edit_vars = {}

            for field, label, value in fields:
                frame = ttk.Frame(form_frame)
                frame.pack(fill='x', pady=5)

                ttk.Label(
                    frame,
                    text=self.lang.get_text(label),
                    width=15
                ).pack(side='left')

                if field == 'category':
                    var = tk.StringVar(value=value)
                    combo = ttk.Combobox(
                        frame,
                        textvariable=var,
                        values=self.get_product_categories(),
                        state='readonly'
                    )
                    combo.pack(side='left', fill='x', expand=True)
                    self.edit_vars[field] = var
                elif field == 'code':
                    # Product code should be read-only
                    ttk.Label(
                        frame,
                        text=value
                    ).pack(side='left', fill='x', expand=True)
                    self.edit_vars[field] = tk.StringVar(value=value)
                else:
                    var = tk.StringVar(value=value)
                    ttk.Entry(
                        frame,
                        textvariable=var
                    ).pack(side='left', fill='x', expand=True)
                    self.edit_vars[field] = var

            # Description
            ttk.Label(
                form_frame,
                text=self.lang.get_text("description")
            ).pack(anchor='w', pady=5)

            self.edit_description = tk.Text(form_frame, height=4)
            self.edit_description.pack(fill='x', pady=5)
            self.edit_description.insert('1.0', product.description or '')

            # Stock information
            stock_frame = ttk.LabelFrame(form_frame, text=self.lang.get_text("stock_info"))
            stock_frame.pack(fill='x', pady=10)

            ttk.Label(
                stock_frame,
                text=f"{self.lang.get_text('current_stock')}: {product.stock} {product.unit}"
            ).pack(pady=5)

            # Buttons
            button_frame = ttk.Frame(form_frame)
            button_frame.pack(fill='x', pady=20)

            ttk.Button(
                button_frame,
                text=self.lang.get_text("save"),
                command=lambda: self.save_product_edit(product_code, dialog)
            ).pack(side='right', padx=5)

            ttk.Button(
                button_frame,
                text=self.lang.get_text("cancel"),
                command=dialog.destroy
            ).pack(side='right', padx=5)

        except Exception as e:
            logger.error(f"Error editing product: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_editing_product")
            )

    def save_product_edit(self, product_code, dialog):
        """Save edited product information"""
        try:
            # Validate required fields
            required_fields = ['name', 'category', 'unit', 'price']
            for field in required_fields:
                if not self.edit_vars[field].get().strip():
                    messagebox.showerror(
                        "Error",
                        self.lang.get_text(f"{field}_required")
                    )
                    return

            # Validate numeric fields
            numeric_fields = ['price', 'cost', 'min_stock']
            for field in numeric_fields:
                try:
                    if self.edit_vars[field].get():
                        float(self.edit_vars[field].get())
                except ValueError:
                    messagebox.showerror(
                        "Error",
                        self.lang.get_text(f"invalid_{field}")
                    )
                    return

            # Prepare product data
            product_data = {
                'code': product_code,
                'name': self.edit_vars['name'].get().strip(),
                'category': self.edit_vars['category'].get(),
                'unit': self.edit_vars['unit'].get().strip(),
                'cost': float(self.edit_vars['cost'].get() or 0),
                'price': float(self.edit_vars['price'].get()),
                'min_stock': float(self.edit_vars['min_stock'].get() or 0),
                'description': self.edit_description.get('1.0', tk.END).strip()
            }

            # Update product in database
            self.db.update_product(product_data)

            messagebox.showinfo(
                "Success",
                self.lang.get_text("product_updated")
            )

            dialog.destroy()
            self.refresh_inventory()

        except Exception as e:
            logger.error(f"Error saving product edit: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_saving_product")
            )

    def export_inventory(self):
        """Export inventory to Excel file"""


        try:
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ],
                initialfile=f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            )

            if not filename:
                return

            # Get all products
            products = self.db.get_products()

            # Convert to DataFrame
            data = [{
                'Code': p.code,
                'Name': p.name,
                'Category': p.category,
                'Stock': p.stock,
                'Min Stock': p.min_stock,
                'Unit': p.unit,
                'Cost': p.cost,
                'Price': p.price,
                'Description': p.description,
                'Last Updated': p.last_updated.strftime("%Y-%m-%d %H:%M")
            } for p in products]

            df = pd.DataFrame(data)

            # Create Excel writer
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Write main data
                df.to_excel(writer, sheet_name='Inventory', index=False)

                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Inventory']

                # Adjust column widths
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(col)
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

                # Add title and date
                title_sheet = workbook.create_sheet('Info', 0)
                title_sheet['A1'] = 'Inventory Export Report'
                title_sheet['A2'] = f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
                title_sheet['A3'] = f'Total Products: {len(products)}'

                # Add summary
                summary_data = df.groupby('Category').agg({
                    'Code': 'count',
                    'Stock': 'sum',
                    'Cost': 'sum',
                    'Price': 'mean'
                }).round(2)

                summary_data.to_excel(writer, sheet_name='Summary', index=True)

            messagebox.showinfo(
                "Success",
                self.lang.get_text("export_complete")
            )

        except Exception as e:
            logger.error(f"Error exporting inventory: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_exporting_inventory")
            )

    def get_product_categories(self):
        """Get list of product categories"""
        try:
            categories = self.db.get_product_categories()
            return [cat.name for cat in categories]
        except Exception as e:
            logger.error(f"Error getting product categories: {e}")
            return []

    def on_inventory_search(self, *args):
        """Handle inventory search"""
        search_term = self.inventory_search_var.get()
        category = self.category_var.get()
        self.refresh_inventory(search_term, category)

    def filter_inventory(self, event=None):
        """Filter inventory by category"""
        search_term = self.inventory_search_var.get()
        category = self.category_var.get()
        self.refresh_inventory(search_term, category)

    def refresh_inventory(self, search_term="", category="All"):
        """Refresh inventory display"""
        try:
            products = self.db.get_products(search_term, category)
            self.inventory_tree.delete(*self.inventory_tree.get_children())

            for product in products:
                self.inventory_tree.insert('', 'end', values=(
                    product.code,
                    product.name,
                    product.category,
                    product.stock,
                    product.min_stock,
                    product.unit,
                    f"฿{product.cost:,.2f}",
                    f"฿{product.price:,.2f}",
                    product.last_updated.strftime("%Y-%m-%d %H:%M")
                ))
        except Exception as e:
            logger.error(f"Error refreshing inventory: {e}")
            messagebox.showerror(
                "Error",
                self.lang.get_text("error_refreshing_inventory")
            )
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
from .theme_config import ThemeConfig


class BeautyClinicPOS:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_branding()
        self.create_styles()
        self.setup_gui()

    def setup_window(self):
        self.root.title("Beauty Clinic POS")
        self.root.geometry("1280x800")

        # Configure the window
        self.root.configure(bg=ThemeConfig.PRIMARY_PINK)

        # Make it responsive
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
            logo_path = os.path.join('static','assets', 'logo.jpeg')
            logo_img = Image.open(logo_path)
            # Resize logo to appropriate height (80px)
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

        except Exception as e:
            print(f"Error loading logo: {e}")
            # Fallback text if logo cannot be loaded
            self.logo_label = tk.Label(
                self.header_frame,
                text="BEAUTY CLINIC",
                font=ThemeConfig.TITLE_FONT,
                bg=ThemeConfig.WHITE,
                fg=ThemeConfig.DARK_PINK
            )
            self.logo_label.pack(side='left', padx=20, pady=10)

    def create_styles(self):
        # Create custom styles for widgets
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

    def create_invoice_template(self):
        self.invoice_template = {
            'company_name': 'Wellness by BFF',
            'address': '239 Asoke soi. Sukhumwit Rd, Wattana Bangkok 10110',
            'phone': '081-847-0000',
            'email': 'ice@dricebeauty.com',
            'website': 'www.dricebeauty.com',
            'logo_path': os.path.join('assets', 'logo.png'),
            'footer_text': 'Thank you for choosing our services!',
            'terms_conditions': [
                'Payment is due at the time of service',
                'Cancellations require 24-hour notice',
                'Gift certificates are non-refundable'
            ]
        }

    def generate_invoice(self, transaction_data):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        doc = SimpleDocTemplate(
            f"invoices/invoice_{transaction_data['invoice_number']}.pdf",
            pagesize=letter
        )

        # Create the document content
        story = []

        # Add logo
        if os.path.exists(self.invoice_template['logo_path']):
            img = Image(self.invoice_template['logo_path'], width=200, height=100)
            story.append(img)

        # Add company information
        styles = getSampleStyleSheet()
        story.append(Paragraph(self.invoice_template['company_name'], styles['Title']))
        story.append(Paragraph(self.invoice_template['address'], styles['Normal']))
        story.append(Paragraph(self.invoice_template['phone'], styles['Normal']))

        # Add invoice details
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Invoice #{transaction_data['invoice_number']}", styles['Heading1']))
        story.append(Paragraph(f"Date: {transaction_data['date']}", styles['Normal']))
        story.append(Paragraph(f"Patient: {transaction_data['patient_name']}", styles['Normal']))

        # Add items table
        data = [['Service', 'Quantity', 'Price', 'Total']]
        for item in transaction_data['items']:
            data.append([
                item['service'],
                item['quantity'],
                f"${item['price']:.2f}",
                f"${item['total']:.2f}"
            ])

        table = Table(data)
        table.setStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.pink),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.pink)
        ])
        story.append(table)

        # Add total
        story.append(Paragraph(
            f"Total Amount: ${transaction_data['total_amount']:.2f}",
            styles['Heading2']
        ))

        # Add footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(self.invoice_template['footer_text'], styles['Normal']))

        # Generate PDF
        doc.build(story)

# Example usage
if __name__ == "__main__":
    pos = BeautyClinicPOS()
    pos.root.mainloop()
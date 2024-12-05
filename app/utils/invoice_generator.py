import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class InvoiceGenerator:
    def __init__(self):
        self.invoice_template = {
            'company_name': 'Wellness by BFF',
            'address': '239 Asoke soi. Sukhumwit Rd, Wattana Bangkok 10110',
            'phone': '081-847-0000',
            'email': 'ice@dricebeauty.com',
            'website': 'www.dricebeauty.com',
            'logo_path': os.path.join('static', 'assets', 'logo.jpeg'),
            'footer_text': 'Thank you for choosing our services!',
            'terms_conditions': [
                'Payment is due at the time of service',
                'Cancellations require 24-hour notice',
                'Gift certificates are non-refundable'
            ]
        }

    def generate_invoice(self, transaction_data):
        doc = SimpleDocTemplate(
            f"invoices/invoice_{transaction_data['invoice_number']}.pdf",
            pagesize=letter
        )

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
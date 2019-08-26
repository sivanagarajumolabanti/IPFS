import os
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def call_pdf(data, hashkey=None):
    pdf_file_name = os.path.join(settings.MEDIA_ROOT, "genpdf", "%s.pdf" % data['name'])
    canv = canvas.Canvas(pdf_file_name, pagesize=letter)
    canv.setLineWidth(.3)
    canv.setFont('Helvetica', 12)

    canv.drawString(50, 603, 'Contract Name:')
    canv.drawString(170, 603, data['name'])

    canv.drawString(50, 540, 'Amount:')
    canv.drawString(170, 540, data['amount'])

    canv.drawString(50, 520, 'Installments:')
    canv.drawString(170, 520, data['installments'])

    canv.drawString(50, 500, 'Amount Paid:')
    canv.drawString(170, 500, data['amount_paid'])

    if data.get('apprcomments'):
        canv.drawString(50, 480, 'Comments:')
        canv.drawString(170, 480, data.get('apprcomments'))

    if hashkey:
        canv.drawString(50, 460, 'File Uploaded Hash:')
        canv.drawString(170, 460, hashkey)
    canv.save()
    return pdf_file_name

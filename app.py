import os
import django
from django.conf import settings
from django.http import HttpResponse
from django.urls import path
from django.core.wsgi import get_wsgi_application
import requests
import pandas as pd
from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

if not settings.configured:
    settings.configure(
        DEBUG=False,
        SECRET_KEY='your-secret-key',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
        MIDDLEWARE=[],  
    )
django.setup()

def generate_pdf(request):
    if request.method != 'POST':
        return HttpResponse("Invalid request method. Use POST.", status=405)

    # orderID = request.POST.get('oid')
    # paymentID = request.POST.get('rp_payment_id')

    Charting_Link = "https://chartink.com/screener/"
    Charting_url = "https://chartink.com/screener/process"
    Condition = "( {57960} ( [0] 15 minute close > [-1] 15 minute max ( 20 , [0] 15 minute close ) and [0] 15 minute volume > [0] 15 minute sma ( volume,20 ) ) ) "

    def GetDataFromChartink(payload):
        payload = {'scan_clause': payload}
        with requests.Session() as s:
            r = s.get(Charting_Link)
            soup = BeautifulSoup(r.text, "html.parser")
            csrf = soup.select_one("[name='csrf-token']")['content']
            s.headers['x-csrf-token'] = csrf
            r = s.post(Charting_url, data=payload)
            df = pd.DataFrame(r.json()['data'])
        return df

    data = GetDataFromChartink(Condition)
    data = data.sort_values(by='per_chg', ascending=False)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []

    logo_path = "rsi_logo.png"
    try:
        logo = Image(logo_path, width=100, height=100)
        elements.append(logo)
    except Exception as e:
        print("Logo not found! Skipping logo...", e)

    styles = getSampleStyleSheet()
    title = Paragraph("<b>Daily VST Stock Report</b>", styles["Title"])
    elements.append(title)

    table_data = [list(data.columns)] + data.values.tolist()
    table = Table(table_data)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey)
    ])
    table.setStyle(style)
    elements.append(table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type="application/pdf")
    response['Content-Disposition'] = 'attachment; filename="Daily_VST_Stock.pdf"'
    return response

urlpatterns = [
    path('generate-pdf/', generate_pdf),
]

application = get_wsgi_application()
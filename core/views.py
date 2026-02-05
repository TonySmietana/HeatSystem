# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Zaklad, Pomiar, ZrodloCiepla
import csv
import random
from django.template.loader import get_template
from xhtml2pdf import pisa  # Biblioteka do PDF działająca na Windows

def dashboard(request):
    zaklady = Zaklad.objects.all()
    # Pobierz 15 ostatnich pomiarów
    pomiary = Pomiar.objects.all().order_by('-data_wpisu')[:15]
    
    total_zysk = sum(p.oblicz_oszczednosc_roczna() for p in Pomiar.objects.all())
    
    context = {
        'zaklady': zaklady,
        'pomiary': pomiary,
        'total_zysk': round(total_zysk, 2)
    }
    return render(request, 'core/dashboard.html', context)

def uruchom_symulacje(request):
    """Generuje losowe dane dla czujników"""
    zrodla = ZrodloCiepla.objects.filter(aktywny_symulator=True)
    
    for z in zrodla:
        # Losowe wahania +/- 5%
        wahanie_t = random.uniform(-0.05, 0.05)
        wahanie_m = random.uniform(-0.02, 0.02)
        
        Pomiar.objects.create(
            zrodlo=z,
            typ_wpisu='SENSOR',
            temp_zrodla=round(z.nominalna_temp * (1 + wahanie_t), 1),
            przeplyw_masowy=round(z.nominalny_przeplyw * (1 + wahanie_m), 2),
            temp_otoczenia=20.0,
            sprawnosc_odzysku=0.85
        )
    return redirect('dashboard')

def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="raport.csv"'
    writer = csv.writer(response)
    writer.writerow(['Zrodlo', 'Typ', 'Temp', 'Moc [kW]', 'Zysk [PLN]'])
    
    for p in Pomiar.objects.all():
        writer.writerow([
            p.zrodlo.nazwa, p.typ_wpisu, p.temp_zrodla, 
            p.oblicz_moc_odzysku_kw(), p.oblicz_oszczednosc_roczna()
        ])
    return response

def generuj_raport_pdf(request, zaklad_id):
    zaklad = get_object_or_404(Zaklad, id=zaklad_id)
    pomiary = Pomiar.objects.filter(zrodlo__zaklad=zaklad).order_by('-data_wpisu')[:50]
    
    template_path = 'core/pdf_template.html'
    context = {'zaklad': zaklad, 'pomiary': pomiary}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="raport_{zaklad.id}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Wystąpił błąd przy tworzeniu PDF')
    return response
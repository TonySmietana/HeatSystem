from django.db import models
from django.contrib.auth.models import User

class Zaklad(models.Model):
    nazwa = models.CharField(max_length=100)
    lokalizacja = models.CharField(max_length=100)
    koszt_energii_mwh = models.FloatField(help_text="Koszt energii w PLN/MWh")

    def __str__(self):
        return self.nazwa

class ZrodloCiepla(models.Model):
    MEDIA_CHOICES = [
        ('woda', 'Woda'),
        ('powietrze', 'Powietrze'),
        ('spaliny', 'Spaliny'),
        ('olej', 'Olej Termalny'),
    ]
    zaklad = models.ForeignKey(Zaklad, on_delete=models.CASCADE)
    nazwa = models.CharField(max_length=100)
    medium = models.CharField(max_length=20, choices=MEDIA_CHOICES)
    czas_pracy_h_rok = models.IntegerField()
    
    # Pola dla Symulatora
    nominalna_temp = models.FloatField(default=100.0, help_text="Typowa temperatura pracy [°C]")
    nominalny_przeplyw = models.FloatField(default=1.0, help_text="Typowy przepływ [kg/s]")
    aktywny_symulator = models.BooleanField(default=False, help_text="Czy generować dane automatycznie?")

    def __str__(self):
        return f"{self.nazwa} ({self.zaklad.nazwa})"

class Pomiar(models.Model):
    TYP_WPISU = [
        ('MANUAL', 'Ręczny'),
        ('SENSOR', 'Czujnik (Symulacja)'),
    ]
    
    zrodlo = models.ForeignKey(ZrodloCiepla, on_delete=models.CASCADE)
    data_wpisu = models.DateTimeField(auto_now_add=True)
    typ_wpisu = models.CharField(max_length=10, choices=TYP_WPISU, default='MANUAL')
    
    # Parametry fizyczne
    temp_zrodla = models.FloatField()
    temp_otoczenia = models.FloatField(default=20.0)
    przeplyw_masowy = models.FloatField()
    sprawnosc_odzysku = models.FloatField(default=0.85)

    def oblicz_moc_odzysku_kw(self):
        # Uproszczone ciepła właściwe [kJ/kg*K]
        cp_map = {'woda': 4.18, 'powietrze': 1.00, 'spaliny': 1.10, 'olej': 1.80}
        cp = cp_map.get(self.zrodlo.medium, 1.0)
        
        delta_t = self.temp_zrodla - self.temp_otoczenia
        if delta_t < 0: return 0.0
        
        moc = self.przeplyw_masowy * cp * delta_t * self.sprawnosc_odzysku
        return round(moc, 2)

    def oblicz_oszczednosc_roczna(self):
        moc = self.oblicz_moc_odzysku_kw()
        mwh_rocznie = (moc * self.zrodlo.czas_pracy_h_rok) / 1000.0
        return round(mwh_rocznie * self.zrodlo.zaklad.koszt_energii_mwh, 2)

from django.contrib import admin
from .models import Zaklad, ZrodloCiepla, Pomiar

@admin.register(Pomiar)
class PomiarAdmin(admin.ModelAdmin):
    list_display = ('zrodlo', 'typ_wpisu', 'temp_zrodla', 'show_moc', 'data_wpisu')
    list_filter = ('typ_wpisu', 'zrodlo__zaklad')
    
    def show_moc(self, obj):
        return f"{obj.oblicz_moc_odzysku_kw()} kW"
    show_moc.short_description = "Moc"

admin.site.register(Zaklad)
admin.site.register(ZrodloCiepla)
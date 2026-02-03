from django.contrib import admin
from .models import EquipmentDataset, AuthToken

@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'key', 'created']

@admin.register(EquipmentDataset)
class EquipmentDatasetAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'uploaded_at', 'total_count']
    list_filter = ['uploaded_at']

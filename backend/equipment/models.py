import secrets
from django.db import models
from django.conf import settings


class AuthToken(models.Model):
    """Custom token for API auth (replaces djangorestframework-authtoken for Python 3.14)."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='equipment_authtoken')
    key = models.CharField(max_length=40, unique=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_hex(20)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} token"


class EquipmentDataset(models.Model):
    """Stores metadata for each uploaded CSV. We keep only last 5 in history."""
    name = models.CharField(max_length=255, default='Untitled')
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    total_count = models.IntegerField(default=0)
    summary_json = models.JSONField(default=dict, blank=True)  # averages, type_distribution

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.name} ({self.uploaded_at})"

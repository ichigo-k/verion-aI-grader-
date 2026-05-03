from django.db import models


class ApiKey(models.Model):
    key_hash = models.CharField(max_length=64, unique=True)   # SHA-256 hex digest
    label = models.CharField(max_length=100, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auth_keys_apikey'

    # DRF's IsAuthenticated checks request.user.is_authenticated.
    # Since ApiKey is used as the "user" object, we satisfy that contract here.
    @property
    def is_authenticated(self):
        return True

    def __str__(self) -> str:
        return f"ApiKey(label={self.label!r}, active={self.is_active})"

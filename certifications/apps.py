# certifications app
from django.apps import AppConfig


class CertificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'certifications'
    verbose_name = 'Certifications'
    
    def ready(self):
        """Import signals when app is ready."""
        # Import signals here if you create any
        # import certifications.signals
        pass
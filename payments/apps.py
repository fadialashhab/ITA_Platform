from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    verbose_name = 'Payment Management'
    
    def ready(self):
        """Import signal handlers when app is ready."""
        # Import signals here if you create any
        # import payments.signals
        pass
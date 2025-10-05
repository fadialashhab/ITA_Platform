from django.apps import AppConfig


class EnrollmentsConfig(AppConfig):
    """Configuration for the enrollments app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'enrollments'
    verbose_name = 'Enrollments'
    
    def ready(self):
        """Import signals when app is ready."""
        # Import signals here if you create any
        # import enrollments.signals
        pass
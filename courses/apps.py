from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'
    verbose_name = 'Course Management'
    
    def ready(self):
        """Import signals when app is ready."""
        # Import signals here if you create any
        # import courses.signals
        pass
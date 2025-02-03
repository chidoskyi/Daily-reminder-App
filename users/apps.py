from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        """Import and connect signals when the app is ready"""
        import users.signals  # Import signals module
        users.signals.ready()  # Connect signals

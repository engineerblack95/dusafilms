from django.apps import AppConfig


class MoviesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'movies'
    
    def ready(self):
        """
        Register signals when the app is ready
        This ensures email notifications are sent when new movies are added
        """
        import movies.signals
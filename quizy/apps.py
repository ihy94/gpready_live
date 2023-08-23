from django.apps import AppConfig


class QuizyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quizy'

    def ready(self) -> None:
        import quizy.signals.handlers

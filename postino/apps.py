from django.apps import AppConfig


class PostinoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'postino'
    verbose_name = 'Postino Blog'

    def ready(self):
        import postino.signals  # noqa

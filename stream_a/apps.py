from django.apps import AppConfig


class StreamAConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stream_a'

    def ready(self):
        import stream_a.signals

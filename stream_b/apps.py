from django.apps import AppConfig


class StreamBConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stream_b'

    def ready(self):
        import stream_a.signals


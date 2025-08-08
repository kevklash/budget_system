from django.apps import AppConfig


class AdsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ads'
    verbose_name = 'Advertisement Management'

    def ready(self) -> None:
        """Import signals when the app is ready."""
        import ads.models  # This ensures signals are imported

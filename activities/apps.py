from pathlib import Path

from django.apps import AppConfig

from utils.module_loader import import_strategies


class ActivitiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "activities"

    def ready(self):
        base_path = Path(__file__).resolve().parent / "strategies"
        import_strategies("payload", base_path.parent)

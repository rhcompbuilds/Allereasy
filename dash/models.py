from django.db import models

# Create your models here.
from django.db import models


class AppSettings(models.Model):
    """
    Singleton model to hold global feature toggles and app-wide options
    for the dashboard + guest experience.
    """

    # Ensure only one row exists
    singleton = models.BooleanField(default=True, unique=True, editable=False)

    # --- Feature flags / toggles ---
    enable_nutrition = models.BooleanField(
        default=False,
        help_text="Show and use extended nutrition fields (carbs, protein, etc.).",
    )
    enable_vegan_flags = models.BooleanField(
        default=True,
        help_text="Show vegan/vegetarian markers on dishes.",
    )
    enable_product_fields = models.BooleanField(
        default=False,
        help_text="Show supplier / barcode / external product fields on dishes.",
    )
    enable_audit_log = models.BooleanField(
        default=True,
        help_text="Require change reasons and record dish change history.",
    )

    class Meta:
        verbose_name = "App settings"
        verbose_name_plural = "App settings"

    def __str__(self) -> str:
        return "Application settings"

    @classmethod
    def get_solo(cls):
        """
        Always returns the single AppSettings instance, creating it if needed.
        """
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"singleton": True})
        return obj

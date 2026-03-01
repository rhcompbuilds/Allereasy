from django.db import models
from django.contrib.auth.models import User


class Allergen(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    icon = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Menu_Type(models.Model):
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=20, unique=True)
    logo = models.URLField(blank=True, default="https://i.ibb.co/7QpKsCX/white-background.jpg")
    background_image = models.URLField(blank=True, default="https://i.ibb.co/7QpKsCX/white-background.jpg")

    # 🎨 Branding fields
    primary_color = models.CharField(
        max_length=7,
        default="#0f172a",
        help_text="Hex colour, e.g. #0f172a"
    )
    secondary_color = models.CharField(
        max_length=7,
        default="#1e293b",
        help_text="Hex colour, e.g. #1e293b"
    )
    accent_color = models.CharField(
        max_length=7,
        default="#eab308",
        help_text="Hex colour for buttons/highlights"
    )
    text_color = models.CharField(
        max_length=7,
        default="#0f172a",
        help_text="Hex colour for main text"
    )
    background_color = models.CharField(
        max_length=7,
        default="#ffffff",
        help_text="Hex colour for page background"
    )
    font_family = models.CharField(
        max_length=200,
        default="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        help_text="CSS font-family stack"
    )

    def __str__(self):
        return self.name
    

class Category(models.Model):
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=20, unique=True)
    cat_image = models.URLField(blank=True, default="https://i.ibb.co/7QpKsCX/white-background.jpg")
    menu_type = models.ForeignKey(Menu_Type, on_delete=models.CASCADE, related_name='categories')
    
    def __str__(self):
        return self.name


class Subcategory(models.Model):
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=20, unique=True)
    subcat_image = models.URLField(blank=True, default="https://i.ibb.co/7QpKsCX/white-background.jpg")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Dish(models.Model):
    name = models.CharField(max_length=50)
    menu_type = models.ManyToManyField('Menu_Type', related_name='dishes_on_menu')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='dishes')
    subcategory = models.ForeignKey(
        'Subcategory', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='dishes_in_sub'
    ) 
    
    description = models.TextField(blank=True)
    allergens = models.ManyToManyField(Allergen, blank=True)
    image = models.URLField(blank=True, default="https://i.ibb.co/7QpKsCX/white-background.jpg")

    # Dietary flags
    is_vegan = models.BooleanField(default=False)
    is_vegetarian = models.BooleanField(default=False)

    # Supplier / product linkage (future-proof for barcode / ingredient work)
    supplier_name = models.CharField(max_length=100, blank=True)
    supplier_code = models.CharField(max_length=50, blank=True, help_text="Internal code or PLU")
    product_barcode = models.CharField(max_length=32, blank=True, help_text="EAN/UPC if available")
    external_product_url = models.URLField(blank=True, help_text="Link to supplier or spec sheet")

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archive', 'Archive'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive')
    kcal = models.PositiveIntegerField(null=True, blank=True)
    slug = models.SlugField(max_length=50, unique=False, blank=True, null=True)

    # Change tracking basics
    last_modified = models.DateTimeField(auto_now=True)
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_dishes',
    )
    last_change_reason = models.CharField(max_length=255, blank=True)
    edit_lock_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class DishNutrition(models.Model):
    """
    Optional per-dish nutrition info.
    Separate table so you can extend without bloating Dish.
    """
    dish = models.OneToOneField(
        Dish,
        on_delete=models.CASCADE,
        related_name='nutrition'
    )
    calories = models.PositiveIntegerField(null=True, blank=True)  # can mirror kcal or replace it later
    carbs = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    protein = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    fat = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    saturated_fat = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    sugar = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    fibre = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    salt = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    portion_size = models.CharField(max_length=50, blank=True)  # e.g. "per serving", "per 100g"
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dish nutrition"
        verbose_name_plural = "Dish nutrition"

    def __str__(self):
        return f"Nutrition for {self.dish.name}"


class DishChangeLog(models.Model):
    """
    Per-change audit log for dishes:
    - who changed what
    - when
    - why
    - which fields changed (stored as JSON)
    """
    dish = models.ForeignKey(
        Dish,
        on_delete=models.CASCADE,
        related_name='change_logs'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dish_change_logs'
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"Change on {self.dish.name} at {self.changed_at:%Y-%m-%d %H:%M}"

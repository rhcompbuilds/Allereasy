from django.contrib import admin
from .models import Allergen, Menu_Type, Category, Subcategory, Dish

# Simple models can use the default registration
admin.site.register(Allergen)
admin.site.register(Menu_Type)
admin.site.register(Category)
admin.site.register(Subcategory)

# Custom Admin for Dish is necessary for M2M fields
@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    # These fields are non-M2M and can be displayed
    list_display = (
        'name', 
        'kcal',
        'status',
        'category',
        'subcategory',
        # Functions to display M2M fields (defined below)
        'display_menu_types',
    )
    
    # Allows easy selection of M2M fields on the Dish form
    filter_horizontal = (
        'menu_type', 
        'allergens'
    )
    
    # Used for filtering the list view
    list_filter = (
        'status',
        ('menu_type', admin.RelatedFieldListFilter),
        'category',
        'subcategory',
        'allergens',
    )
    
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    # Methods to display the names of the M2M objects in the list view
    def display_menu_types(self, obj):
        return ", ".join([menu.name for menu in obj.menu_type.all()])
    display_menu_types.short_description = 'Menus'
    
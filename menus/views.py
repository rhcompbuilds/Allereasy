from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from .models import Menu_Type, Category, Subcategory, Dish, Allergen 

# Create your views here.
# The main public entry point - typically shows all available menu types
def index(request):
    menu_types = Menu_Type.objects.all()
    context = {
        'menu_types': menu_types,
        'page_title': 'Select Menu',
    }
    return render(request, 'menus/index.html', context)

def category_selection(request, menu_type_slug):
    menu_type = get_object_or_404(Menu_Type, slug=menu_type_slug)
    
    categories = Category.objects.filter(
        menu_type=menu_type,  
        
        dishes__status='active'
        
    ).distinct().order_by('name')
    
    # Fetch all allergens for the filter sidebar (on the next page)
    all_allergens = Allergen.objects.all().order_by('name')

    context = {
        'menu_type': menu_type,
        'categories': categories,
        'all_allergens': all_allergens,
        'page_title': f'{menu_type.name} Categories'
    }
    return render(request, 'menus/category_selection.html', context)

# View for showing the list of dishes for a specific Menu_Type.
@require_http_methods(["GET"])
def dish_list_view(request, menu_type_slug, category_slug): 
    menu_type = get_object_or_404(Menu_Type, slug=menu_type_slug)
    category = get_object_or_404(Category, slug=category_slug) 
    
    # 2. Get Subcategories for the tab navigation
    subcategories = Subcategory.objects.filter(category=category).order_by('name')
    
    # 3. Retrieve query parameters
    selected_subcat_slug = request.GET.get('subcategory')
    excluded_allergens_str = request.GET.get('excluded_allergens', '')
    
    # 4. Build the initial Dish queryset
    dish_queryset = Dish.objects.filter(
        menu_type=menu_type,
        category=category,
        status='active'
    ).distinct().order_by('name')


    # 5. Apply Subcategory Filter (If a tab is selected)
    if selected_subcat_slug:
        # Filter by the Subcategory's slug
        dish_queryset = dish_queryset.filter(subcategory__slug=selected_subcat_slug)
        
    # 6. Apply Allergen Exclusion Filter
    excluded_allergen_ids = []
    if excluded_allergens_str:
        try:
            excluded_allergen_ids = [int(i) for i in excluded_allergens_str.split(',') if i.isdigit()]
        except ValueError:
            pass
        
    if excluded_allergen_ids:
        # Exclude dishes that contain any of the selected allergens
        dish_queryset = dish_queryset.exclude(allergens__id__in=excluded_allergen_ids).distinct()

    # 7. Final Context preparation
    all_allergens = Allergen.objects.all().order_by('name')
    
    context = {
        'menu_type': menu_type,
        'category': category, 
        'subcategories': subcategories,
        'dishes': dish_queryset,
        'all_allergens': all_allergens,
        'excluded_allergen_ids': excluded_allergen_ids, 
        'selected_subcat_slug': selected_subcat_slug,
        'page_title': f'{category.name} Menu',
    }
    
    # 8. AJAX check for partial updates
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Render only the dish content area
        return render(request, 'menus/dish_content_partial.html', context) 

    # 9. Full page load
    return render(request, 'menus/dish_list.html', context)
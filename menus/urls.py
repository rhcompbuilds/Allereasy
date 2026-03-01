from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
     
    path('<slug:menu_type_slug>/categories/', views.category_selection, name='category_selection'), 
    path('menu/<slug:menu_type_slug>/<slug:category_slug>/', views.dish_list_view, name='dish_list'),
]
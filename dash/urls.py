from django.urls import path
from . import views

urlpatterns = [
    # Custom Login/Logout
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='custom_logout'),
    
    # Dashboard Home
    path('', views.dashboard_home, name='dashboard_home'),
    
    # Dish CRUD
    path('dishes/', views.DishListView.as_view(), name='dish_list'),
    path('dishes/add/', views.DishCreateView.as_view(), name='dish_create'),
    path('dishes/edit/<int:pk>/', views.DishUpdateView.as_view(), name='dish_update'),
    path('dishes/delete/<int:pk>/', views.DishDeleteView.as_view(), name='dish_delete'),
    
    # Bulk Action
    path('dishes/bulk-delete-archive/', views.bulk_archive_delete, name='bulk_archive_delete'),
    path('dishes/import/', views.import_data, name='import_data'),
    path("dash/convert-allergens/", views.convert_allergen_csv_view, name="convert_allergens"),

    # User Management (superuser only)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/', views.UserCreateView.as_view(), name='user_create'),
    path('users/edit/<int:pk>/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/delete/<int:pk>/', views.UserDeleteView.as_view(), name='user_delete'),

    # Branding (superuser only)
    path('branding/', views.BrandingListView.as_view(), name='branding_list'),
    path('branding/edit/<int:pk>/', views.BrandingUpdateView.as_view(), name='branding_update'),

    # Logs and Changes
    path("dishes/<int:pk>/confirm-changes/", views.confirm_dish_changes, name="confirm_dish_changes"),
    path("audit-log/", views.DishChangeLogListView.as_view(), name="dish_audit_log"),

]

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns=[
    path('',views.accueil, name='accueil'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-user-role/<int:user_id>/', views.manage_user_role, name='manage_user_role'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('create-role/', views.create_role, name='create_role'),
    path('no-access/', views.no_access, name='no_access'),
    path('toggle-task-status/', views.toggle_task_status, name='toggle_task_status'),
    path('task-details/<int:task_id>/', views.get_task_details, name='get_task_details'),
]
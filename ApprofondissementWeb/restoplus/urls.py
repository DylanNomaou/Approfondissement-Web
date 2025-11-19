"""Contient les liens pour les views"""
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
    # URLs pour les notifications
    path('assign-role/', views.assign_role_to_user, name='assign_role_to_user'),
    path('notifications/', views.get_user_notifications, name='get_user_notifications'),
    path('mark-notification-read/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('test-notification/', views.create_test_notification, name='create_test_notification'),
    #URLS SECTION EMPLOYÉS
    path('dashboard/',views.employees_management,name="employees_management"),
    path('employees/<int:employe_id>/', views.employee_profile, name='employee_profile'),
    path('ask_availibilities/<int:employe_id>/', views.ask_availibilities, name='send_availabilities_form'),
    path('fill_availability/',views.availability_form, name='fill_availability'),
    path('add-employee/', views.add_employee, name='add_employee'),
    path('edit-employee/<int:employe_id>/', views.edit_employee, name='edit_employee'),
    path('delete-employee/<int:employe_id>/', views.delete_employee, name='delete_employee'),
    path('create-schedule/', views.create_schedule, name='create_schedule'),
    path('view-schedule/', views.view_schedule, name='view_schedule'),
    path('publish-schedule/', views.publish_schedule, name='publish_schedule'),
    path('horaire/delete-shift/<int:shift_id>/', views.delete_shift, name='delete_shift'),

    # URLs pour la réinitialisation de mot de passe
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
    path('tickets/', views.tickets_list, name='tickets_list'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:ticket_id>/delete/', views.delete_ticket, name='delete_ticket'),
    path('tickets/all/', views.all_tickets, name='all_tickets'),
    # URLS SECTION INVENTAIRE
    path('inventory/',views.inventory_management,name='inventory_management'),
    path('stock-orders/', views.stock_order_list, name='stock_order_list'),
    path('stock-orders/create/', views.stock_order_create, name='stock_order_create'),
    path('stock-orders/<int:pk>/', views.stock_order_detail, name='stock_order_detail'),
    path('stock-orders/<int:pk>/edit/', views.stock_order_update, name='stock_order_update'),
    path('stock-orders/<int:pk>/delete/', views.stock_order_delete, name='stock_order_delete'),
    path('delete-inventory-item/<int:item_id>/', views.delete_inventory_item, name='delete_inventory_item'),
    path('ajax/suggestions/<path:query>',views.suggestions_ajax, name="suggestions_ajax")

]




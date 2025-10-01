from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .models import User, Task, Role, Notification

# Register your models here.
@admin.register(User,)
class CustomAdmin(UserAdmin):
    list_display=('username','email','first_name','last_name', 'role')
    list_filter = ('role', 'is_staff', 'is_active')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'can_manage_users', 'can_manage_inventory', 'can_view_reports', 'can_distribute_tasks', 'can_manage_orders')
    list_filter = ('can_manage_users', 'can_manage_inventory', 'can_view_reports', 'can_distribute_tasks', 'can_manage_orders')
    search_fields = ('name', 'description')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description')
        }),
        ('Permissions', {
            'fields': ('can_manage_users', 'can_manage_inventory', 'can_view_reports', 'can_manage_orders', 'can_distribute_tasks'),
            'description': 'Définissez les permissions pour ce rôle'
        }),
    )

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'category', 'due_date', 'is_completed', 'estimated_duration', 'get_assigned_users')
    list_filter = ('priority', 'category', 'is_completed', 'due_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'due_date'
    filter_horizontal = ('assigned_to',)
    readonly_fields = ('id',)
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'description', 'category', 'priority')
        }),
        ('Planning', {
            'fields': ('due_date', 'estimated_duration')
        }),
        ('Assignation', {
            'fields': ('assigned_to',)
        }),
        ('Statut', {
            'fields': ('is_completed',)
        }),
    )
    
    def get_assigned_users(self, obj):
        """Affiche les utilisateurs assignés à la tâche"""
        return ", ".join([str(user) for user in obj.assigned_to.all()])
    get_assigned_users.short_description = 'Assigné à'
    
    def get_queryset(self, request):
        """Optimise les requêtes en préchargeant les utilisateurs assignés"""
        return super().get_queryset(request).prefetch_related('assigned_to')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_notification', 'assigned_to', 'created_by', 'is_read', 'created_at')
    list_filter = ('type_notification', 'is_read', 'created_at')
    search_fields = ('titre', 'description', 'assigned_to__username', 'created_by__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'read_at')
    
    fieldsets = (
        ('Contenu de la notification', {
            'fields': ('titre', 'description', 'type_notification')
        }),
        ('Assignation', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Références', {
            'fields': ('task_reference', 'role_reference'),
            'description': 'Références optionnelles vers les objets liés'
        }),
        ('Statut', {
            'fields': ('is_read', 'created_at', 'read_at')
        }),
    )
    
    def get_queryset(self, request):
        """Optimise les requêtes"""
        return super().get_queryset(request).select_related('assigned_to', 'created_by', 'task_reference', 'role_reference')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Action pour marquer les notifications comme lues"""
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f"{updated} notification(s) marquée(s) comme lue(s).")
    mark_as_read.short_description = "Marquer comme lu"
    
    def mark_as_unread(self, request, queryset):
        """Action pour marquer les notifications comme non lues"""
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f"{updated} notification(s) marquée(s) comme non lue(s).")
    mark_as_unread.short_description = "Marquer comme non lu"


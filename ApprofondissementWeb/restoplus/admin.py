from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .models import User, Task, Role, Notification, WorkShift, PasswordResetCode,Inventory

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


@admin.register(WorkShift)  
class WorkShiftAdmin(admin.ModelAdmin):
    list_display = (
        'employee', 'date', 'heure_debut', 'heure_fin', 
        'has_break', 'pause_duree', 'duree_totale_formatted',
        'duree_effective_formatted', 'status'
    )
    list_filter = (
        'status', 'has_break', 'date', 'employee__role'
    )
    search_fields = (
        'employee__username', 'employee__first_name', 'employee__last_name', 'note'
    )
    date_hierarchy = 'date'
    readonly_fields = (
        'duree_totale_formatted', 'duree_effective_formatted', 
        'is_long_shift', 'break_required', 'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('Employé et Date', {
            'fields': ('employee', 'date')
        }),
        ('Heures de travail', {
            'fields': ('heure_debut', 'heure_fin'),
            'description': 'Définissez les heures de début et de fin du quart'
        }),
        ('Pause', {
            'fields': ('has_break', 'pause_duree', 'pause_debut', 'pause_fin'),
            'description': 'Configuration de la pause'
        }),
        ('Informations calculées', {
            'fields': ('duree_totale_formatted', 'duree_effective_formatted', 'is_long_shift', 'break_required'),
            'classes': ('collapse',)
        }),
        ('Note et Statut', {
            'fields': ('note', 'status', 'created_by')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    # Actions personnalisées
    def mark_as_published(self, request, queryset):
        updated = queryset.update(status=WorkShift.ShiftStatus.PUBLISHED)
        self.message_user(request, f"{updated} quart(s) marqué(s) comme publié(s).")
    mark_as_published.short_description = "Marquer comme publié"
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status=WorkShift.ShiftStatus.COMPLETED)
        self.message_user(request, f"{updated} quart(s) marqué(s) comme terminé(s).")
    mark_as_completed.short_description = "Marquer comme terminé"
    
    actions = ['mark_as_published', 'mark_as_completed']


@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'created_at', 'expires_at', 'is_used', 'attempts', 'is_expired_display')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('email', 'code')
    readonly_fields = ('code', 'created_at', 'expires_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    def is_expired_display(self, obj):
        """Afficher si le code est expiré avec une icône"""
        if obj.is_expired():
            return "✅ Expiré"
        else:
            return "❌ Actif"
    is_expired_display.short_description = "Statut"
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related()
    
    def has_add_permission(self, request):
        """Empêcher la création manuelle de codes (utiliser les vues)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Permettre seulement la lecture"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Permettre la suppression pour le nettoyage"""
        return request.user.is_superuser
    
    actions = ['cleanup_expired_codes']
    
    def cleanup_expired_codes(self, request, queryset):
        """Action pour nettoyer les codes expirés"""
        deleted_count, _ = PasswordResetCode.cleanup_expired()
        self.message_user(
            request, 
            f"{deleted_count[0] if deleted_count else 0} code(s) expiré(s) supprimé(s)."
        )
    cleanup_expired_codes.short_description = "Nettoyer les codes expirés"


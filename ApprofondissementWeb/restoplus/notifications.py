"""
Utilitaires pour la gestion des notifications
"""
from django.utils import timezone
from .models import Notification, User, Task, Role


def create_notification(titre, description, assigned_to, created_by=None, 
                       notification_type='system', task_reference=None, role_reference=None):
    """
    Créer une nouvelle notification
    
    Args:
        titre (str): Titre de la notification
        description (str): Description détaillée
        assigned_to (User): Utilisateur qui reçoit la notification
        created_by (User, optionnel): Utilisateur qui a créé la notification
        notification_type (str): Type de notification
        task_reference (Task, optionnel): Référence vers une tâche
        role_reference (Role, optionnel): Référence vers un rôle
    
    Returns:
        Notification: L'objet notification créé
    """
    notification = Notification.objects.create(
        titre=titre,
        description=description,
        assigned_to=assigned_to,
        created_by=created_by,
        type_notification=notification_type,
        task_reference=task_reference,
        role_reference=role_reference
    )
    return notification


def notify_task_assigned(task, assigned_users, created_by):
    """
    Créer des notifications quand une tâche est assignée
    
    Args:
        task (Task): La tâche assignée
        assigned_users (list): Liste des utilisateurs assignés
        created_by (User): Utilisateur qui a créé la tâche
    """
    notifications = []
    
    for user in assigned_users:
        # Créer une notification pour TOUS les utilisateurs assignés
        if user == created_by:
            # Message spécial pour le créateur
            titre = f"Tâche créée et assignée : {task.title}"
            description = (
                f"Vous avez créé une nouvelle tâche et elle vous a été assignée.\n\n"
                f"Titre : {task.title}\n"
                f"Priorité : {task.get_priority_display()}\n"
                f"Catégorie : {task.get_category_display()}\n"
                f"Échéance : {task.due_date}\n\n"
                f"Description : {task.description}"
            )
        else:
            # Message pour les autres utilisateurs
            titre = f"Nouvelle tâche assignée : {task.title}"
            description = (
                f"Une nouvelle tâche vous a été assignée par {created_by.get_full_name() or created_by.username}.\n\n"
                f"Titre : {task.title}\n"
                f"Priorité : {task.get_priority_display()}\n"
                f"Catégorie : {task.get_category_display()}\n"
                f"Échéance : {task.due_date}\n\n"
                f"Description : {task.description}"
            )
        
        notification = create_notification(
            titre=titre,
            description=description,
            assigned_to=user,
            created_by=created_by,
            notification_type='task_assigned',
            task_reference=task
        )
        notifications.append(notification)
    
    return notifications


def notify_role_assigned(user, role, assigned_by):
    """
    Créer une notification quand un rôle est assigné
    
    Args:
        user (User): Utilisateur qui reçoit le rôle
        role (Role): Le rôle assigné
        assigned_by (User): Utilisateur qui a assigné le rôle
    """
    titre = f"Nouveau rôle assigné : {role.name}"
    description = (
        f"Un nouveau rôle vous a été assigné par {assigned_by.get_full_name() or assigned_by.username}.\n\n"
        f"Rôle : {role.name}\n"
        f"Description : {role.description}\n\n"
        f"Nouvelles permissions :\n"
    )
    
    # Ajouter la liste des permissions
    permissions = []
    if role.can_manage_users:
        permissions.append("• Gérer les utilisateurs")
    if role.can_view_reports:
        permissions.append("• Voir les rapports")
    if role.can_manage_inventory:
        permissions.append("• Gérer l'inventaire")
    if role.can_manage_orders:
        permissions.append("• Gérer les commandes")
    if role.can_distribute_tasks:
        permissions.append("• Distribuer des tâches à tous")
    
    if permissions:
        description += "\n".join(permissions)
    else:
        description += "• Aucune permission spéciale"
    
    notification = create_notification(
        titre=titre,
        description=description,
        assigned_to=user,
        created_by=assigned_by,
        notification_type='role_assigned',
        role_reference=role
    )
    
    return notification


def notify_task_completed(task, completed_by):
    """
    Créer des notifications quand une tâche est terminée
    
    Args:
        task (Task): La tâche terminée
        completed_by (User): Utilisateur qui a terminé la tâche
    """
    notifications = []
    
    # Notifier tous les autres utilisateurs assignés à la tâche
    for user in task.assigned_to.all():
        if user != completed_by:
            titre = f"Tâche terminée : {task.title}"
            description = (
                f"La tâche '{task.title}' a été marquée comme terminée par {completed_by.get_full_name() or completed_by.username}."
            )
            
            notification = create_notification(
                titre=titre,
                description=description,
                assigned_to=user,
                created_by=completed_by,
                notification_type='task_completed',
                task_reference=task
            )
            notifications.append(notification)
    
    return notifications


def get_unread_notifications_count(user):
    """
    Obtenir le nombre de notifications non lues pour un utilisateur
    
    Args:
        user (User): L'utilisateur
    
    Returns:
        int: Nombre de notifications non lues
    """
    return Notification.objects.filter(assigned_to=user, is_read=False).count()


def get_recent_notifications(user, limit=10):
    """
    Obtenir les notifications récentes pour un utilisateur
    
    Args:
        user (User): L'utilisateur
        limit (int): Nombre maximum de notifications à retourner
    
    Returns:
        QuerySet: Les notifications récentes
    """
    return Notification.objects.filter(assigned_to=user).order_by('-created_at')[:limit]


def mark_notifications_as_read(user, notification_ids=None):
    """
    Marquer des notifications comme lues
    
    Args:
        user (User): L'utilisateur
        notification_ids (list, optionnel): IDs des notifications spécifiques, sinon toutes
    """
    notifications = Notification.objects.filter(assigned_to=user, is_read=False)
    
    if notification_ids:
        notifications = notifications.filter(id__in=notification_ids)
    
    notifications.update(is_read=True, read_at=timezone.now())

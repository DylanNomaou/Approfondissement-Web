"""
Utilitaires pour la gestion des notifications
"""
from django.utils import timezone
from django.db import models
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


def notify_schedule_published(week_start_date, published_by, shifts_count, affected_employees=None):
    """
    Créer UNE notification par employé concerné pour informer qu'un horaire a été publié

    Args:
        week_start_date (date): Date de début de la semaine (lundi)
        published_by (User): L'utilisateur qui a publié l'horaire
        shifts_count (int): Nombre d'horaires publiés
        affected_employees (list, optional): Liste des IDs des employés concernés par les shifts

    Returns:
        int: Nombre de notifications créées
    """
    from datetime import timedelta

    # Obtenir la date de fin de semaine (dimanche)
    week_end_date = week_start_date + timedelta(days=6)

    # Formatage des dates pour l'affichage
    week_start_formatted = week_start_date.strftime('%d/%m/%Y')
    week_end_formatted = week_end_date.strftime('%d/%m/%Y')

    # Titre et description de la notification
    titre = f"📅 Horaire publié - Semaine du {week_start_formatted}"
    description = (
        f"L'horaire de la semaine du {week_start_formatted} au {week_end_formatted} "
        f"a été publié par {published_by.get_full_name() or published_by.username}. "
        f"Consultez votre horaire dans la section 'Voir les horaires'."
    )

    # Récupérer seulement les employés qui ont des shifts publiés
    if affected_employees:
        employees_to_notify = User.objects.filter(
            id__in=affected_employees,
            is_active=True
        ).exclude(id=published_by.id)
    else:
        # Fallback: notifier tous les employés actifs (ancien comportement)
        employees_to_notify = User.objects.filter(is_active=True).exclude(id=published_by.id)

    # Créer UNE SEULE notification par employé concerné
    notifications_created = 0
    for employee in employees_to_notify:
        create_notification(
            titre=titre,
            description=description,
            assigned_to=employee,
            created_by=published_by,
            notification_type='schedule_published'
        )
        notifications_created += 1

    return notifications_created


def notify_inventory_added(inventory_item, added_by):
    """
    Créer une notification pour informer les administrateurs qu'un article d'inventaire a été ajouté

    Args:
        inventory_item (Inventory): L'article d'inventaire ajouté
        added_by (User): L'utilisateur qui a ajouté l'article

    Returns:
        int: Nombre de notifications créées
    """
    # Titre et description de la notification
    titre = f"📦 Nouvel article ajouté à l'inventaire"
    description = (
        f"Un nouvel article '{inventory_item.name}' a été ajouté à l'inventaire "
        f"par {added_by.get_full_name() or added_by.username}. "
        f"Quantité: {inventory_item.quantity} {inventory_item.get_unit_display()}. "
    )

    if inventory_item.category:
        description += f"Catégorie: {inventory_item.category}. "

    if inventory_item.supplier:
        description += f"Fournisseur: {inventory_item.supplier}. "

    description += "Consultez l'inventaire pour plus de détails."

    # Récupérer tous les administrateurs (staff et superusers)
    administrators = User.objects.filter(
        is_active=True
    ).filter(
        models.Q(is_staff=True) | models.Q(is_superuser=True)
    ).exclude(id=added_by.id)  # Exclure celui qui a ajouté l'article

    # Créer une notification pour chaque administrateur
    notifications_created = 0
    for admin in administrators:
        create_notification(
            titre=titre,
            description=description,
            assigned_to=admin,
            created_by=added_by,
            notification_type='inventory_added'
        )
        notifications_created += 1

    return notifications_created


def notify_ticket_created(ticket, created_by):
    """
    Créer une notification pour informer les administrateurs qu'un nouveau ticket a été créé

    Args:
        ticket: L'objet ticket créé
        created_by (User): L'utilisateur qui a créé le ticket

    Returns:
        int: Nombre de notifications créées
    """
    # Titre de la notification (tronqué si nécessaire)
    titre_ticket = ticket.title[:25] + "..." if len(ticket.title) > 25 else ticket.title
    titre = f"🎫 Nouveau ticket : {titre_ticket}"

    # Description de la notification
    description = (
        f"Un nouveau ticket a été créé par {created_by.get_full_name() or created_by.username}.\n\n"
        f"Titre : {ticket.title}\n"
        f"Catégorie : {ticket.category}\n\n"
        f"Description : {ticket.description[:200]}{'...' if len(ticket.description) > 200 else ''}"
    )

    # Récupérer tous les administrateurs (utilisateurs avec permission can_manage_users)
    administrators = User.objects.filter(
        is_active=True,
        role__can_manage_users=True
    ).exclude(id=created_by.id)  # Exclure celui qui a créé le ticket

    # Créer une notification pour chaque administrateur
    notifications_created = 0
    for admin in administrators:
        create_notification(
            titre=titre,
            description=description,
            assigned_to=admin,
            created_by=created_by,
            notification_type='ticket_created'
        )
        notifications_created += 1

    return notifications_created

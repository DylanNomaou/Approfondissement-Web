from django.contrib.auth.models import AbstractUser
from django.db import models
from django.forms import ValidationError
from django.utils import timezone
from datetime import date

class Role(models.Model):
    """Modèle pour définir les rôles"""

    name = models.CharField(max_length=100, unique=True, verbose_name="Nom du rôle")
    description = models.TextField(blank=True, verbose_name="Description")
    can_manage_users = models.BooleanField(default=False, verbose_name="Peut gérer les utilisateurs")
    can_view_reports = models.BooleanField(default=False, verbose_name="Peut voir les rapports")
    can_manage_inventory = models.BooleanField(default=False, verbose_name="Peut gérer l'inventaire")
    can_manage_orders = models.BooleanField(default=False, verbose_name="Peut gérer les commandes")
    can_distribute_tasks = models.BooleanField(default=False, verbose_name="Peut distribuer des tâches à tous")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"
        ordering = ['name']

class User(AbstractUser):
    class AvailabilityStatus(models.TextChoices):
        NOT_FILLED = "not_filled", "Non remplie"
        PENDING    = "pending",    "En attente"
        FILLED     = "filled",     "Remplie"
    availability_status = models.CharField(
        max_length=20,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.NOT_FILLED,
        verbose_name="Statut des disponibilités"
        )
    first_name = models.CharField(max_length=150, blank=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Nom de famille")
    email = models.EmailField(blank=True, verbose_name="Courriel")
    is_manager = models.BooleanField(default=False)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.username})"
        elif self.first_name:
            return f"{self.first_name} ({self.username})"
        else:
            return self.username

    def has_permission(self, permission):
        """Vérifier si l'utilisateur a une permission spécifique basée sur son rôle"""
        if self.is_superuser:
            return True
        if not self.role:
            return False
        return getattr(self.role, permission, False)

    def can_distribute_tasks_to_all(self):
        """Vérifier si l'utilisateur peut distribuer des tâches à tous les utilisateurs"""
        return self.has_permission('can_distribute_tasks')

    def can_create_task_for_user(self, target_user):
        """Vérifier si l'utilisateur peut créer une tâche pour un utilisateur spécifique"""
        # Les superusers peuvent tout faire
        if self.is_superuser:
            return True
        # Les utilisateurs avec la permission can_distribute_tasks peuvent assigner à tous
        if self.can_distribute_tasks_to_all():
            return True
        # Sinon, on peut seulement s'assigner des tâches à soi-même
        return self == target_user

class Availability(models.Model):
    employe=models.ForeignKey(User,on_delete=models.CASCADE)
    day=models.CharField(max_length=10, choices=[
        ('monday', 'Lundi'),
        ('tuesday', 'Mardi'),
        ('wednesday', 'Mercredi'),
        ('thursday', 'Jeudi'),
        ('friday', 'Vendredi'),
        ('saturday', 'Samedi'),
        ('sunday', 'Dimanche'),
        ])
    heure_debut=models.TimeField()
    heure_fin=models.TimeField()
    remplie = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.employe.username} - {self.day} ({self.heure_debut} à {self.heure_fin})"

class Task(models.Model):
    # Titre de la tâche
    title = models.CharField(max_length=255, verbose_name="Titre")
    # Choix de priorité
    PRIORITY_CHOICES = [
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('urgent', 'Urgente'),
    ]
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="Priorité"
    )

    # Catégorie de la tâche
    CATEGORY_CHOICES = [
        ('cuisine', 'Cuisine'),
        ('nettoyage', 'Nettoyage'),
        ('inventaire', 'Inventaire'),
        ('formation', 'Formation'),
    ]
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='cuisine',
        verbose_name="Catégorie"
    )

    # Description de la tâche
    description = models.TextField(blank=True, verbose_name="Description")
    # Date d'échéance
    due_date = models.DateField(null=True, blank=True, verbose_name="Date d'échéance")
    # Utilisateur assigné à la tâche
    assigned_to = models.ManyToManyField(User, blank=True, related_name='tasks', verbose_name="Assigné à")
    # Durée estimée en minutes
    estimated_duration = models.PositiveIntegerField(null=True, blank=True, verbose_name="Durée estimée (minutes)")
    # état de la tâche
    is_completed = models.BooleanField(default=False, verbose_name="Complétée")
    # Date de création
    created_at = models.DateTimeField(null=True, blank=True, default=timezone.now, verbose_name="Créé le")

    # class META
    class Meta:
        verbose_name = "Tâche"
        verbose_name_plural = "Tâches"
        ordering = ['is_completed', 'due_date', 'priority']


    def clean(self):
        # Validation personnalisée
        if self.due_date and self.due_date < date.today():
            raise ValidationError("La date d'échéance ne peut pas être dans le passé.")

    def __str__(self):
        return self.title


class Notification(models.Model):
    """Modèle pour les notifications système"""

    NOTIFICATION_TYPES = [
        ('task_assigned', 'Tâche assignée'),
        ('role_assigned', 'Rôle assigné'),
        ('task_completed', 'Tâche terminée'),
        ('reminder', 'Rappel'),
        ('system', 'Notification système'),
    ]

    titre = models.CharField(max_length=255, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    type_notification = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system',
        verbose_name="Type de notification"
    )

    # Utilisateur qui reçoit la notification
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Assigné à"
    )

    # Utilisateur qui a créé la notification (optionnel)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_created',
        verbose_name="Créé par"
    )

    # Statut de la notification
    is_read = models.BooleanField(default=False, verbose_name="Lu")

    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Lu le")

    # Référence optionnelle vers l'objet lié (tâche, rôle, etc.)
    task_reference = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Tâche liée"
    )

    role_reference = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Rôle lié"
    )

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']  # Plus récentes en premier

    def __str__(self):
        return f"{self.titre} - {self.assigned_to.username}"

    def mark_as_read(self):
        """Marquer la notification comme lue"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def get_type_display_icon(self):
        """Retourner l'icône Bootstrap selon le type"""
        icons = {
            'task_assigned': 'bi-clipboard-check',
            'role_assigned': 'bi-person-badge',
            'task_completed': 'bi-check-circle',
            'reminder': 'bi-bell',
            'system': 'bi-info-circle',
        }
        return icons.get(self.type_notification, 'bi-bell')

    def get_type_display_color(self):
        """Retourner la couleur selon le type"""
        colors = {
            'task_assigned': 'primary',
            'role_assigned': 'success',
            'task_completed': 'info',
            'reminder': 'warning',
            'system': 'secondary',
        }
        return colors.get(self.type_notification, 'secondary')


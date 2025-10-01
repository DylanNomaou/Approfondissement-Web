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
    


class Task(models.Model):
    # Titre de la tâche
    title = models.CharField(max_length=255, verbose_name="Titre") 

    # Priorité de la tâche

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


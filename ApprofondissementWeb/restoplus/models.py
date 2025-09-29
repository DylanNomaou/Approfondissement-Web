from datetime import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.forms import ValidationError



class Role(models.Model):
    """Modèle pour définir les rôles"""

    ROLE_CHOICES = [
        ('proprietaire', 'Proprietaire'),
        ('gerant', 'Gerant'),
        ('employe', 'Employe')
    ]

    name = models.CharField( max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField( blank=True)
    can_manage_users = models.BooleanField( default=False)
    can_view_reports = models.BooleanField(default=False)
    can_manage_inventory = models.BooleanField(default=False)
    can_manage_orders = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.get_name_display()



class Role(models.Model):
    """Modèle pour définir les rôles"""

    ROLE_CHOICES = [
        ('proprietaire', 'Proprietaire'),
        ('gerant', 'Gerant'),
        ('employe', 'Employe')
    ]

    name = models.CharField( max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField( blank=True)
    can_manage_users = models.BooleanField( default=False)
    can_view_reports = models.BooleanField(default=False)
    can_manage_inventory = models.BooleanField(default=False)
    can_manage_orders = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.get_name_display()

class User(AbstractUser):
    first_name = models.CharField(max_length=150, blank=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Nom de famille")
    email = models.EmailField(blank=True, verbose_name="Courriel")
    is_manager = models.BooleanField(default=False)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"
    


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


    # class META
    class Meta:
        verbose_name = "Tâche"
        verbose_name_plural = "Tâches"
        ordering = ['is_completed', 'due_date', 'priority']


    def clean(self):
        # Validation personnalisée
        if self.due_date and self.due_date < timezone.now().date():
            raise ValidationError("La date d'échéance ne peut pas être dans le passé.")
        
    def __str__(self):
        return self.title    

    def has_permission(self, permission):
        """Vérifier si l'utilisateur a une permission """
        if not self.is_superuser:
            return False
        return getattr(self.role, permission, False)


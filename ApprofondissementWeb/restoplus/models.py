from django.contrib.auth.models import AbstractUser
from django.db import models



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

    def has_permission(self, permission):
        """Vérifier si l'utilisateur a une permission """
        if not self.is_superuser:
            return False
        return getattr(self.role, permission, False)


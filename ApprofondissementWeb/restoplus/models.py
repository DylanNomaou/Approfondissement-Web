from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
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

phone_validator = RegexValidator(
    regex=r'^\+?1?\s*(?:\([2-9]\d{2}\)|[2-9]\d{2})[-.\s]?\d{3}[-.\s]?\d{4}$',
    message="Numéro invalide.Il doit être au format 444-555-1234"
)
email_validator = RegexValidator(
    regex=r'^((?!\.)[\w\-_.]*[^.])(@\w+)(\.\w+(\.\w+)?[^.\W])$',
    message="Format de l'adresse courriel invalide."
)

class User(AbstractUser):
    @property
    def mobile_display(self):
        return self.mobile if self.mobile else '—'
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
    poste = models.CharField(max_length=100, blank=True, verbose_name="Poste")
    mobile = models.CharField(max_length=20,blank=True,validators=[phone_validator], verbose_name="Téléphone")
    # Utiliser CharField avec le RegexValidator personnalisé pour n'avoir QUE
    # la validation définie par le regex (évite l'EmailValidator par défaut
    # de Django qui produit le message en anglais).
    email = models.CharField(
        max_length=254,
        blank=True,
        verbose_name="Courriel",
        validators=[email_validator]
    )
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
        if self.is_superuser:
            return True
        if self.can_distribute_tasks_to_all():
            return True
        return self == target_user

    def can_manage_employees(self):
        """Vérifier si l'utilisateur peut gérer les employés"""
        if self.is_superuser:
            return True
        return self.has_permission('can_manage_users')


# ======================================================================
# 🧑‍💼 DISPONIBILITÉS
# ======================================================================

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

# ======================================================================
# 🧑‍💼 INVENTAIRE
# ======================================================================

class Inventory(models.Model):
    """Article d'inventaire"""
    UNIT_CHOICES = [
        ("pcs", "Pièce(s)"),
        ("lb", "Livres"),
        ("g", "Grammes"),
        ("l", "Litres"),
        ("ml", "Millilitres"),
        ("pack", "Paquet"),
    ]

    name = models.CharField(max_length=200, verbose_name="Nom")
    sku = models.CharField(max_length=50, blank=True, unique=True, verbose_name="SKU")
    category = models.CharField(max_length=100, blank=True, verbose_name="Catégorie")

    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Quantité")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default="pcs", verbose_name="Unité")
    supplier = models.CharField(max_length=200, blank=True, verbose_name="Fournisseur")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prix coûtant")

    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Article d'inventaire"
        verbose_name_plural = "Inventaire"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})" if self.sku else self.name

    def clean(self):
        """Validations simples"""
        errors = {}
        if self.quantity is not None and self.quantity < 0:
            errors["quantity"] = "La quantité ne peut pas être négative."
        if errors:
            raise ValidationError(errors)


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

class Quart(models.Model):
    employe = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Employé")
    date = models.DateField(verbose_name="Date du quart")
    heure_debut = models.TimeField(verbose_name="Heure de début")
    heure_fin = models.TimeField(verbose_name="Heure de fin")
    note = models.TextField(blank=True, verbose_name="Note")

    def __str__(self):
        return f"{self.employe.username} - {self.date} ({self.heure_debut} à {self.heure_fin})"

    def clean(self):
        # Validation personnalisée pour s'assurer que l'heure de fin est après l'heure de début
        if self.heure_fin <= self.heure_debut:
            raise ValidationError("L'heure de fin doit être après l'heure de début.")

class Schedule(models.Model):
    semaine_debut = models.DateField(verbose_name="Semaine débutant le")
    Quarts = models.ManyToManyField(Quart, blank=True, related_name='schedules', verbose_name="Quarts")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    def __str__(self):
        return f"Semaine du {self.semaine_debut}"

    def clean(self):
        # Validation personnalisée pour s'assurer que la date de début est un lundi
        if self.semaine_debut.weekday() != 0:
            raise ValidationError("La date de début de la semaine doit être un lundi.")



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


class WorkShift(models.Model):
    """
    Modèle pour représenter un quart de travail d'un employé
    """
    class ShiftStatus(models.TextChoices):
        DRAFT = 'draft', 'Brouillon'
        PUBLISHED = 'published', 'Publié'
        COMPLETED = 'completed', 'Terminé'
        CANCELLED = 'cancelled', 'Annulé'

    # Relations
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='work_shifts',
        verbose_name="Employé"
    )

    # Informations de base
    date = models.DateField(verbose_name="Date du quart")
    heure_debut = models.TimeField(verbose_name="Heure de début")
    heure_fin = models.TimeField(verbose_name="Heure de fin")

    # Gestion des pauses
    has_break = models.BooleanField(
        default=True,
        verbose_name="A une pause"
    )
    pause_duree = models.PositiveIntegerField(
        default=30,
        verbose_name="Durée de pause (minutes)",
        help_text="Durée de la pause en minutes (0-120)"
    )
    pause_debut = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Début de pause"
    )
    pause_fin = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Fin de pause"
    )

    # Informations complémentaires
    note = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="Note",
        help_text="Informations supplémentaires sur ce quart"
    )

    # Statut et gestion
    status = models.CharField(
        max_length=20,
        choices=ShiftStatus.choices,
        default=ShiftStatus.DRAFT,
        verbose_name="Statut"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_shifts',
        verbose_name="Créé par"
    )

    class Meta:
        verbose_name = "Quart de travail"
        verbose_name_plural = "Quarts de travail"
        ordering = ['date', 'heure_debut']
        unique_together = ['employee', 'date']  # Un seul quart par employé par jour
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f"{self.employee} - {self.date} ({self.heure_debut}-{self.heure_fin})"

    def clean(self):
        """Validation personnalisée du modèle"""
        from django.core.exceptions import ValidationError
        from datetime import datetime, timedelta

        errors = {}

        # Vérifier que l'heure de fin est après l'heure de début
        if self.heure_debut and self.heure_fin:
            if self.heure_fin <= self.heure_debut:
                # Gérer le cas où le quart se termine le lendemain
                debut = datetime.combine(self.date, self.heure_debut)
                fin = datetime.combine(self.date, self.heure_fin)
                if fin <= debut:
                    fin += timedelta(days=1)

                duree_totale = (fin - debut).total_seconds() / 3600
                if duree_totale > 12:
                    errors['heure_fin'] = "Un quart ne peut pas dépasser 12 heures."

        # Validation des pauses
        if self.has_break:
            if self.pause_duree is None or self.pause_duree < 0:
                errors['pause_duree'] = "La durée de pause doit être positive."
            elif self.pause_duree > 120:
                errors['pause_duree'] = "La durée de pause ne peut pas dépasser 120 minutes."

            # Vérifier les heures de pause si elles sont définies
            if self.pause_debut and self.pause_fin:
                if self.pause_fin <= self.pause_debut:
                    errors['pause_fin'] = "L'heure de fin de pause doit être après l'heure de début."

                # Vérifier que la pause est dans les heures de travail
                if self.heure_debut and self.heure_fin:
                    if (self.pause_debut < self.heure_debut or
                        self.pause_fin > self.heure_fin):
                        errors['pause_debut'] = "La pause doit être dans les heures de travail."
        else:
            # Si pas de pause, réinitialiser les champs de pause
            self.pause_duree = 0
            self.pause_debut = None
            self.pause_fin = None

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Sauvegarde avec validation"""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def duree_totale_minutes(self):
        """Durée totale du quart en minutes"""
        if not self.heure_debut or not self.heure_fin:
            return 0

        from datetime import datetime, timedelta
        debut = datetime.combine(self.date, self.heure_debut)
        fin = datetime.combine(self.date, self.heure_fin)

        # Gérer le cas où le quart se termine le lendemain
        if fin <= debut:
            fin += timedelta(days=1)

        return int((fin - debut).total_seconds() / 60)

    @property
    def duree_effective_minutes(self):
        """Durée effective de travail (sans pause) en minutes"""
        duree_totale = self.duree_totale_minutes
        pause = self.pause_duree if self.has_break else 0
        return max(0, duree_totale - pause)

    @property
    def duree_totale_formatted(self):
        """Durée totale formatée en heures:minutes"""
        minutes = self.duree_totale_minutes
        heures = minutes // 60
        mins = minutes % 60
        return f"{heures}h{mins:02d}"

    @property
    def duree_effective_formatted(self):
        """Durée effective formatée en heures:minutes"""
        minutes = self.duree_effective_minutes
        heures = minutes // 60
        mins = minutes % 60
        return f"{heures}h{mins:02d}"

    @property
    def is_long_shift(self):
        """Détermine si c'est un quart long (plus de 8h)"""
        return self.duree_totale_minutes > 480  # 8 heures

    @property
    def break_required(self):
        """Détermine si une pause est légalement requise"""
        # En général, pause requise pour les quarts de plus de 6h
        return self.duree_totale_minutes > 360  # 6 heures

    def get_status_display_class(self):
        """Retourne la classe CSS pour l'affichage du statut"""
        status_classes = {
            'draft': 'badge-secondary',
            'published': 'badge-primary',
            'completed': 'badge-success',
            'cancelled': 'badge-danger',
        }
        return status_classes.get(self.status, 'badge-secondary')

    def can_edit(self, user):
        """Détermine si l'utilisateur peut éditer ce quart"""
        # L'employé peut éditer son propre quart si c'est un brouillon
        if self.employee == user and self.status == self.ShiftStatus.DRAFT:
            return True

        # Les managers peuvent toujours éditer
        if user.is_manager or user.is_superuser:
            return True

        # Les utilisateurs avec permission de distribuer des tâches
        if hasattr(user, 'role') and user.role and user.role.can_distribute_tasks:
            return True

        return False

    def can_delete(self, user):
        """Détermine si l'utilisateur peut supprimer ce quart"""
        # Seuls les managers et créateurs peuvent supprimer
        if user.is_manager or user.is_superuser:
            return True

        if self.created_by == user and self.status == self.ShiftStatus.DRAFT:
            return True

        return False

    @classmethod
    def get_shifts_for_week(cls, start_date, employee=None):
        """Récupère les quarts pour une semaine donnée"""
        from datetime import timedelta

        end_date = start_date + timedelta(days=6)
        queryset = cls.objects.filter(
            date__range=[start_date, end_date]
        ).select_related('employee', 'employee__role')

        if employee:
            queryset = queryset.filter(employee=employee)

        return queryset.order_by('date', 'heure_debut')

    @classmethod
    def get_employee_shifts_for_date(cls, employee, date):
        """Récupère les quarts d'un employé pour une date donnée"""
        return cls.objects.filter(
            employee=employee,
            date=date
        ).first()  # Un seul quart par employé par jour


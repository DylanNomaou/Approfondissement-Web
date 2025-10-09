from django import forms
from .models import User, Task
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import date

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        error_messages={"required": "Mot de passe obligatoire."}
    )
    password_confirmation = forms.CharField(
        label="Confirmation mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirmation"}),
        error_messages={"required": "Confirmation obligatoire."}
    )
    class Meta:
        model = User
        fields = ['username', 'password']
        labels = {
            'username': "Nom d'utilisateur",
        }
        help_texts = {
            'username': 'Choisissez un identifiant.',
        }
        error_messages = {
            'username': {
                'required': "Nom d’utilisateur obligatoire.",
                'unique': "Ce nom d’utilisateur est déjà pris.",
            }
        }
        widgets = {
            "username": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Identifiant"
            }),
        }
    def clean_password_confirmation(self):
        p1 = self.cleaned_data.get("password")
        p2 = self.cleaned_data.get("password_confirmation")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        return p2
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Identifiant"}),
        error_messages={"required": "Identifiant obligatoire."}
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Mot de passe"}),
        error_messages={"required": "Mot de passe obligatoire."}
    )
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Identifiants invalides.")
            self.user = user
        return cleaned_data

    def get_user(self):
        return getattr(self, "user", None)

class AvailabilityForm(forms.Form):
    DAYS = [
        ('monday', 'Lundi'),
        ('tuesday', 'Mardi'),
        ('wednesday', 'Mercredi'),
        ('thursday', 'Jeudi'),
        ('friday', 'Vendredi'),
        ('saturday', 'Samedi'),
        ('sunday', 'Dimanche'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, label in self.DAYS:
            self.fields[f"{key}_start"] = forms.TimeField(
                required=False,
                label=f"{label} - Début",
                widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
            )
            self.fields[f"{key}_end"] = forms.TimeField(
                required=False,
                label=f"{label} - Fin",
                widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
            )

    def clean(self):
        """Validation logique des heures de début/fin"""
        cleaned_data = super().clean()
        errors = {}
        for key, label in self.DAYS:
            start = cleaned_data.get(f"{key}_start")
            end = cleaned_data.get(f"{key}_end")
            if (start and not end) or (end and not start):
                errors[key] = f"{label} : veuillez remplir à la fois l'heure de début et l'heure de fin."
            # Si les deux sont présentes mais incohérentes
            elif start and end and start >= end:
                errors[key] = f"{label} : l'heure de fin doit être après l'heure de début."
        if errors:
            raise ValidationError(errors)
        return cleaned_data

class TaskForm(forms.ModelForm):
    DURATION_CHOICES = [
        ('', 'Estimer la durée'),
        (15, '15 minutes'),
        (30, '30 minutes'),
        (60, '1 heure'),
        (120, '2 heures'),
        (240, '4 heures'),
        (480, '8 heures (journée complète)'),
    ]

    estimated_duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'id': 'taskDuration'
        })
    )

    def clean_estimated_duration(self):
        """Convertir la durée estimée en entier ou None"""
        duration = self.cleaned_data.get('estimated_duration')
        if duration == '' or duration is None:
            return None
        try:
            return int(duration)
        except (ValueError, TypeError):
            return None



    assigned_to = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select form-select-lg',
            'id': 'taskAssignee',
            'size': '5'
        }),
        label="Assigné à"
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Configurer le queryset selon les permissions de l'utilisateur
        if user:
            if user.can_distribute_tasks_to_all():
                # L'utilisateur peut assigner des tâches à tout le monde
                self.fields['assigned_to'].queryset = User.objects.all().order_by('username')
                # Ne pas pré-sélectionner automatiquement - laisser le choix libre
                self.fields['assigned_to'].initial = []
            else:
                # L'utilisateur ne peut assigner des tâches qu'à lui-même
                self.fields['assigned_to'].queryset = User.objects.filter(id=user.id)
                # Pré-sélectionner l'utilisateur actuel car il ne peut pas choisir d'autres
                self.fields['assigned_to'].initial = [user.id]
        else:
            # Par défaut, si aucun utilisateur n'est fourni
            self.fields['assigned_to'].queryset = User.objects.all().order_by('username')

        # Marquer tous les champs comme obligatoires sauf estimated_duration
        required_fields = ['title', 'priority', 'category', 'description', 'due_date', 'assigned_to']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
                # Ajouter une classe CSS pour les champs obligatoires
                current_classes = self.fields[field_name].widget.attrs.get('class', '')
                self.fields[field_name].widget.attrs['class'] = current_classes + ' required-field'

        # Marquer estimated_duration comme optionnel
        self.fields['estimated_duration'].required = False

    class Meta:
        model = Task
        fields = ['title', 'priority', 'category', 'description', 'due_date', 'assigned_to', 'estimated_duration']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ex: Vérifier les stocks frigo...',
                'id': 'taskTitle',
                'maxlength': '100'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'id': 'taskPriority'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'id': 'taskCategory'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez la tâche en détail, les étapes à suivre, les ressources nécessaires...',
                'id': 'taskDescription',
                'maxlength': '500'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
                'id': 'taskDueDate'
            }),
        }
        labels = {
            'title': "Titre de la tâche",
            'priority': "Priorité",
            'category': "Catégorie",
            'description': "Description détaillée",
            'due_date': "Date d'échéance",
            'assigned_to': "Assigné à",
            'estimated_duration': "Durée estimée",
        }
        help_texts = {
            'assigned_to': "Sélectionnez un ou plusieurs utilisateurs.",
        }
        error_messages = {
            'title': {
                'required': "Le titre de la tâche est obligatoire.",
                'max_length': "Le titre ne peut pas dépasser 100 caractères.",
            },
            'priority': {
                'required': "Veuillez sélectionner une priorité.",
                'invalid_choice': "Priorité invalide."
            },
            'category': {
                'required': "Veuillez sélectionner une catégorie.",
                'invalid_choice': "Catégorie invalide."
            },
            'description': {
                'required': "La description est obligatoire.",
                'max_length': "La description ne peut pas dépasser 500 caractères."
            },
            'due_date': {
                'required': "La date d'échéance est obligatoire.",
                'invalid': "Veuillez entrer une date valide."
            },
            'assigned_to': {
                'required': "Veuillez assigner la tâche à au moins un utilisateur.",
                'invalid_choice': "Utilisateur sélectionné invalide."
            }
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or title.strip() == '':
            raise ValidationError("Le titre de la tâche est obligatoire.")
        if title.isdigit():
            raise ValidationError("Le titre ne peut pas être composé uniquement de chiffres.")
        return title.strip()

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description or description.strip() == '':
            raise ValidationError("La description est obligatoire.")
        return description.strip()

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if not due_date:
            raise ValidationError("La date d'échéance est obligatoire.")
        if due_date < date.today():
            raise ValidationError("La date d'échéance ne peut pas être dans le passé.")
        return due_date

    def clean_assigned_to(self):
        assigned_to = self.cleaned_data.get('assigned_to')
        if not assigned_to or assigned_to.count() == 0:
            raise ValidationError("La tâche doit être assignée à au moins un utilisateur.")
        return assigned_to

    def clean_priority(self):
        priority = self.cleaned_data.get('priority')
        if not priority:
            raise ValidationError("Veuillez sélectionner une priorité.")
        return priority

    def clean_category(self):
        category = self.cleaned_data.get('category')
        if not category:
            raise ValidationError("Veuillez sélectionner une catégorie.")
        return category

    def save(self, commit=True):
        task = super().save(commit=False)
        if commit:
            task.save()
        return task

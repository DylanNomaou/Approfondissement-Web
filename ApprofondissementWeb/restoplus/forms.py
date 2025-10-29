from django import forms
from .models import User, Task, WorkShift
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import date, datetime, timedelta

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
        time_widget = forms.TimeInput(
        format='%H:%M',
        attrs={
            'type': 'time',
            'class': 'form-control',
            'step': '60',
        }
    )
        for key, label in self.DAYS:
            self.fields[f"{key}_start"] = forms.TimeField(
                required=False,
                label=f"{label} - Début",
                widget=time_widget,
                input_formats=['%H:%M'],

            )
            self.fields[f"{key}_end"] = forms.TimeField(
                required=False,
                label=f"{label} - Fin",
                widget=time_widget,
                input_formats=['%H:%M'],
            )

    def clean(self):
        """Validation logique des heures de début/fin"""
        cleaned_data = super().clean()
        for key, label in self.DAYS:
            start = cleaned_data.get(f"{key}_start")
            end = cleaned_data.get(f"{key}_end")
            # Cas 1 : un seul champ rempli
            if (end and not start):
                msg = f"veuillez remplir l'heure de début."
                self.add_error(f"{key}_start", msg)
            if(start and not end):
                msg = f"veuillez remplir l'heure de fin."
                self.add_error(f"{key}_end", msg)
            # Cas 2 : incohérence logique (début >= fin)
            elif start and end and start >= end:
                msg = f"l'heure de fin doit être après l'heure de début."
                self.add_error(f"{key}_end", msg)
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


class WorkShiftForm(forms.ModelForm):
    """
    Formulaire pour créer/éditer un quart de travail basé sur le modèle WorkShift
    """
    
    class Meta:
        model = WorkShift
        fields = [
            'heure_debut', 'heure_fin', 'has_break', 'pause_duree', 
            'pause_debut', 'pause_fin', 'note'
        ]
        
        widgets = {
            'heure_debut': forms.TimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'time',
                    'step': '900'  # Pas de 15 minutes
                }
            ),
            'heure_fin': forms.TimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'time',
                    'step': '900'  # Pas de 15 minutes
                }
            ),
            'has_break': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input'
                }
            ),
            'pause_duree': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'max': '120',
                    'step': '15',
                    'placeholder': '30'
                }
            ),
            'pause_debut': forms.TimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'time',
                    'step': '900'
                }
            ),
            'pause_fin': forms.TimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'time',
                    'step': '900'
                }
            ),
            'note': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': '3',
                    'placeholder': 'Informations supplémentaires sur ce quart...',
                    'maxlength': '500'
                }
            ),
        }
        
        labels = {
            'heure_debut': 'Heure de début',
            'heure_fin': 'Heure de fin',
            'has_break': 'Prendre une pause',
            'pause_duree': 'Durée de pause (minutes)',
            'pause_debut': 'Début de pause',
            'pause_fin': 'Fin de pause',
            'note': 'Note (optionnelle)',
        }
        
        error_messages = {
            'heure_debut': {
                'required': 'L\'heure de début est obligatoire.',
                'invalid': 'Format d\'heure invalide.'
            },
            'heure_fin': {
                'required': 'l\'heure de fin est obligatoire.',
                'invalid': 'Format d\'heure invalide.'
            },
            'pause_duree': {
                'invalid': 'La durée de pause doit être un nombre entier.'
            }
        }

    def __init__(self, *args, **kwargs):
        # Récupérer les données du contexte
        self.employee = kwargs.pop('employee', None)
        self.shift_date = kwargs.pop('date', None)
        super().__init__(*args, **kwargs)
        
        # Configuration conditionnelle des champs de pause
        if not self.instance.pk or not self.instance.has_break:
            self.fields['pause_debut'].required = False
            self.fields['pause_fin'].required = False
            self.fields['pause_duree'].initial = 30

    def clean(self):
        cleaned_data = super().clean()
        heure_debut = cleaned_data.get('heure_debut')
        heure_fin = cleaned_data.get('heure_fin')
        has_break = cleaned_data.get('has_break', True)
        pause_duree = cleaned_data.get('pause_duree', 0)
        pause_debut = cleaned_data.get('pause_debut')
        pause_fin = cleaned_data.get('pause_fin')
        
        # Validation des heures de base
        if heure_debut and heure_fin:
            # Calculer la durée totale du quart
            debut = datetime.combine(date.today(), heure_debut)
            fin = datetime.combine(date.today(), heure_fin)
            
            # Gérer le cas où le quart se termine le lendemain
            if fin <= debut:
                fin += timedelta(days=1)
            
            duree_totale = (fin - debut).total_seconds() / 3600  # en heures
            
            # Vérifications de durée
            if duree_totale > 12:
                raise ValidationError(
                    "Un quart ne peut pas dépasser 12 heures."
                )
            
            # Validation spécifique des pauses
            if has_break:
                if pause_duree is None:
                    cleaned_data['pause_duree'] = 30
                    pause_duree = 30
                elif pause_duree < 0:
                    raise ValidationError({
                        'pause_duree': 'La durée de pause ne peut pas être négative.'
                    })
                elif pause_duree > 120:
                    raise ValidationError({
                        'pause_duree': 'La durée de pause ne peut pas dépasser 120 minutes.'
                    })
                
                # Calculer la durée effective
                duree_effective = duree_totale - (pause_duree / 60)
                
                if duree_effective < 1:
                    raise ValidationError(
                        "La durée effective de travail doit être d'au moins 1 heure."
                    )
                
                # Validation des heures de pause spécifiques
                if pause_debut and pause_fin:
                    if pause_fin <= pause_debut:
                        raise ValidationError({
                            'pause_fin': 'L\'heure de fin de pause doit être après l\'heure de début.'
                        })
                    
                    # Vérifier que la pause est dans les heures de travail
                    if (pause_debut < heure_debut or pause_fin > heure_fin):
                        raise ValidationError({
                            'pause_debut': 'La pause doit être comprise dans les heures de travail.'
                        })
                    
                    # Calculer la durée réelle de la pause
                    pause_debut_dt = datetime.combine(date.today(), pause_debut)
                    pause_fin_dt = datetime.combine(date.today(), pause_fin)
                    duree_pause_reelle = (pause_fin_dt - pause_debut_dt).total_seconds() / 60
                    
                    # Vérifier la cohérence avec pause_duree
                    if abs(duree_pause_reelle - pause_duree) > 5:  # Tolérance de 5 minutes
                        raise ValidationError({
                            'pause_duree': f'La durée de pause ({pause_duree} min) ne correspond pas aux heures définies ({duree_pause_reelle:.0f} min).'
                        })
            else:
                # Si pas de pause, nettoyer les champs de pause
                cleaned_data['pause_duree'] = 0
                cleaned_data['pause_debut'] = None
                cleaned_data['pause_fin'] = None
                
                # Vérifier la durée minimale sans pause
                if duree_totale < 1:
                    raise ValidationError(
                        "La durée totale de travail doit être d'au moins 1 heure."
                    )
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Assigner l'employé et la date si fournis
        if self.employee:
            instance.employee = self.employee
        if self.shift_date:
            instance.date = self.shift_date
            
        if commit:
            instance.save()
        return instance

    def get_duration_info(self):
        """
        Retourne les informations de durée calculées
        """
        if self.is_valid():
            heure_debut = self.cleaned_data['heure_debut']
            heure_fin = self.cleaned_data['heure_fin']
            has_break = self.cleaned_data.get('has_break', True)
            pause_duree = self.cleaned_data.get('pause_duree', 0) if has_break else 0
            
            debut = datetime.combine(date.today(), heure_debut)
            fin = datetime.combine(date.today(), heure_fin)
            
            if fin <= debut:
                fin += timedelta(days=1)
            
            duree_totale = (fin - debut).total_seconds() / 3600
            duree_effective = duree_totale - (pause_duree / 60) if has_break else duree_totale
            
            return {
                'duree_totale': round(duree_totale, 2),
                'duree_effective': round(duree_effective, 2),
                'pause_duree': pause_duree if has_break else 0,
                'has_break': has_break
            }
        return None

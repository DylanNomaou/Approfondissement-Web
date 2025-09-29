from datetime import timezone
from django import forms
from .models import User, Task
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate

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



class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'priority', 'category', 'description', 'due_date', 'assigned_to']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de la tâche'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigned_to': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }
        labels = {
            'title': "Titre",
            'priority': "Priorité",
            'category': "Catégorie",
            'description': "Description",
            'due_date': "Date d'échéance",
            'assigned_to': "Assigné à",
        }
        help_texts = {
            'assigned_to': "Sélectionnez un ou plusieurs utilisateurs.",
        }
        error_messages = {
            'title': {
                'required': "Le titre est obligatoire.",
                'max_length': "Le titre ne peut pas dépasser 255 caractères.",
            },
            'due_date': {
                'invalid': "Entrez une date valide.",
            },
        }


        def clean(self):
            cleaned_data = super().clean()
            title = cleaned_data.get("title")
            due_date = cleaned_data.get("due_date")
            assigned_to = cleaned_data.get("assigned_to")
            category = cleaned_data.get("category")
            
            # Vérification du titre
            if not title:
                raise ValidationError("Le titre est obligatoire.")
            if title.isdigit():
                raise ValidationError("Le titre ne peut pas être composé uniquement de chiffres.")
            
            # Vérification de la date d'échéance
            if not due_date:
                raise ValidationError("La date d'échéance est obligatoire.")
            if due_date and due_date < timezone.now().date():
                raise ValidationError("La date d'échéance ne peut pas être dans le passé.")
            
            # Vérification de l'assignation
            if not assigned_to:
                raise ValidationError("La tâche doit être assignée à au moins un employé.")
            
            # Vérification de la catégorie
            if not category:
                raise ValidationError("La catégorie est obligatoire.")
            
            return cleaned_data

        def save(self, commit=True):
            task = super().save(commit=False)
            if commit:
                task.save()
            return task

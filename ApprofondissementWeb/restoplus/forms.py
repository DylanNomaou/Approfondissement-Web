from django import forms
from .models import User
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
    
from django import forms
from django.contrib.auth import authenticate

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


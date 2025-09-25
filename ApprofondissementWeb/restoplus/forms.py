from django import forms
from .models import User
from django.core.exceptions import ValidationError

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(label = "mot de passe", widget = forms.PasswordInput(attrs={"class":"form-control"}),error_messages={"required":"Mot de passe obbligatoire"})
    password_confirmation = forms.CharField( label="confirmation mot de passe", widget=forms.PasswordInput
    (attrs={ "class":"form-control", "placeholder":"Confirmation"}),
    error_messages={"required": "Confirmation obligatoire."})

    class Meta:
        model = User
        fields= ['username','password']
        labels={'username':'nom d\'utilisateur'}
        help_texts ={
            'username':'choisissez un identifiant ',
        }
        error_messages={
            'username':{
                'unique':"Ce nom d'utilisateur est déjà pris.",
            }
        }
        widgets = {
            "username": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Identifiant"
            }),
        }
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("password_confirmation")
        if p1 and p2 and p1 != p2:
            self.add_error("password_confirmation", "Les mots de passe ne correspondent pas.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
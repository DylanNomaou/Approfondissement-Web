from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import login

from django.shortcuts import render
from django.contrib.auth import login
from .forms import UserRegisterForm, UserLoginForm
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.
def accueil(request):
    """Vue pour la page d'accueil."""
    if not request.user.is_authenticated:
        messages.info(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('login')
    return render(request,"restoplus/accueil.html")

def signup_view(request):
    """Affiche le formulaire pour l'inscription"""
    if request.method=='POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Inscription réussie !")
            return redirect('accueil')
    else:
        form=UserRegisterForm()
    return render(request, 'registration/signup.html',{'form':form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("accueil")
    else:
        form = UserLoginForm()
    return render(request, 'registration/login.html', {'form': form})



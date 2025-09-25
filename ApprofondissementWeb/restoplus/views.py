from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import login
from django.shortcuts import render
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required

# Create your views here.
def accueil(request):
    """Vue pour la page d'accueil."""
    return render(request,"restoplus/accueil.html")

def signup_view(request):
    """Affiche le formulaire pour l'inscription"""
    if request.method=='POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user=form.save()
            messages.success(request, "Inscription réussie !")
            return redirect('login')
    else:
        form=UserRegisterForm()
    return render(request, 'registration/signup.html',{'form':form})

def login_view(request):
    """Affiche le formulaire pour la connexion"""
    if request.method=='POST':
        form = AuthenticationForm(request,data=request.POST)
        if form.is_valid():
            user=form.get_user()
            login(request,user)
            return redirect("accueil")
    else:
        form=AuthenticationForm()
    return render(request, 'registration/login.html',{'form':form})

@login_required
def admin_dashboard(request):
    """Vue pour le tableau de bord administrateur."""

    context = {
    'title': 'Tableau de bord administrateur',
    }
    return render(request, "resto/admin_dashboard.html", context)

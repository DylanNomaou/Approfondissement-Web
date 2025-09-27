from django.shortcuts import render,redirect,get_object_or_404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
def accueil(request):
    """Vue pour la page d'accueil."""
    return render(request,"accueil.html")
#commentaire pour tester git


@login_required
def admin_dashboard(request):
    """Vue pour le tableau de bord administrateur."""

    context = {
    'title': 'Tableau de bord administrateur',
    }
    return render(request, "resto/admin_dashboard.html", context)

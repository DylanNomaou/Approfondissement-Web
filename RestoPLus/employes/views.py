from django.shortcuts import render

# Create your views here.

def index(request):
    """Vue index pour l'application employes."""
    return render(request, 'employes/index.html')

from django.shortcuts import render

# Create your views here.

def index(request):
    """Vue index pour l'application inventaires."""
    return render(request, 'inventaires/index.html')

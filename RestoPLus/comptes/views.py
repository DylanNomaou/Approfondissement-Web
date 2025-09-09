from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def index(request):
    """Vue index pour l'application comptes."""
    return render(request, 'comptes/index.html')

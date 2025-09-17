from django.shortcuts import render,redirect,get_object_or_404
from django.shortcuts import render

# Create your views here.
def accueil(request):
    return render(request,"comptes/index.html")
#commentaire pour tester git
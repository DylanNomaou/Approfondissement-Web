from django.urls import path
from . import views

app_name = 'employes'

urlpatterns = [
    # Exemple de route pour l'application employes
    path('', views.index, name='index'),
]

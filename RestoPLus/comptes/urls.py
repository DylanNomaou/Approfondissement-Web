from django.urls import path
from . import views

app_name = 'comptes'

urlpatterns = [
    # Exemple de route pour l'application comptes
    path('', views.index, name='index'),
]

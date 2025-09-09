from django.urls import path
from . import views

app_name = 'inventaires'

urlpatterns = [
    # Exemple de route pour l'application inventaires
    path('', views.index, name='index'),
]

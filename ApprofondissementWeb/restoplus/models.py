from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    first_name = models.CharField(max_length=150, blank=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Nom de famille")
    email = models.EmailField(blank=True, verbose_name="Courriel")
    is_manager = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name})"
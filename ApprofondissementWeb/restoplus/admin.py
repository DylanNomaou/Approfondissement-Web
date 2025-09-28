from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
@admin.register(User,)
class CustomAdmin(UserAdmin):
    list_display=('username','email','first_name','last_name',)
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserLoginForm
from django.contrib.auth import get_user_model

from .models import User, Role
# Create your views here.
def accueil(request):
    """Vue pour la page d'accueil."""
    if not request.user.is_authenticated:
        messages.info(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('login')
    return render(request,"restoplus/accueil.html")

def signup_view(request):
    """Affiche le formulaire pour l'inscription"""
    if request.method=='POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Inscription réussie !")
            return redirect('accueil')
    else:
        form=UserRegisterForm()
    return render(request, 'registration/signup.html',{'form':form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("accueil")
    else:
        form = UserLoginForm()
    return render(request, 'registration/login.html', {'form': form})

def admin_dashboard(request):
    """Vue pour le tableau de bord administrateur."""

    if not request.user.has_permission('can_manage_users'):
        messages.error(request, "Vous n'avez pas les permissions d'accéder à cette page")
        return redirect('no_access')

    users = User.objects.all().select_related('role')
    roles = Role.objects.all()

    context = {
    'title': 'Tableau de bord administrateur',
    'users' : users,
    'roles' : roles,
    }
    return render(request, "restoplus/admin_dashboard.html", context)

@login_required
def manage_user_role(request, user_id):
    """Modifier le rôle d'un utilisateur"""
    if not request.user.has_permission('can_manage_users'):
        messages.error(request, "Permission refusée")
        return redirect('no_access')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        role_id = request.POST.get('role_id')
        if role_id:
            role = get_object_or_404(Role, id=role_id)
            user.role = role
            user.save()
            messages.success(request,
                        f"Le rôle de  {user.username} mis à jour vers {role.get_name_display()}")
        else:
            user.role = None
            user.save()
            messages.success(request, f"Rôle retiré pour {user.username}")
    return redirect('admin_dashboard')


@login_required
def create_role(request):
    """Créer une nouveau rôle"""
    if not request.user.has_permission('can_manage_users'):
        messages.error(request,"Permission refusée")
        return redirect('no_access')

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        can_manage_users = request.POST.get('can_manage_users') == 'on'
        can_manage_orders = request.POST.get('can_manage_orders') == 'on'
        can_manage_inventory = request.POST.get('can_manage_inventory') == 'on'
        can_view_reports = request.POST.get('can_view_reports') == 'on'

        if Role.objects.filter(name=name).exists():
            messages.error(request, "Ce rôle existe déja")
        else:
            Role.objects.create(
                name = name,
                description = description,
                can_manage_inventory = can_manage_inventory,
                can_manage_users = can_manage_users,
                can_manage_orders = can_manage_orders,
                can_view_reports=can_view_reports
            )
            messages.success(request, "Nouveau rôle créé avec succès!")
    return redirect('admin_dashboard')


@login_required
def no_access(request):
    """page d'accès refusé"""
    return render(request, 'restoplus/no_acces.html')

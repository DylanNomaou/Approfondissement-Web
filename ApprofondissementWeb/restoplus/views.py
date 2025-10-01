from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserLoginForm, TaskForm
from django.contrib.auth import get_user_model
from datetime import date
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import User, Role, Task
# Create your views here.
def accueil(request):
    """Vue pour la page d'accueil."""
    if not request.user.is_authenticated:
        messages.info(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('login')
    
    # Gestion du formulaire de tâche
    if request.method == 'POST':
        task_form = TaskForm(request.POST, user=request.user)
        if task_form.is_valid():
            task = task_form.save()
            # Message de succès détaillé
            assigned_users = ", ".join([str(user) for user in task.assigned_to.all()])
            if assigned_users:
                messages.success(request, f"✅ Tâche '{task.title}' créée avec succès ! Assignée à : {assigned_users}")
            else:
                messages.success(request, f"✅ Tâche '{task.title}' créée avec succès !")
            return redirect('accueil')
        else:
            # Ajouter les classes CSS d'erreur directement aux champs
            for field_name, field_errors in task_form.errors.items():
                if field_name in task_form.fields:
                    widget_attrs = task_form[field_name].field.widget.attrs
                    current_class = widget_attrs.get('class', '')
                    if 'is-invalid' not in current_class:
                        widget_attrs['class'] = current_class + ' is-invalid'
        # Pas de redirection en cas d'erreur - on reste sur la page avec le formulaire invalide
    else:
        task_form = TaskForm(user=request.user)
    
    # Récupérer les tâches assignées à l'utilisateur connecté
    today = date.today()
    
    # Pour déboguer : récupérer TOUTES les tâches assignées à l'utilisateur (terminées et non terminées)
    user_tasks_today = Task.objects.filter(
        assigned_to=request.user
    ).order_by('-is_completed', 'due_date')
    
    # Tâches à venir (avec date d'échéance future)
    user_tasks_upcoming = Task.objects.filter(
        assigned_to=request.user,
        is_completed=False,
        due_date__gt=today
    ).order_by('due_date', 'priority')[:5]  # Limiter à 5 tâches
    
    # Tâches terminées récemment
    user_tasks_completed = Task.objects.filter(
        assigned_to=request.user,
        is_completed=True
    ).order_by('-due_date')[:3]  # Les 3 dernières terminées
    
    context = {
        'task_form': task_form,
        'user_tasks_today': user_tasks_today,
        'user_tasks_upcoming': user_tasks_upcoming,
        'user_tasks_completed': user_tasks_completed,
        'tasks_count_today': user_tasks_today.count(),
        'tasks_count_upcoming': user_tasks_upcoming.count(),
    }
    return render(request, "restoplus/accueil.html", context)

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

    # Exclure l'utilisateur connecté de la liste pour éviter qu'il modifie ses propres permissions
    users = User.objects.exclude(id=request.user.id).select_related('role')
    all_users = User.objects.all().select_related('role')  # Pour les statistiques générales
    roles = Role.objects.all()
    
    # Calculer les statistiques sur tous les utilisateurs
    users_without_role = all_users.filter(role__isnull=True)
    active_users = all_users.filter(is_active=True)

    context = {
    'title': 'Tableau de bord administrateur',
    'users' : users,  # Utilisateurs sans l'utilisateur connecté
    'roles' : roles,
    'users_without_role_count': users_without_role.count(),
    'active_users_count': active_users.count(),
    'total_users_count': all_users.count(),  # Nombre total pour les statistiques
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
            old_role = user.role.name if user.role else "Aucun rôle"
            user.role = role
            user.save()
            messages.success(request,
                        f"Rôle mis à jour avec succès ! {user.get_full_name() or user.username} : {old_role} → {role.name}")
        else:
            old_role = user.role.name if user.role else "Aucun rôle"
            user.role = None
            user.save()
            messages.success(request, f"Rôle retiré avec succès pour {user.get_full_name() or user.username} (ancien rôle : {old_role})")
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
        can_distribute_tasks = request.POST.get('can_distribute_tasks') == 'on'

        if Role.objects.filter(name=name).exists():
            messages.error(request, f"❌ Erreur : Le rôle '{name}' existe déjà !")
        else:
            Role.objects.create(
                name = name,
                description = description,
                can_manage_inventory = can_manage_inventory,
                can_manage_users = can_manage_users,
                can_manage_orders = can_manage_orders,
                can_view_reports=can_view_reports,
                can_distribute_tasks=can_distribute_tasks
            )
            permissions_list = []
            if can_manage_users: permissions_list.append("Gérer les utilisateurs")
            if can_manage_orders: permissions_list.append("Gérer les commandes")
            if can_manage_inventory: permissions_list.append("Gérer l'inventaire")
            if can_view_reports: permissions_list.append("Voir les rapports")
            if can_distribute_tasks: permissions_list.append("Distribuer des tâches à tous")
            
            permissions_text = ", ".join(permissions_list) if permissions_list else "Aucune permission spéciale"
            messages.success(request, f"✅ Nouveau rôle '{name}' créé avec succès ! Permissions : {permissions_text}")
    return redirect('admin_dashboard')


@login_required
def no_access(request):
    """page d'accès refusé"""
    return render(request, 'restoplus/no_acces.html')


@login_required
def get_task_details(request, task_id):
    """Vue pour récupérer les détails d'une tâche"""
    try:
        task = get_object_or_404(Task, id=task_id)
        
        # Vérifier que l'utilisateur peut voir cette tâche
        if request.user not in task.assigned_to.all() and not request.user.is_staff:
            return JsonResponse({'success': False, 'message': 'Permission refusée'})
        
        # Préparer les données de la tâche
        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description or 'Aucune description',
            'category': task.get_category_display(),  # Affichage lisible de la catégorie
            'priority': task.get_priority_display(),  # Affichage lisible de la priorité
            'is_completed': task.is_completed,
            'due_date': task.due_date.strftime('%d/%m/%Y') if task.due_date else None,
            'created_at': task.created_at.strftime('%d/%m/%Y à %H:%M') if task.created_at else 'Non définie',
            'estimated_duration': task.estimated_duration,
            'assigned_users': [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username
                }
                for user in task.assigned_to.all()
            ]
        }
        
        return JsonResponse({
            'success': True,
            'task': task_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})


@login_required
def toggle_task_status(request):
    """Vue pour changer le statut d'une tâche (terminée/non terminée)"""
    if request.method == 'POST':
        try:
            task_id = request.POST.get('task_id')
            if not task_id:
                return JsonResponse({'success': False, 'message': 'ID de tâche manquant'})
            
            task = get_object_or_404(Task, id=task_id)
            
            # Vérifier que l'utilisateur peut modifier cette tâche
            if request.user not in task.assigned_to.all() and not request.user.is_staff:
                return JsonResponse({'success': False, 'message': 'Permission refusée'})
            
            # Changer le statut
            task.is_completed = not task.is_completed
            task.save()
            
            # Message de retour
            status_text = "terminée" if task.is_completed else "réouverte"
            message = f"Tâche '{task.title}' marquée comme {status_text}"
            
            return JsonResponse({
                'success': True, 
                'message': message,
                'is_completed': task.is_completed
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

"""Views pour l'application RestoPlus"""
import json
import locale
from datetime import date, datetime, timedelta
from os import rename
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.core.exceptions import PermissionDenied, ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .forms import UserRegisterForm, UserLoginForm, TaskForm, AvailabilityForm
from .models import User, Role, Task, Notification, Availability, PasswordResetCode
from .notifications import notify_task_assigned, notify_role_assigned

# Configuration de la locale française pour les dates
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR')
    except locale.Error:
        pass  # Garde la locale par défaut si français non disponible

# Create your views here.

@login_required
def accueil(request):
    """Vue pour la page d'accueil."""
    # Gestion du formulaire de tâche
    if request.method == 'POST':
        task_form = TaskForm(request.POST, user=request.user)
        if task_form.is_valid():
            # Vérification des permissions avant de sauvegarder
            assigned_users_from_form = task_form.cleaned_data['assigned_to']
            # Vérifier que l'utilisateur a le droit d'assigner à ces utilisateurs
            if not request.user.can_distribute_tasks_to_all():
                # Si l'utilisateur n'a pas la permission, il ne peut assigner qu'à lui-même
                unauthorized_users = [user for user in assigned_users_from_form if user != request.user]
                if unauthorized_users:
                    unauthorized_names = ", ".join([str(user) for user in unauthorized_users])
                    messages.error(
                        request,
                        request,
                        f"❌ Vous n'avez pas l'autorisation d'assigner des tâches à : {unauthorized_names}. "
                        f"Vous ne pouvez assigner des tâches qu'à vous-même."
                    )
                    # Recréer le formulaire avec les erreurs
                    task_form = TaskForm(request.POST, user=request.user)
                    task_form.add_error('assigned_to', 'Vous n\'avez pas l\'autorisation d\'assigner des tâches à d\'autres utilisateurs.')
                else:
                    # Sauvegarder la tâche si tout est correct
                    task = task_form.save(commit=False)
                    task.save()
                    task_form.save_m2m()
                    assigned_users = list(task.assigned_to.all())
                    notifications = notify_task_assigned(task, assigned_users, request.user)
                    messages.success(request, f"✅ Tâche '{task.title}' créée avec succès et assignée à vous-même !")
                    return redirect('accueil')
            else:
                # L'utilisateur a les permissions, procéder normalement
                task = task_form.save(commit=False)
                task.save()
                task_form.save_m2m()

                # Vérifier qu'au moins un utilisateur est assigné
                assigned_users = list(task.assigned_to.all())
                if not assigned_users:
                    # Si aucun utilisateur n'est assigné, assigner à l'utilisateur actuel par défaut
                    task.assigned_to.add(request.user)
                    assigned_users = [request.user]
                # Créer des notifications pour tous les utilisateurs assignés
                notifications = notify_task_assigned(task, assigned_users, request.user)
                # Message de succès détaillé
                assigned_users_names = ", ".join([str(user) for user in assigned_users])
                if assigned_users_names:
                    notification_count = len(notifications)
                    if notification_count > 0:
                        messages.success(
                            request,
                            request,
                            f"✅ Tâche '{task.title}' créée avec succès ! Assignée à : {assigned_users_names} "
                            f"({notification_count} notification(s) envoyée(s))"
                        )
                    else:
                        messages.success(request, f"Tâche '{task.title}' créée avec succès ! Assignée à : {assigned_users_names}")
                else:
                    messages.success(request, f"Tâche '{task.title}' créée avec succès !")
                return redirect('accueil')
        else:
            # En cas d'erreur, ajouter un message pour informer l'utilisateur
            errors_list = []
            for field_name, field_errors in task_form.errors.items():
                # Ajouter la classe CSS d'erreur au widget
                if field_name in task_form.fields:
                    widget = task_form[field_name].field.widget
                    current_class = widget.attrs.get('class', '')
                    if 'is-invalid' not in current_class:
                        widget.attrs['class'] = current_class + ' is-invalid'

                # Collecter les erreurs pour le message
                for error in field_errors:
                    field_label = task_form.fields[field_name].label if field_name in task_form.fields else field_name
                    errors_list.append(f"{field_label}: {error}")
            if errors_list:
                error_message = "Erreurs dans le formulaire : " + " | ".join(errors_list[:3])
                if len(errors_list) > 3:
                    error_message += f" (et {len(errors_list) - 3} autre(s) erreur(s))"
                messages.error(request, error_message)
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

    # Récupérer les notifications de l'utilisateur
    from .notifications import get_recent_notifications, get_unread_notifications_count
    user_notifications = get_recent_notifications(request.user, limit=10)
    unread_notifications_count = get_unread_notifications_count(request.user)

    context = {
        'task_form': task_form,
        'user_tasks_today': user_tasks_today,
        'user_tasks_upcoming': user_tasks_upcoming,
        'user_tasks_completed': user_tasks_completed,
        'tasks_count_today': user_tasks_today.count(),
        'tasks_count_upcoming': user_tasks_upcoming.count(),
        'user_notifications': user_notifications,
        'unread_notifications_count': unread_notifications_count,
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
        return render(request, 'restoplus/403.html', status=403)

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

# ======================================================================
# 🧑‍💼 EMPLOYÉS ET DISPONIBILITÉS
# ======================================================================

@login_required
def employees_management(request):
    """Permet d'accéder aux données des employés"""
    employes = User.objects.all()
    return render(request,"restoplus/employees_management.html",{"employes": employes})

@login_required
def employee_profile(request, employe_id):
    try:
        employe = User.objects.get(id=employe_id)
    except User.DoesNotExist:
        raise Http404("Aucun employé ne correspond à cet ID.")
    if not request.user.is_staff and request.user.id != employe.id:
        messages.error(request, "Accès refusé : vous ne pouvez consulter que votre profil.")
        return redirect('accueil')
    order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    availabilities = sorted(
    Availability.objects.filter(employe=employe),
    key=lambda a: order.index(a.day))
    if employe.availability_status == User.AvailabilityStatus.NOT_FILLED:
        status_label = "Aucune disponibilité reçue"
        status_class = "secondary"
    elif employe.availability_status == User.AvailabilityStatus.PENDING:
        status_label = "Demande envoyée (en attente de réponse)"
        status_class = "info"
    elif employe.availability_status == User.AvailabilityStatus.FILLED:
        status_label = "Disponibilités complétées "
        status_class = "success"
    else:
        status_label = "Statut inconnu"
        status_class = "dark"

    return render(request, "restoplus/employee_profile.html", {
        "employe": employe,
        "availabilities": availabilities,
        "status_label": status_label,
        "status_class": status_class,
    })

@login_required
@require_POST
def ask_availibilities(request, employe_id):
    """Permet d'envoyer une demande de disponibilités à un employé, si aucune demande n'est déjà active."""
    if not request.user.is_staff:
        raise PermissionDenied("Vous n'avez pas l'autorisation d'envoyer une demande.")
    try:
        employe = User.objects.get(id=employe_id)
    except User.DoesNotExist:
        raise Http404("Aucun employé ne correspond à cet ID")
    if employe.availability_status in[User.AvailabilityStatus.PENDING]:
        messages.warning(request, f"⚠️ Une demande de disponibilités est déjà en attente pour {employe.username}.")
        return redirect('employees_management')
    if employe.availability_status in[User.AvailabilityStatus.NOT_FILLED,User.AvailabilityStatus.FILLED]:
        employe.availability_status = User.AvailabilityStatus.PENDING
        employe.save()
        task_description = (
        "Merci de remplir ton formulaire de disponibilités dès que possible.")
        task = Task.objects.create(
        title="Remplir ses disponibilités",
        estimated_duration=15,
        description=task_description,
        priority="moyenne")
        task.assigned_to.add(employe)
        notify_task_assigned(task, [employe], request.user)
        messages.success(request, f" Une demande de disponibilités a été envoyée à {employe.username}.")
        return redirect('employees_management')
    else :
        messages.warning(request, 'La demande n\'a pu être complétée')
        return redirect('employees_management')

@login_required
def availability_form(request):
    """Formulaire pour remplir les disponibilités"""
    employe = request.user
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            days = AvailabilityForm.DAYS
            for day,_label in days:
                start = form.cleaned_data.get(f"{day}_start")
                end = form.cleaned_data.get(f"{day}_end")
                if start and end:
                    Availability.objects.update_or_create(
                        employe=employe,
                        day=day,
                        defaults={'heure_debut': start, 'heure_fin': end, 'remplie': True}
                    )
                elif start is None and end is None:
                    Availability.objects.filter(employe=employe, day=day).delete()
            employe.availability_status = User.AvailabilityStatus.FILLED
            employe.save()
            messages.success(request, "Disponibilités sauvegardés ✅, merci!")
            return redirect('fill_availability')
    else:
        existing = {a.day: a for a in Availability.objects.filter(employe=employe)}
        initial = {}
        for day,_label in AvailabilityForm.DAYS:
            if day in existing:
                initial[f"{day}_start"] = existing[day].heure_debut
                initial[f"{day}_end"] = existing[day].heure_fin
        form = AvailabilityForm(initial=initial)
    return render(request, 'restoplus/availability_form.html', {"form": form, "employe": employe})




# ======================================================================
# ⚙️ ADMINISTRATION
# ======================================================================

@login_required
def manage_user_role(request, user_id):
    """Modifier le rôle d'un utilisateur"""
    if not request.user.has_permission('can_manage_users'):
        messages.error(request, "Permission refusée")
        return redirect('no_access')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404("Aucun employé ne correspond à cet ID.")
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
            messages.error(request, f"Erreur : Le rôle '{name}' existe déjà !")
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
            messages.success(request, f"Nouveau rôle '{name}' créé avec succès ! Permissions : {permissions_text}")
    messages.success(request, "Modifications effectuées avec succès.")
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

@csrf_exempt
@login_required
def assign_role_to_user(request):
    """Vue pour assigner un rôle à un utilisateur avec notification"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            role_id = data.get('role_id')
            if not user_id or not role_id:
                return JsonResponse({'success': False, 'message': 'Utilisateur et rôle requis'})
            # Vérifier les permissions (seuls les admins ou utilisateurs avec permission peuvent assigner des rôles)
            if not (request.user.is_superuser or request.user.has_permission('can_manage_users')):
                return JsonResponse({'success': False, 'message': 'Permission insuffisante'})
            user = User.objects.get(id=user_id)
            role = Role.objects.get(id=role_id)
            # Sauvegarder l'ancien rôle pour comparaison
            old_role = user.role
            # Assigner le nouveau rôle
            user.role = role
            user.save()
            # Créer une notification si le rôle a changé
            if old_role != role:
                notification = notify_role_assigned(user, role, request.user)
                return JsonResponse({
                    'success': True,
                    'message': f"Rôle '{role.name}' assigné à {user.get_full_name() or user.username}. Notification envoyée.",
                    'notification_sent': True
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': f"L'utilisateur avait déjà le rôle '{role.name}'.",
                    'notification_sent': False
                })

        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Utilisateur introuvable'})
        except Role.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Rôle introuvable'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


@login_required
def get_user_notifications(request):
    """Vue pour récupérer les notifications de l'utilisateur connecté"""
    from .notifications import get_recent_notifications, get_unread_notifications_count
    # Récupérer les notifications récentes
    notifications = get_recent_notifications(request.user, limit=20)
    unread_count = get_unread_notifications_count(request.user)
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'titre': notification.titre,
            'description': notification.description,
            'type': notification.type_notification,
            'type_display': notification.get_type_notification_display(),
            'icon': notification.get_type_display_icon(),
            'color': notification.get_type_display_color(),
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%d/%m/%Y %H:%M'),
            'created_by': notification.created_by.get_full_name() or notification.created_by.username if notification.created_by else None,
        })
    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': unread_count
    })

@csrf_exempt
@login_required
def mark_notification_as_read(request):
    """Vue pour marquer une notification comme lue"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            notification_id = data.get('notification_id')
            if not notification_id:
                return JsonResponse({'success': False, 'message': 'ID de notification requis'})
            notification = Notification.objects.get(
                id=notification_id,
                assigned_to=request.user
            )
            notification.mark_as_read()
            return JsonResponse({
                'success': True,
                'message': 'Notification marquée comme lue'
            })
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Notification introuvable'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def create_test_notification(request):
    """Vue pour créer une notification de test"""
    if request.method == 'POST':
        try:
            from .notifications import create_notification
            notification = create_notification(
                titre="🎉 Notification de test",
                description="Ceci est une notification de test pour vérifier que le système fonctionne correctement ! Si vous voyez ce message, tout est opérationnel.",
                assigned_to=request.user,
                created_by=request.user,
                notification_type='system'
            )
            return JsonResponse({
                'success': True,
                'message': 'Notification de test créée avec succès !',
                'notification_id': notification.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def add_employee(request):
    """Vue pour ajouter un employé (utilisateur)"""
    if not request.user.has_permission('can_manage_users'):
        return render(request, 'restoplus/403.html', status=403)

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            role_id = request.POST.get('role_id')
            if role_id:
                role = Role.objects.get(id=role_id)
                new_user.role = role
                new_user.save()
            messages.success(request, f"Nouvel employé '{new_user.get_full_name() or new_user.username}' ajouté avec succès !")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Erreur lors de l'ajout de l'employé. Veuillez vérifier les informations.")
    else:
        form = UserRegisterForm()
    roles = Role.objects.all()
    return render(request, 'restoplus/add_employee.html',
                  {'form': form,
                   'roles': roles})

@login_required
def edit_employee(request, employe_id):
    """Vue pour éditer un employé"""
    if not request.user.has_permission('can_manage_users'):
        messages.error(request, "Vous n'avez pas les permissions d'accéder à cette page")
        return redirect('no_access')

    try:
        employee = User.objects.get(id=employe_id)
    except User.DoesNotExist:
        raise Http404("Aucun employé ne correspond à cet ID.")

    # Interdiction de se modifier soi-même ici
    if employee == request.user:
        messages.warning(
            request,
            "Vous ne pouvez pas modifier votre propre profil ici. Veuillez utiliser la page de profil."
        )
        return redirect('employees_management')

    form_errors = {}

    if request.method == 'POST':
        employee.first_name = request.POST.get('first_name', '').strip()
        employee.last_name = request.POST.get('last_name', '').strip()
        employee.email = request.POST.get('email', '').strip()
        employee.mobile = request.POST.get('mobile', '').strip()
        employee.poste = request.POST.get('poste', '').strip()
        role_id = request.POST.get('role_id')
        if role_id:
            try:
                role = Role.objects.get(id=role_id)
                old_role = employee.role.name if employee.role else "Aucun rôle"
                employee.role = role
                messages.info(request, f"Rôle mis à jour : {old_role} --> {role.name}")
            except Role.DoesNotExist:
                messages.warning(request, "Rôle sélectionné invalide.")
        else:
            if employee.role:
                old_role = employee.role.name
                messages.info(request, f"Rôle '{old_role}' retiré de l'employé.")
                employee.role = None

        try:
            employee.full_clean(validate_unique=False)
            employee.save()
            employee_display = employee.get_full_name() or employee.username
            messages.success(request, f"{employee_display} a été modifié avec succès.")
            return redirect('employees_management')
        except ValidationError as e:
            form_errors = e.message_dict

    roles = Role.objects.all()
    return render(request, 'restoplus/edit_employee.html', {
        'employee': employee,
        'roles': roles,
        'form_errors': form_errors
    })


@login_required
def delete_employee(request, employe_id):
    """Vue pour supprimer un employé (utilisateur)"""
    if not request.user.has_permission('can_manage_users'):
        return render(request, 'restoplus/403.html', status=403)

    try:
        employee = User.objects.get(id=employe_id)
    except User.DoesNotExist:
        raise Http404("Aucun employé ne correspond à cet ID.")

    if employee == request.user:
        messages.warning(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('employees_management')

    if employee.is_superuser and not request.user.is_superuser:
        messages.error(request, "Vous ne pouvez pas supprimer un Admin.")
        return redirect('employees_management')


    employee_display = employee.get_full_name() or employee.username
    employee.delete()
    messages.success(request, f"Employé '{employee_display}' supprimé avec succès.")
    return redirect('employees_management')


# ======================================================================
#  CRÉATION D'HORAIRES
# ======================================================================

@login_required
def create_schedule(request):
    """Vue pour créer des horaires - Réservée aux administrateurs"""

    # Vérifier que l'utilisateur est administrateur
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, "Accès non autorisé. Seuls les administrateurs peuvent créer des horaires.")
        return redirect('view_schedule')

    # Récupérer le décalage de semaine depuis les paramètres GET
    week_offset = int(request.GET.get('week_offset', 0))

    # Récupérer tous les employés avec leurs disponibilités
    employes = User.objects.all()

    # Créer les jours de la semaine (lundi à dimanche)
    today = datetime.now().date()
    # Trouver le lundi de cette semaine + décalage
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)

    # Vérifier si la semaine peut être modifiée
    # Règle : On peut modifier tant que la semaine n'a pas encore commencé (même si publiée)
    week_has_started = today >= monday
    can_edit_week = not week_has_started

    week_days = []
    days_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    days_keys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    for i in range(7):
        day = monday + timedelta(days=i)
        week_days.append({
            'jour_name': days_names[i],
            'jour_key': days_keys[i],
            'date_short': day.strftime('%d/%m'),
            'date_str': day.strftime('%Y-%m-%d'),
            'date_formatted': day.strftime('%d %B %Y')
        })

    # Récupérer les WorkShifts existants pour cette semaine
    from .models import WorkShift
    week_start = monday
    week_end = monday + timedelta(days=6)

    # Vérifier si l'horaire de cette semaine est déjà publié
    published_shifts_count = WorkShift.objects.filter(
        date__range=[week_start, week_end],
        status=WorkShift.ShiftStatus.PUBLISHED
    ).count()

    # Déterminer si l'horaire est publié (pour affichage d'information)
    is_published = published_shifts_count > 0

    existing_shifts = WorkShift.objects.filter(
        date__range=[week_start, week_end]
    ).select_related('employee').order_by('date', 'heure_debut')

    # Organiser les shifts par employé et jour
    shifts_by_employee = {}
    for shift in existing_shifts:
        emp_id = shift.employee_id
        day_key = days_keys[shift.date.weekday()]  # 0=lundi, 1=mardi, etc.

        if emp_id not in shifts_by_employee:
            shifts_by_employee[emp_id] = {}

        shifts_by_employee[emp_id][day_key] = {
            'heure_debut': shift.heure_debut.strftime('%H:%M'),
            'heure_fin': shift.heure_fin.strftime('%H:%M'),
            'duree_effective': shift.duree_effective_formatted,
            'note': shift.note,
            'has_break': shift.has_break,
            'pause_duree': shift.pause_duree,
            'status': shift.status,
            'id': shift.id,
        }

    # Récupérer les disponibilités pour tous les employés
    avail_qs = Availability.objects.all().select_related('employe')
    availabilities = [
        {
            'employe_id': a.employe_id,
            'day': a.day,                                    # 'monday'...'sunday'
            'heure_debut': a.heure_debut.strftime('%H:%M'),
            'heure_fin': a.heure_fin.strftime('%H:%M'),
            'remplie': a.remplie,
        }
        for a in avail_qs
    ]

    # Forcer la locale française pour le formatage des dates
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR')
        except:
            pass

    # Créer des variables de dates explicites
    week_start_formatted = week_start.strftime('%d %B %Y')
    week_end_formatted = week_end.strftime('%d %B %Y')

    context = {
        'employes': employes,
        'week_days': week_days,
        'week_days_json': week_days,
        'availabilities_json': availabilities,  # Pas de json.dumps() ici car json_script le fait automatiquement
        'shifts_by_employee': shifts_by_employee,
        'week_start_formatted': week_start_formatted,
        'week_end_formatted': week_end_formatted,
        'week_schedule': {
            'status': 'published' if is_published else 'draft',
            'can_be_edited': can_edit_week,  # Permettre l'édition tant que la semaine n'a pas commencé
            'is_published': is_published,
            'week_start': week_start_formatted,
            'week_end': week_end_formatted,
            'week_offset': week_offset,
        },
    }

    return render(request, 'restoplus/horaire_creation.html', context)


@login_required
def view_schedule(request):
    """Vue pour afficher les horairebliés en lecture seule"""

    # Récupérer tous les employés
    employes = User.objects.all()

    # Récupérer le décalage de semaine depuis les paramètres GET
    week_offset = int(request.GET.get('week_offset', 0))
    # Créer les jours de la semaine (lundi à dimanche)
    today = datetime.now().date()
    # Trouver le lundi de cette semaine + décalage
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)

    week_has_started = today >= monday




    week_days = []
    days_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    days_keys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    for i in range(7):
        day = monday + timedelta(days=i)
        week_days.append({
            'rename': days_names[i],
            'jour_key': days_keys[i],
            'date_short': day.strftime('%d/%m'),
            'date_str': day.strftime('%Y-%m-%d'),
            'date_formatted': day.strftime('%d %B %Y')
        })

    # Récupérer les shifts publiés pour cette semaine
    from .models import WorkShift
    week_start = monday
    week_end = monday + timedelta(days=6)

    shifts = WorkShift.objects.filter(
        date__range=[week_start, week_end],
        status=WorkShift.ShiftStatus.PUBLISHED
    ).select_related('employee').order_by('date', 'heure_debut')

    # Organiser les shifts par employé et jour
    shifts_by_employee = {}
    for shift in shifts:
        emp_id = shift.employee_id
        day_key = days_keys[shift.date.weekday()]  # 0=lundi, 1=mardi, etc.

        if emp_id not in shifts_by_employee:
            shifts_by_employee[emp_id] = {}

        shifts_by_employee[emp_id][day_key] = {
            'heure_debut': shift.heure_debut.strftime('%H:%M'),
            'heure_fin': shift.heure_fin.strftime('%H:%M'),
            'duree_effective': shift.duree_effective_formatted,
            'note': shift.note,
            'has_break': shift.has_break,
            'pause_duree': shift.pause_duree,
        }

    # Déterminer le statut de l'horaire pour cette semaine
    published_shifts_count = WorkShift.objects.filter(
        date__range=[week_start, week_end],
        status=WorkShift.ShiftStatus.PUBLISHED
    ).count()

    # Si il y a des shifts publiés, l'horaire est publié et ne peut pas être modifié
    is_published = published_shifts_count > 0
    can_modify = not week_has_started

    context = {
        'employes': employes,
        'week_days': week_days,
        'shifts_by_employee': shifts_by_employee,
        'week_schedule': {
            'status': 'published' if is_published else 'draft',
            'week_start': week_start.strftime('%d/%m/%Y'),
            'week_end': week_end.strftime('%d/%m/%Y'),
            'is_published': is_published,
            'can_modify': can_modify,
        },
    }

    return render(request, 'restoplus/view_schedule.html', context)


@login_required
@require_POST
def publish_schedule(request):
    """Publie les horaires depuis localStorage vers la bse de données - Réservé aux administrateurs"""

    # Vérifier que l'utilisateur est administrateur
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'message': 'Accès non autorisé. Seuls les administrateurs peuvent publier des horaires.'
        }, status=403)

    try:
        # Récupérer les données JSON depuis la requête
        data = json.loads(request.body)
        shifts_data = data.get('shifts', {})

        published_count = 0
        errors = []

        # Parcourir chaque shift et l'enregistrer en base
        for shift_key, shift_info in shifts_data.items():
            try:
                # Extraire employee_id et date du key: "shift_1_2025-10-28"
                parts = shift_key.split('_')
                if len(parts) >= 3:
                    employee_id = int(parts[1])
                    date_str = parts[2]
                    shift_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                    # Récupérer l'employé
                    employee = User.objects.get(id=employee_id)

                    # Créer ou mettre à jour le WorkShift
                    from .models import WorkShift
                    shift, created = WorkShift.objects.update_or_create(
                        employee=employee,
                        date=shift_date,
                        defaults={
                            'heure_debut': datetime.strptime(shift_info['heure_debut'], '%H:%M').time(),
                            'heure_fin': datetime.strptime(shift_info['heure_fin'], '%H:%M').time(),
                            'pause_duree': shift_info.get('pause_duree', 30),
                            'has_break': shift_info.get('pause_duree', 30) > 0,
                            'note': shift_info.get('note', ''),
                            'status': WorkShift.ShiftStatus.PUBLISHED,
                            'created_by': request.user,
                        }
                    )

                    published_count += 1

            except (ValueError, User.DoesNotExist) as e:
                errors.append(f"Erreur avec {shift_key}: {str(e)}")
                continue

        if errors:
            return JsonResponse({
                'success': False,
                'message': f'{published_count} horaires publiés, {len(errors)} erreurs',
                'errors': errors
            })
        else:
            return JsonResponse({
                'success': True,
                'message': f'{published_count} horaires publiés avec succès',
                'published_count': published_count
            })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Données JSON invalides'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur serveur: {str(e)}'
        })



def custom_403_view(request, exception=None):
    """Vue personnalisée pour les erreurs 403 de permission refusée"""
    return render(request, 'restoplus/403.html', status=403)

def custom_404_view(request, exception=None):
    """Vue personnalisée pour les erreurs 404 de page non trouvée"""
    return render(request, 'restoplus/404.html', status=404)
    return redirect('employees_management')


# ==========================================
# VUES POUR LA RÉINITIALISATION DE MOT DE PASSE
# ==========================================

def password_reset_request(request):
    """Étape 1: Saisie de l'adresse email pour la réinitialisation"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()

        if not email:
            messages.error(request, "❌ Veuillez saisir une adresse email.")
            return render(request, 'registration/password_reset_request.html')

        # Vérifier si l'email existe dans notre base de données
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Pour des raisons de sécurité, on ne révèle pas si l'email existe ou non
            messages.info(request,
                "📧 Si cette adresse email est enregistrée dans notre système, "
                "vous recevrez un code de réinitialisation dans quelques minutes.")
            return render(request, 'registration/password_reset_request.html')

        # Vérifier le rate limiting (max 1 code par minute)
        if PasswordResetCode.has_recent_code(email, minutes=1):
            messages.warning(request,
                "⏱️ Un code de réinitialisation a déjà été envoyé récemment. "
                "Veuillez attendre 1 minute avant de demander un nouveau code.")
            return render(request, 'registration/password_reset_request.html')

        # Nettoyer les anciens codes et créer un nouveau
        try:
            reset_code = PasswordResetCode.create_for_email(email)

            # Envoyer l'email avec le code
            subject = "🔑 Code de réinitialisation - RestoPLus"
            message = f"""
Bonjour,

Vous avez demandé la réinitialisation de votre mot de passe pour RestoPLus.

Votre code de réinitialisation est : {reset_code.code}

Ce code est valide pendant 15 minutes et ne peut être utilisé qu'une seule fois.

Si vous n'avez pas demandé cette réinitialisation, ignorez simplement ce message.

L'équipe RestoPLus
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )

            messages.success(request,
                "📧 Un code de réinitialisation a été envoyé à votre adresse email. "
                "Vérifiez votre boîte de réception et vos spam.")

            # Rediriger vers la page de saisie du code avec l'email en session
            request.session['reset_email'] = email
            return redirect('password_reset_verify')

        except Exception as e:
            messages.error(request,
                "❌ Une erreur s'est produite lors de l'envoi de l'email. "
                "Veuillez réessayer plus tard.")
            return render(request, 'registration/password_reset_request.html')

    return render(request, 'registration/password_reset_request.html')


def password_reset_verify(request):
    """Étape 2: Saisie et vérification du code de réinitialisation"""
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, "❌ Session expirée. Veuillez recommencer la procédure.")
        return redirect('password_reset_request')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()

        if not code:
            messages.error(request, "❌ Veuillez saisir le code de réinitialisation.")
            return render(request, 'registration/password_reset_verify.html', {'email': email})

        if len(code) != 6:
            messages.error(request, "❌ Le code doit contenir exactement 6 caractères.")
            return render(request, 'registration/password_reset_verify.html', {'email': email})

        # Chercher le code valide
        reset_code = PasswordResetCode.get_valid_code(email, code)

        if not reset_code:
            messages.error(request, "❌ Code invalide ou expiré. Veuillez vérifier et réessayer.")
            return render(request, 'registration/password_reset_verify.html', {'email': email})

        # Vérifier les tentatives
        if not reset_code.can_attempt():
            messages.error(request,
                "❌ Trop de tentatives invalides. Veuillez demander un nouveau code.")
            return redirect('password_reset_request')

        # Incrémenter les tentatives avant validation
        reset_code.increment_attempts()

        # Valider le code (vérification redondante pour sécurité)
        if reset_code.code != code:
            messages.error(request, "❌ Code incorrect. Tentatives restantes : " +
                          str(5 - reset_code.attempts))
            return render(request, 'registration/password_reset_verify.html', {'email': email})

        # Code valide ! Passer à l'étape suivante
        request.session['reset_code_id'] = reset_code.id
        messages.success(request, "✅ Code validé avec succès !")
        return redirect('password_reset_confirm')

    return render(request, 'registration/password_reset_verify.html', {'email': email})


def password_reset_confirm(request):
    """Étape 3: Saisie du nouveau mot de passe"""
    reset_code_id = request.session.get('reset_code_id')
    if not reset_code_id:
        messages.error(request, "❌ Session expirée. Veuillez recommencer la procédure.")
        return redirect('password_reset_request')

    try:
        reset_code = PasswordResetCode.objects.get(id=reset_code_id)
        if not reset_code.is_valid():
            messages.error(request, "❌ Code expiré. Veuillez recommencer la procédure.")
            return redirect('password_reset_request')
    except PasswordResetCode.DoesNotExist:
        messages.error(request, "❌ Code invalide. Veuillez recommencer la procédure.")
        return redirect('password_reset_request')

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        # Validation du mot de passe
        if not password1 or not password2:
            messages.error(request, "❌ Tous les champs sont obligatoires.")
            return render(request, 'registration/password_reset_confirm.html')

        if password1 != password2:
            messages.error(request, "❌ Les mots de passe ne correspondent pas.")
            return render(request, 'registration/password_reset_confirm.html')

        if len(password1) < 8:
            messages.error(request, "❌ Le mot de passe doit contenir au moins 8 caractères.")
            return render(request, 'registration/password_reset_confirm.html')

        # Mettre à jour le mot de passe de l'utilisateur
        try:
            user = User.objects.get(email=reset_code.email)
            user.set_password(password1)
            user.save()

            # Marquer le code comme utilisé
            reset_code.mark_as_used()

            # Nettoyer la session
            if 'reset_email' in request.session:
                del request.session['reset_email']
            if 'reset_code_id' in request.session:
                del request.session['reset_code_id']

            messages.success(request,
                "✅ Votre mot de passe a été mis à jour avec succès ! "
                "Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.")

            return redirect('login')

        except User.DoesNotExist:
            messages.error(request, "❌ Utilisateur introuvable. Veuillez recommencer la procédure.")
            return redirect('password_reset_request')
        except Exception as e:
            messages.error(request, "❌ Une erreur s'est produite. Veuillez réessayer.")
            return render(request, 'registration/password_reset_confirm.html')

    return render(request, 'registration/password_reset_confirm.html')


def password_reset_complete(request):
    """Étape 4: Confirmation de la réinitialisation"""
    # Cette vue peut être utilisée pour afficher une page de confirmation
    # ou rediriger directement vers la page de connexion
    return render(request, 'registration/password_reset_complete.html')

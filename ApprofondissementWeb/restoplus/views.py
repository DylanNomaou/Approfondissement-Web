from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import login
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserLoginForm, TaskForm,AvailabilityForm
from .models import User, Role, Task, Notification,Availability, Task
from .notifications import notify_task_assigned, notify_role_assigned
from datetime import date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import json


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
    
    availabilities = Availability.objects.filter(employe=employe).order_by('day')
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
    if employe.availability_status in[User.AvailabilityStatus.PENDING,User.AvailabilityStatus.FILLED]:
        messages.warning(request, f"⚠️ Une demande de disponibilités est déjà en attente pour {employe.username}.")
        return redirect('employees_management')

    if employe.availability_status==User.AvailabilityStatus.NOT_FILLED:
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
        messages.warning('La demande n\a pu être complétée')
        return redirect('employees_management')

@login_required
def availability_form(request):
    """Formulaire pour remplir les disponibilités"""
    employe = request.user
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            days = [
                ('monday', 'Lundi'),
                ('tuesday', 'Mardi'),
                ('wednesday', 'Mercredi'),
                ('thursday', 'Jeudi'),
                ('friday', 'Vendredi'),
                ('saturday', 'Samedi'),
                ('sunday', 'Dimanche'),
            ]
            for day_key, day_label in days:
                start = form.cleaned_data.get(f"{day_key}_start")
                end = form.cleaned_data.get(f"{day_key}_end")
                if start and end:
                    Availability.objects.update_or_create(
                        employe=employe,
                        day=day_key,
                        defaults={'heure_debut': start, 'heure_fin': end, 'remplie': True}
                    )
            employe.availability_status = User.AvailabilityStatus.FILLED
            employe.save()
            messages.success(request, "Disponibilités sauvegardés ✅, merci!")
            return redirect('fill_availability') 
    else:
        existing = {a.day: a for a in Availability.objects.filter(employe=employe)}
        initial = {}
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
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

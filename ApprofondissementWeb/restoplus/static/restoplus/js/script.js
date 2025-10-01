/**
 * SCRIPT.JS - Gestion des modals de tâches
 */

console.log('=== SCRIPT CHARGÉ ===');

// Fonction pour remplir le modal avec les données d'une tâche
function fillTaskModal(taskData) {
    console.log('Remplissage du modal avec:', taskData);
    
    // Titre
    const titleElement = document.getElementById('taskDetailTitle');
    if (titleElement) {
        titleElement.textContent = taskData.title || 'Titre non défini';
        titleElement.style.color = '';
        titleElement.style.fontSize = '';
    }
    
    // Statut
    const statusElement = document.getElementById('taskDetailStatus');
    if (statusElement) {
        statusElement.textContent = taskData.is_completed ? 'Terminé' : 'En cours';
        statusElement.className = taskData.is_completed ? 'badge bg-success fs-6 px-3 py-2' : 'badge bg-warning fs-6 px-3 py-2';
    }
    
    // Description
    const descElement = document.getElementById('taskDetailDescription');
    if (descElement) {
        descElement.textContent = taskData.description || 'Aucune description';
        descElement.className = 'fs-5 mb-0 text-dark';
    }
    
    // Priorité
    const priorityElement = document.getElementById('taskDetailPriority');
    if (priorityElement) {
        priorityElement.textContent = taskData.priority || 'Non définie';
        // Colorer selon la priorité
        const priorityColors = {
            'Urgente': 'fs-5 fw-bold text-danger',
            'Haute': 'fs-5 fw-bold text-warning',
            'Moyenne': 'fs-5 fw-bold text-info',
            'Basse': 'fs-5 fw-bold text-secondary'
        };
        priorityElement.className = priorityColors[taskData.priority] || 'fs-5 fw-bold text-muted';
    }
    
    // Catégorie
    const categoryElement = document.getElementById('taskDetailCategory');
    if (categoryElement) {
        categoryElement.textContent = taskData.category || 'Non définie';
        categoryElement.className = 'badge bg-secondary fs-6 px-3 py-2';
    }
    
    // Date d'échéance
    const dueDateElement = document.getElementById('taskDetailDueDate');
    if (dueDateElement) {
        if (taskData.due_date) {
            dueDateElement.textContent = taskData.due_date;
            // Vérifier si la date est proche ou dépassée
            const today = new Date();
            const dueDate = new Date(taskData.due_date.split('/').reverse().join('-'));
            const diffTime = dueDate - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays < 0) {
                dueDateElement.className = 'fs-5 text-danger fw-bold';
                dueDateElement.textContent += ' En retard!';
            } else if (diffDays <= 3) {
                dueDateElement.className = 'fs-5 text-warning fw-bold';
                dueDateElement.textContent += ' Urgent!';
            } else {
                dueDateElement.className = 'fs-5 text-success fw-bold';
            }
        } else {
            dueDateElement.textContent = 'Non définie';
            dueDateElement.className = 'fs-5 text-muted';
        }
    }
    
    // Durée estimée
    const durationElement = document.getElementById('taskDetailDuration');
    if (durationElement) {
        if (taskData.estimated_duration) {
            const hours = Math.floor(taskData.estimated_duration / 60);
            const minutes = taskData.estimated_duration % 60;
            let durationText = '';
            if (hours > 0) {
                durationText += `${hours}h `;
            }
            if (minutes > 0) {
                durationText += `${minutes}min`;
            }
            durationElement.textContent = durationText.trim();
            durationElement.className = 'fs-5 text-info fw-bold';
        } else {
            durationElement.textContent = 'Non définie';
            durationElement.className = 'fs-5 text-muted';
        }
    }
    
    // Utilisateurs assignés
    const assignedElement = document.getElementById('taskDetailAssignedUsers');
    if (assignedElement) {
        assignedElement.innerHTML = '';
        if (taskData.assigned_users && taskData.assigned_users.length > 0) {
            taskData.assigned_users.forEach(user => {
                const badge = document.createElement('span');
                badge.className = 'badge bg-primary me-2 mb-2 fs-6 px-3 py-2';
                badge.textContent = user.full_name || user.username || user.email || 'Utilisateur inconnu';
                assignedElement.appendChild(badge);
            });
        } else {
            assignedElement.innerHTML = '<span class="fs-6 text-muted">Aucun utilisateur assigné</span>';
        }
    }
    
    // Date de création
    const createdAtElement = document.getElementById('taskDetailCreatedAt');
    if (createdAtElement) {
        createdAtElement.textContent = taskData.created_at || '--';
        createdAtElement.className = 'fs-6 text-dark fw-bold';
    }
    
    // Préparer le formulaire de statut
    const taskIdInput = document.getElementById('taskDetailId');
    if (taskIdInput) {
        taskIdInput.value = taskData.id || '';
    }
    
    const currentStatusInput = document.getElementById('taskDetailCurrentStatus');
    if (currentStatusInput) {
        currentStatusInput.value = taskData.is_completed ? 'True' : 'False';
    }
    
    // Bouton de toggle
    const toggleBtn = document.getElementById('toggleStatusBtn');
    if (toggleBtn) {
        const iconClass = taskData.is_completed ? 'bi bi-arrow-clockwise me-2' : 'bi bi-check-circle me-2';
        toggleBtn.innerHTML = `<i class="${iconClass}"></i>${taskData.is_completed ? 'Marquer comme en cours' : 'Marquer comme terminé'}`;
        toggleBtn.className = taskData.is_completed ? 'btn btn-warning btn-lg flex-fill' : 'btn btn-success btn-lg flex-fill';
    }
}

// Fonction pour ouvrir le modal avec les données d'une tâche
function openTaskModal(taskId) {
    console.log('Ouverture du modal pour la tâche:', taskId);
    
    // Récupérer les détails de la tâche via AJAX
    fetch(`/task-details/${taskId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Données reçues:', data.task);
                fillTaskModal(data.task);
                
                // Ouvrir le modal
                const modal = document.getElementById('taskDetailsModal');
                if (modal) {
                    modal.style.display = 'block';
                    modal.classList.add('show');
                    modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
                    
                    // Ajouter le backdrop
                    const backdrop = document.createElement('div');
                    backdrop.className = 'modal-backdrop fade show';
                    backdrop.id = 'modalBackdrop';
                    document.body.appendChild(backdrop);
                    
                    console.log('Modal ouvert avec les vraies données !');
                }
            } else {
                console.error('Erreur lors de la récupération des données:', data.message);
                alert('Erreur: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Erreur réseau:', error);
            alert('Erreur de connexion');
        });
}

// Fonction ultra-simple pour ouvrir le modal avec des données
function openModal() {
    console.log('Tentative d\'ouverture du modal...');
    
    const modal = document.getElementById('taskDetailsModal');
    if (modal) {
        console.log('Modal trouvé !');
        
        // Remplir avec des données de test VISIBLES
        const titleElement = document.getElementById('taskDetailTitle');
        if (titleElement) {
            titleElement.textContent = 'TÂCHE DE TEST - DONNÉES VISIBLES';
            titleElement.style.color = 'red';
            titleElement.style.fontSize = '1.5em';
        }
        
        const descElement = document.getElementById('taskDetailDescription');
        if (descElement) {
            descElement.textContent = 'Ceci est une description de test qui devrait être VISIBLE dans le modal. Si vous voyez ce texte, le modal affiche correctement les données !';
            descElement.style.color = 'blue';
            descElement.style.fontSize = '1.1em';
        }
        
        const statusElement = document.getElementById('taskDetailStatus');
        if (statusElement) {
            statusElement.textContent = 'EN COURS';
            statusElement.className = 'badge bg-warning';
            statusElement.style.fontSize = '1.2em';
        }
        
        const priorityElement = document.getElementById('taskDetailPriority');
        if (priorityElement) {
            priorityElement.textContent = 'HAUTE PRIORITÉ';
            priorityElement.style.color = 'red';
            priorityElement.style.fontWeight = 'bold';
        }
        
        const assignedElement = document.getElementById('taskDetailAssignedUsers');
        if (assignedElement) {
            assignedElement.innerHTML = '<span class="badge bg-info me-1">Utilisateur Test 1</span><span class="badge bg-info me-1">Utilisateur Test 2</span>';
        }
        
        const createdAtElement = document.getElementById('taskDetailCreatedAt');
        if (createdAtElement) {
            createdAtElement.textContent = '01/01/2025 à 10:00';
            createdAtElement.style.fontWeight = 'bold';
        }
        
        const createdByElement = document.getElementById('taskDetailCreatedBy');
        if (createdByElement) {
            createdByElement.textContent = 'Admin Test';
            createdByElement.style.fontWeight = 'bold';
        }
        
        // Forcer l'ouverture avec du CSS pur
        modal.style.display = 'block';
        modal.classList.add('show');
        modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
        
        // Ajouter aussi un backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        backdrop.id = 'modalBackdrop';
        document.body.appendChild(backdrop);
        
        console.log('Modal forcé ouvert avec données de test !');
        return true;
    } else {
        console.error('Modal non trouvé !');
        return false;
    }
}

// Fonction pour fermer le modal
function closeModal() {
    const modal = document.getElementById('taskDetailsModal');
    const backdrop = document.getElementById('modalBackdrop');
    
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }
    
    if (backdrop) {
        backdrop.remove();
    }
    
    console.log('Modal fermé');
}

// Quand la page est chargée
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM chargé !');
    
    // GESTION DES CLICS SUR LES TÂCHES
    console.log('Ajout des gestionnaires de clic sur les tâches...');
    
    // Délégation d'événements pour les clics sur les tâches
    document.addEventListener('click', function(e) {
        // Vérifier si l'élément cliqué est une tâche ou est contenu dans une tâche
        const taskElement = e.target.closest('.task-clickable');
        
        if (taskElement) {
            console.log('Clic détecté sur une tâche !');
            e.preventDefault();
            e.stopPropagation();
            
            const taskId = taskElement.getAttribute('data-task-id');
            console.log('ID de la tâche:', taskId);
            
            if (taskId) {
                openTaskModal(taskId);
            } else {
                console.error('Aucun ID de tâche trouvé !');
            }
        }
    });
    
    // Ajouter gestionnaire de clic sur les boutons de fermeture
    setTimeout(() => {
        const closeButtons = document.querySelectorAll('[data-bs-dismiss="modal"], .btn-close');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', closeModal);
        });
        
        // Clic sur le backdrop pour fermer
        document.addEventListener('click', function(e) {
            if (e.target && e.target.id === 'modalBackdrop') {
                closeModal();
            }
        });
    }, 1000);
    
    // *** GESTION DU FORMULAIRE DE CHANGEMENT DE STATUT ***
    setTimeout(() => {
        const statusForm = document.getElementById('taskStatusForm');
        if (statusForm) {
            console.log('Gestionnaire de formulaire ajouté');
            statusForm.addEventListener('submit', function(e) {
                e.preventDefault();
                console.log('Formulaire soumis !');
                
                const formData = new FormData(this);
                const toggleBtn = document.getElementById('toggleStatusBtn');
                const originalText = toggleBtn.textContent;
                
                // Désactiver le bouton pendant le traitement
                toggleBtn.disabled = true;
                toggleBtn.textContent = 'Traitement...';
                
                // Envoyer la requête AJAX
                fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Réponse reçue:', data);
                    if (data.success) {
                        // Mettre à jour l'affichage du modal
                        updateTaskStatusInModal(data.is_completed);
                        
                        // Mettre à jour la liste principale
                        updateTaskInMainList(formData.get('task_id'), data.is_completed);
                        
                        // Afficher un message de succès
                        showNotification(data.message, 'success');
                    } else {
                        showNotification(data.message || 'Erreur lors du changement de statut', 'error');
                    }
                })
                .catch(error => {
                    console.error('Erreur:', error);
                    showNotification('Erreur de connexion', 'error');
                })
                .finally(() => {
                    // Réactiver le bouton
                    toggleBtn.disabled = false;
                });
            });
        } else {
            console.log('Formulaire de statut non trouvé');
        }
    }, 1500);
    
    // *** GESTION DU FORMULAIRE D'AJOUT DE TÂCHES ***
    setTimeout(() => {
        const addTaskForm = document.getElementById('addTaskForm');
        const descriptionField = document.getElementById('taskDescription');
        
        // Compteur de caractères pour la description
        if (descriptionField) {
            const charCount = document.getElementById('charCount');
            if (charCount) {
                descriptionField.addEventListener('input', function() {
                    charCount.textContent = this.value.length;
                    if (this.value.length > 450) {
                        charCount.parentElement.classList.add('text-warning');
                    } else {
                        charCount.parentElement.classList.remove('text-warning');
                    }
                });
            }
        }
        
        // Gestion de la soumission du formulaire d'ajout
        if (addTaskForm) {
            console.log('Gestionnaire de formulaire d\'ajout ajouté');
            addTaskForm.addEventListener('submit', function(e) {
                // Laisser la soumission normale du formulaire Django
                console.log('Soumission du formulaire d\'ajout de tâche');
                
                // Optionnel : ajouter un indicateur de chargement
                const submitBtn = addTaskForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Création en cours...';
                }
            });
        }
        
        // Réinitialiser le formulaire quand le modal se ferme
        const addTaskModal = document.getElementById('addTaskModal');
        if (addTaskModal) {
            addTaskModal.addEventListener('hidden.bs.modal', function() {
                if (addTaskForm) {
                    addTaskForm.reset();
                    // Réinitialiser le compteur de caractères
                    const charCount = document.getElementById('charCount');
                    if (charCount) {
                        charCount.textContent = '0';
                        charCount.parentElement.classList.remove('text-warning');
                    }
                    // Réinitialiser le bouton
                    const submitBtn = addTaskForm.querySelector('button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<i class="bi bi-check-circle me-2"></i>Créer la tâche';
                    }
                }
            });
        }
    }, 1500);
});
    


// =========================================
// FONCTIONS UTILITAIRES
// =========================================

/**
 * Formate une date pour l'affichage
 * @param {string} dateString - La date à formater
 * @returns {string} - La date formatée
 */
function formatDate(dateString) {
    if (!dateString) return 'Non définie';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * Capitalise la première lettre d'une chaîne
 * @param {string} str - La chaîne à capitaliser
 * @returns {string} - La chaîne capitalisée
 */
function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Met à jour l'affichage du statut dans le modal
 * @param {boolean} isCompleted - Nouvel état de la tâche
 */
function updateTaskStatusInModal(isCompleted) {
    const statusElement = document.getElementById('taskDetailStatus');
    const toggleBtn = document.getElementById('toggleStatusBtn');
    const currentStatusInput = document.getElementById('taskDetailCurrentStatus');
    
    if (statusElement) {
        statusElement.textContent = isCompleted ? 'Terminé' : 'En cours';
        statusElement.className = isCompleted ? 'badge bg-success fs-6 px-3 py-2' : 'badge bg-warning fs-6 px-3 py-2';
    }
    
    if (toggleBtn) {
        const iconClass = isCompleted ? 'bi bi-arrow-clockwise me-2' : 'bi bi-check-circle me-2';
        toggleBtn.innerHTML = `<i class="${iconClass}"></i>${isCompleted ? 'Marquer comme en cours' : 'Marquer comme terminé'}`;
        toggleBtn.className = isCompleted ? 'btn btn-warning btn-lg flex-fill' : 'btn btn-success btn-lg flex-fill';
    }
    
    if (currentStatusInput) {
        currentStatusInput.value = isCompleted ? 'True' : 'False';
    }
}

/**
 * Met à jour l'affichage d'une tâche dans la liste principale
 * @param {string} taskId - ID de la tâche
 * @param {boolean} isCompleted - Nouvel état de la tâche
 */
function updateTaskInMainList(taskId, isCompleted) {
    console.log(`Mise à jour de la tâche ${taskId} vers ${isCompleted ? 'terminé' : 'en cours'}`);
    const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
    if (taskElement) {
        // Mettre à jour les classes CSS principales
        if (isCompleted) {
            taskElement.classList.remove('task-pending');
            taskElement.classList.add('task-completed');
        } else {
            taskElement.classList.remove('task-completed');
            taskElement.classList.add('task-pending');
        }
        
        // Mettre à jour l'attribut data-task-completed
        taskElement.setAttribute('data-task-completed', isCompleted ? 'true' : 'false');
        
        // Mettre à jour l'icône (checkmark vs priority indicator)
        const iconContainer = taskElement.querySelector('.d-flex.align-items-center.justify-content-between.mb-2');
        if (iconContainer) {
            const firstChild = iconContainer.firstElementChild;
            if (isCompleted) {
                // Remplacer par l'icône de tâche terminée
                firstChild.className = 'task-completed-icon text-success fs-5';
                firstChild.innerHTML = '✓'; // Checkmark
            } else {
                // Remettre l'indicateur de priorité (on utilise une classe générique)
                firstChild.className = 'priority-indicator priority-medium';
                firstChild.innerHTML = '';
            }
        }
        
        // Mettre à jour le titre (souligné si terminé)
        const titleElement = taskElement.querySelector('.task-title-horizontal');
        if (titleElement) {
            if (isCompleted) {
                titleElement.classList.add('text-decoration-line-through', 'text-muted');
                titleElement.classList.remove('text-dark');
            } else {
                titleElement.classList.remove('text-decoration-line-through', 'text-muted');
                titleElement.classList.add('text-dark');
            }
        }
        
        // Mettre à jour le badge/statut en bas
        const taskContent = taskElement.querySelector('.task-content-horizontal');
        if (taskContent) {
            // Supprimer l'ancien badge ou texte de catégorie
            const existingBadge = taskContent.querySelector('.badge');
            const existingCategory = taskContent.querySelector('small.text-muted');
            
            if (existingBadge) existingBadge.remove();
            if (existingCategory) existingCategory.remove();
            
            // Ajouter le nouveau statut
            if (isCompleted) {
                const badge = document.createElement('span');
                badge.className = 'badge bg-success small';
                badge.innerHTML = '<span class="check-small me-1"></span>Terminé';
                taskContent.appendChild(badge);
            } else {
                // Récupérer la catégorie depuis les data attributes
                const category = taskElement.getAttribute('data-task-category') || 'Tâche';
                const categoryElement = document.createElement('small');
                categoryElement.className = 'text-muted';
                categoryElement.textContent = category;
                taskContent.appendChild(categoryElement);
            }
        }
        
        console.log(`Tâche ${taskId} mise à jour avec succès`);
    } else {
        console.error(`Tâche avec l'ID ${taskId} non trouvée dans la liste`);
    }
}

/**
 * Affiche une notification
 * @param {string} message - Message à afficher
 * @param {string} type - Type de notification ('success', 'error', 'info', 'warning')
 */
function showNotification(message, type = 'info') {
    // Créer l'élément de notification
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        <span>${message}</span>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Ajouter au body
    document.body.appendChild(notification);
    
    // Supprimer automatiquement après 5 secondes
    setTimeout(() => {
        if (notification && notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// JavaScript pour la gestion des horaires

class HoraireManager {
    constructor() {
        this.currentWeekOffset = 0;

        // Récupérer les données des jours depuis Django
        const weekDaysElement = document.getElementById('week-days-data');
        if (weekDaysElement && weekDaysElement.textContent) {
            try {
                this.weekDays = JSON.parse(weekDaysElement.textContent);
                console.log('Données des jours chargées depuis Django:', this.weekDays);
            } catch (error) {
                console.error('Erreur lors du parsing des données JSON:', error);
                this.weekDays = this.generateDefaultWeekDays();
            }
        } else {
            console.warn('Données des jours de la semaine non trouvées, génération par défaut');
            this.weekDays = this.generateDefaultWeekDays();
        }

        console.log('Données finales des jours:', this.weekDays);
        this.init();
    }

    generateDefaultWeekDays() {
        // Générer les jours par défaut si les données Django ne sont pas disponibles
        const today = new Date();
        const mondayDate = new Date(today);
        const dayOfWeek = today.getDay();
        const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
        mondayDate.setDate(today.getDate() + mondayOffset);

        return this.generateWeekDays(mondayDate);
    }

    init() {
        this.bindEvents();
        // S'assurer que l'affichage initial est correct
        if (this.weekDays && this.weekDays.length > 0) {
            this.updateWeekDisplay(this.weekDays);
        }
    }

    bindEvents() {
        console.log('🔧 Initialisation des événements navigation...');
        
        // Navigation de semaine uniquement - les cellules sont gérées ailleurs
        const prevWeekBtn = document.getElementById('prev-week-btn');
        const nextWeekBtn = document.getElementById('next-week-btn');

        if (prevWeekBtn) {
            prevWeekBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.changeWeek(-1);
            });
            console.log('✅ Bouton semaine précédente attaché');
        }

        if (nextWeekBtn) {
            nextWeekBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.changeWeek(1);
            });
            console.log('✅ Bouton semaine suivante attaché');
        }

        console.log('✅ Événements navigation attachés');
    }

    bindScheduleCellEvents() {
        // Gérer les clics sur les cellules d'horaire
        const scheduleCells = document.querySelectorAll('.schedule-cell');
        console.log('Nombre de cellules trouvées:', scheduleCells.length);
        
        scheduleCells.forEach((cell, index) => {
            // Ajouter le curseur pointer pour indiquer que c'est cliquable
            cell.style.cursor = 'pointer';
            cell.title = 'Cliquer pour définir les horaires';
            
            cell.addEventListener('click', (e) => {
                console.log('Clic détecté sur cellule');
                this.handleScheduleCellClick(e, cell);
            });
        });

        // Gérer les clics sur les boutons d'édition
        const editButtons = document.querySelectorAll('.edit-time-btn');
        console.log('Nombre de boutons d\'édition trouvés:', editButtons.length);
        
        editButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                console.log('Clic détecté sur bouton d\'édition');
                e.stopPropagation(); // Empêcher le déclenchement du clic sur la cellule
                this.handleEditTimeClick(e, btn);
            });
        });
    }

    handleScheduleCellClick(event, cell) {
        const employeeId = cell.dataset.employeeId;
        const day = cell.dataset.day;
        const date = cell.dataset.date;

        console.log('🖱️ Clic sur cellule détecté:', { employeeId, day, date, cell });
        console.log('📍 Position du clic:', { x: event.clientX, y: event.clientY });

        if (!employeeId || !day || !date) {
            console.error('❌ Données manquantes sur la cellule:', { employeeId, day, date });
            return;
        }

        this.openTimeEditModal(employeeId, day, date, cell);
    }

    handleEditTimeClick(event, button) {
        const cell = button.closest('.schedule-cell');
        const employeeId = cell.dataset.employeeId;
        const day = cell.dataset.day;
        const date = cell.dataset.date;

        console.log('Clic sur bouton d\'édition:', { employeeId, day, date });

        // Ouvrir directement l'éditeur d'horaire
        this.openTimeEditModal(employeeId, day, date, cell);
    }

    openTimeEditModal(employeeId, day, date, cell) {
        console.log('🚀 Tentative d\'ouverture du modal pour:', { employeeId, day, date });
        
        // Vérifier si Bootstrap est disponible
        if (typeof bootstrap === 'undefined') {
            console.error('❌ Bootstrap n\'est pas chargé !');
            alert('Erreur: Bootstrap n\'est pas chargé. Veuillez recharger la page.');
            return;
        }
        console.log('✅ Bootstrap disponible:', bootstrap.Modal);
        
        // Récupérer les informations de l'employé depuis la cellule
        const employeeRow = cell.closest('.employee-row');
        const employeeName = employeeRow?.querySelector('.employee-name')?.textContent || 'Employé inconnu';
        const employeeRole = employeeRow?.querySelector('.employee-role')?.textContent || 'Rôle non défini';
        
        console.log('👤 Informations employé:', { employeeName, employeeRole });
        
        // Stocker les informations du contexte
        this.currentWorkShift = {
            employeeId: employeeId,
            day: day,
            date: date,
            employeeName: employeeName,
            employeeRole: employeeRole,
            cell: cell
        };
        
        // Mettre à jour les informations dans le modal
        this.updateModalContext();
        
        // Initialiser le formulaire
        this.initWorkShiftForm();
        
        // Vérifier et ouvrir le modal
        const modalElement = document.getElementById('timeEditModal');
        if (!modalElement) {
            console.error('❌ Modal timeEditModal non trouvé dans le DOM !');
            console.log('📋 Éléments modal disponibles:', document.querySelectorAll('[id*="modal"], [id*="Modal"]'));
            alert('Erreur: Modal non trouvé dans la page');
            return;
        }
        
        console.log('✅ Élément modal trouvé:', modalElement);
        
        try {
            const modal = new bootstrap.Modal(modalElement);
            console.log('🎭 Instance modal créée:', modal);
            modal.show();
            console.log('🎉 Modal affiché avec succès !');
        } catch (error) {
            console.error('❌ Erreur lors de l\'ouverture du modal:', error);
            alert('Erreur lors de l\'ouverture du modal: ' + error.message);
        }
    }

    updateModalContext() {
        const modalEmployeeInfo = document.getElementById('modal-employee-info');
        if (modalEmployeeInfo && this.currentWorkShift) {
            modalEmployeeInfo.innerHTML = `
                <div class="employee-name">
                    <i class="fas fa-user me-2"></i>
                    ${this.currentWorkShift.employeeName}
                </div>
                <div class="employee-details">
                    <strong>Rôle:</strong> ${this.currentWorkShift.employeeRole}<br>
                    <strong>Jour:</strong> ${this.currentWorkShift.day}<br>
                    <strong>Date:</strong> ${this.currentWorkShift.date}
                </div>
            `;
        }
    }

    initWorkShiftForm() {
        // Réinitialiser le formulaire
        const form = document.getElementById('workShiftForm');
        if (form) {
            form.reset();
            this.clearFormErrors();
        }

        // Initialiser les événements du formulaire
        this.bindFormEvents();
        
        // Charger les données existantes s'il y en a
        this.loadExistingShiftData();
    }

    bindFormEvents() {
        // Calculer automatiquement les durées
        const heureDebut = document.getElementById('heure_debut');
        const heureFin = document.getElementById('heure_fin');
        const pauseDuree = document.getElementById('pause_duree');
        const hasBreak = document.getElementById('has_break');
        
        if (heureDebut && heureFin && pauseDuree) {
            [heureDebut, heureFin, pauseDuree].forEach(input => {
                input.addEventListener('change', () => this.calculateDurations());
                input.addEventListener('input', () => this.calculateDurations());
            });
        }

        // Gestion de la checkbox pause
        if (hasBreak) {
            hasBreak.addEventListener('change', () => {
                this.togglePauseControls();
                this.calculateDurations();
            });
        }

        // Boutons +/- pour la durée de pause
        const btnDecrease = document.querySelector('.btn-pause-decrease');
        const btnIncrease = document.querySelector('.btn-pause-increase');
        
        if (btnDecrease && pauseDuree) {
            btnDecrease.addEventListener('click', () => {
                const currentValue = parseInt(pauseDuree.value) || 0;
                const newValue = Math.max(0, currentValue - 15);
                pauseDuree.value = newValue;
                this.calculateDurations();
            });
        }
        
        if (btnIncrease && pauseDuree) {
            btnIncrease.addEventListener('click', () => {
                const currentValue = parseInt(pauseDuree.value) || 0;
                const newValue = Math.min(120, currentValue + 15);
                pauseDuree.value = newValue;
                this.calculateDurations();
            });
        }

        // Boutons preset de pause
        const pausePresets = document.querySelectorAll('.pause-preset');
        pausePresets.forEach(btn => {
            btn.addEventListener('click', () => {
                const duration = btn.dataset.duration;
                if (pauseDuree) {
                    pauseDuree.value = duration;
                    this.calculateDurations();
                }
                
                // Mise à jour visuelle des presets
                pausePresets.forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // Compteur de caractères pour la note
        const noteField = document.getElementById('note');
        const noteCounter = document.getElementById('note-counter');
        
        if (noteField && noteCounter) {
            noteField.addEventListener('input', () => {
                noteCounter.textContent = noteField.value.length;
            });
        }

        // Bouton de sauvegarde
        const saveBtn = document.getElementById('saveWorkShiftBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveWorkShift());
        }

        // Validation en temps réel
        const formInputs = document.querySelectorAll('#workShiftForm input, #workShiftForm textarea');
        formInputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
        });
    }

    togglePauseControls() {
        const hasBreak = document.getElementById('has_break');
        const pauseControls = document.getElementById('pause-controls');
        const toggleText = document.querySelector('.toggle-text');
        
        if (hasBreak && pauseControls && toggleText) {
            if (hasBreak.checked) {
                pauseControls.style.display = 'block';
                toggleText.textContent = 'Pause activée';
                pauseControls.style.opacity = '1';
            } else {
                pauseControls.style.display = 'none';
                toggleText.textContent = 'Aucune pause';
                document.getElementById('pause_duree').value = '0';
            }
        }
    }

    calculateDurations() {
        const heureDebut = document.getElementById('heure_debut')?.value;
        const heureFin = document.getElementById('heure_fin')?.value;
        const hasBreak = document.getElementById('has_break')?.checked;
        const pauseDuree = hasBreak ? (parseInt(document.getElementById('pause_duree')?.value) || 0) : 0;
        
        if (!heureDebut || !heureFin) {
            const dureeTotale = document.getElementById('duree-totale');
            const dureeEffective = document.getElementById('duree-effective');
            if (dureeTotale) dureeTotale.textContent = '--';
            if (dureeEffective) dureeEffective.textContent = '--';
            return;
        }

        try {
            const debut = new Date(`2024-01-01T${heureDebut}`);
            const fin = new Date(`2024-01-01T${heureFin}`);
            
            if (fin <= debut) {
                throw new Error("L'heure de fin doit être après l'heure de début");
            }

            const dureeMs = fin - debut;
            const dureeMinutes = Math.floor(dureeMs / (1000 * 60));
            
            const heures = Math.floor(dureeMinutes / 60);
            const minutes = dureeMinutes % 60;
            const dureeFormatee = `${heures}h${minutes.toString().padStart(2, '0')}`;
            
            const dureeEffectiveMinutes = dureeMinutes - pauseDuree;
            const heuresEffectives = Math.floor(dureeEffectiveMinutes / 60);
            const minutesEffectives = dureeEffectiveMinutes % 60;
            const dureeEffectiveFormatee = `${heuresEffectives}h${minutesEffectives.toString().padStart(2, '0')}`;
            
            // Mise à jour des éléments d'affichage
            const dureeTotale = document.getElementById('duree-totale');
            const dureeEffective = document.getElementById('duree-effective');
            if (dureeTotale) dureeTotale.textContent = dureeFormatee;
            if (dureeEffective) dureeEffective.textContent = dureeEffectiveFormatee;
            
            // Mise à jour du temps de pause affiché
            const pauseMinutes = Math.floor(pauseDuree / 60);
            const pauseReste = pauseDuree % 60;
            const pauseTexte = pauseDuree > 0 ? 
                (pauseMinutes > 0 ? `${pauseMinutes}h${pauseReste.toString().padStart(2, '0')}` : `${pauseReste}min`) :
                'Aucune pause';
            const pauseDisplay = document.querySelector('.pause-duration-display');
            if (pauseDisplay) pauseDisplay.textContent = pauseTexte;
            
            // Mise à jour visuelle selon la durée
            const dureeCards = document.querySelectorAll('.duration-card');
            dureeCards.forEach(card => {
                card.classList.remove('duration-short', 'duration-normal', 'duration-long');
                if (dureeEffectiveMinutes < 240) {
                    card.classList.add('duration-short');
                } else if (dureeEffectiveMinutes > 480) {
                    card.classList.add('duration-long');
                } else {
                    card.classList.add('duration-normal');
                }
            });
            
        } catch (error) {
            console.error('Erreur calcul durée:', error);
            const dureeTotale = document.getElementById('duree-totale');
            const dureeEffective = document.getElementById('duree-effective');
            if (dureeTotale) dureeTotale.textContent = 'Erreur';
            if (dureeEffective) dureeEffective.textContent = 'Erreur';
        }
    }

    validateDurations(dureTotaleMinutes, dureeEffectiveMinutes) {
        const maxDureeMinutes = 12 * 60; // 12 heures
        const minDureeEffectiveMinutes = 60; // 1 heure
        
        let errors = [];
        
        if (dureTotaleMinutes > maxDureeMinutes) {
            errors.push('Un quart ne peut pas dépasser 12 heures.');
        }
        
        if (dureeEffectiveMinutes < minDureeEffectiveMinutes) {
            errors.push('La durée effective de travail doit être d\'au moins 1 heure.');
        }
        
        if (dureeEffectiveMinutes <= 0) {
            errors.push('La durée de pause ne peut pas être supérieure à la durée totale du quart.');
        }
        
        this.showFormErrors(errors);
    }

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';
        
        // Validation selon le type de champ
        switch (field.id) {
            case 'heure_debut':
            case 'heure_fin':
                if (!value) {
                    isValid = false;
                    errorMessage = 'Ce champ est obligatoire.';
                }
                break;
                
            case 'pause_duree':
                const pause = parseInt(value);
                if (value && (isNaN(pause) || pause < 0 || pause > 120)) {
                    isValid = false;
                    errorMessage = 'La pause doit être entre 0 et 120 minutes.';
                }
                break;
                
            case 'note':
                if (value.length > 500) {
                    isValid = false;
                    errorMessage = 'La note ne peut pas dépasser 500 caractères.';
                }
                break;
        }
        
        // Appliquer la validation visuelle
        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
            field.nextElementSibling.textContent = errorMessage;
        }
        
        return isValid;
    }

    showFormErrors(errors) {
        const errorContainer = document.getElementById('form-errors');
        const errorList = document.getElementById('error-list');
        
        if (errors.length > 0) {
            errorList.innerHTML = '';
            errors.forEach(error => {
                const li = document.createElement('li');
                li.textContent = error;
                errorList.appendChild(li);
            });
            errorContainer.classList.remove('d-none');
        } else {
            errorContainer.classList.add('d-none');
        }
    }

    clearFormErrors() {
        document.getElementById('form-errors').classList.add('d-none');
        document.querySelectorAll('#workShiftForm .form-control').forEach(field => {
            field.classList.remove('is-invalid', 'is-valid');
        });
    }

    loadExistingShiftData() {
        // Ici on peut charger les données existantes du quart depuis le localStorage
        // ou d'une autre source temporaire
        const existingData = this.getStoredShiftData();
        if (existingData) {
            document.getElementById('heure_debut').value = existingData.heure_debut || '';
            document.getElementById('heure_fin').value = existingData.heure_fin || '';
            document.getElementById('pause_duree').value = existingData.pause_duree || 30;
            document.getElementById('note').value = existingData.note || '';
            
            this.calculateDurations();
        }
    }

    getStoredShiftData() {
        if (!this.currentWorkShift) return null;
        
        const key = `shift_${this.currentWorkShift.employeeId}_${this.currentWorkShift.date}`;
        const stored = localStorage.getItem(key);
        return stored ? JSON.parse(stored) : null;
    }

    saveWorkShift() {
        console.log('Sauvegarde du quart de travail...');
        
        // Valider le formulaire
        if (!this.validateForm()) {
            return;
        }
        
        // Récupérer les données du formulaire
        const formData = {
            employee_id: this.currentWorkShift.employeeId,
            employee_name: this.currentWorkShift.employeeName,
            date: this.currentWorkShift.date,
            day: this.currentWorkShift.day,
            heure_debut: document.getElementById('heure_debut').value,
            heure_fin: document.getElementById('heure_fin').value,
            pause_duree: parseInt(document.getElementById('pause_duree').value) || 0,
            note: document.getElementById('note').value.trim(),
            timestamp: new Date().toISOString()
        };
        
        // Stocker temporairement en localStorage
        const key = `shift_${formData.employee_id}_${formData.date}`;
        localStorage.setItem(key, JSON.stringify(formData));
        
        // Mettre à jour l'affichage dans la cellule
        this.updateCellDisplay(formData);
        
        // Fermer le modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('timeEditModal'));
        modal.hide();
        
        // Afficher un message de succès
        this.showSuccessMessage('Quart de travail enregistré avec succès !');
        
        console.log('Données sauvegardées:', formData);
    }

    validateForm() {
        const form = document.getElementById('workShiftForm');
        const inputs = form.querySelectorAll('input[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });
        
        // Validation des durées
        const heureDebut = document.getElementById('heure_debut').value;
        const heureFin = document.getElementById('heure_fin').value;
        
        if (heureDebut && heureFin) {
            const [debutH, debutM] = heureDebut.split(':').map(Number);
            const [finH, finM] = heureFin.split(':').map(Number);
            
            let debutMinutes = debutH * 60 + debutM;
            let finMinutes = finH * 60 + finM;
            
            if (finMinutes <= debutMinutes) {
                finMinutes += 24 * 60;
            }
            
            const dureTotaleMinutes = finMinutes - debutMinutes;
            const pauseDuree = parseInt(document.getElementById('pause_duree').value) || 0;
            const dureeEffectiveMinutes = dureTotaleMinutes - pauseDuree;
            
            this.validateDurations(dureTotaleMinutes, dureeEffectiveMinutes);
            
            if (dureTotaleMinutes > 12 * 60 || dureeEffectiveMinutes < 60 || dureeEffectiveMinutes <= 0) {
                isValid = false;
            }
        }
        
        return isValid;
    }

    updateCellDisplay(shiftData) {
        if (!this.currentWorkShift || !this.currentWorkShift.cell) return;
        
        const cell = this.currentWorkShift.cell;
        const timeSlot = cell.querySelector('.time-slot');
        
        if (timeSlot) {
            const timeDisplay = timeSlot.querySelector('.time-display');
            if (timeDisplay) {
                timeDisplay.textContent = `${shiftData.heure_debut} - ${shiftData.heure_fin}`;
            }
            
            // Ajouter une classe pour indiquer qu'il y a des données
            cell.classList.add('has-shift');
            
            // Ajouter un tooltip avec les détails
            cell.title = `${shiftData.heure_debut} - ${shiftData.heure_fin}`;
            if (shiftData.pause_duree > 0) {
                cell.title += `\nPause: ${shiftData.pause_duree} min`;
            }
            if (shiftData.note) {
                cell.title += `\nNote: ${shiftData.note}`;
            }
        }
    }

    showSuccessMessage(message) {
        // Créer un toast de succès
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-bg-success border-0 position-fixed';
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-check-circle me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Supprimer le toast après fermeture
        toast.addEventListener('hidden.bs.toast', () => {
            document.body.removeChild(toast);
        });
    }

    changeWeek(direction) {
        this.currentWeekOffset += direction;
        this.loadWeekData();
    }

    loadWeekData() {
        console.log('Chargement des données pour la semaine avec offset:', this.currentWeekOffset);

        // Calculer la nouvelle date de début de semaine
        const today = new Date();
        const startDate = new Date(today);
        startDate.setDate(today.getDate() + (this.currentWeekOffset * 7));

        // Obtenir le lundi de cette semaine (0=dimanche, 1=lundi, etc.)
        const dayOfWeek = startDate.getDay();
        const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // Si dimanche (0), aller 6 jours en arrière

        const mondayDate = new Date(startDate);
        mondayDate.setDate(startDate.getDate() + mondayOffset);

        console.log('Date du lundi calculée:', mondayDate.toLocaleDateString('fr-FR'));

        // Générer les nouveaux jours de la semaine
        const newWeekDays = this.generateWeekDays(mondayDate);

        console.log('Nouveaux jours générés:', newWeekDays);

        // Mettre à jour l'affichage
        this.updateWeekDisplay(newWeekDays);
        this.updateGridHeaders(newWeekDays);
    }

    generateWeekDays(startDate) {
        const jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
        const weekDays = [];

        for (let i = 0; i < 7; i++) {
            const currentDate = new Date(startDate);
            currentDate.setDate(startDate.getDate() + i);

            weekDays.push({
                jour_name: jours[i],
                date_short: currentDate.toLocaleDateString('fr-FR', {
                    day: '2-digit',
                    month: '2-digit'
                }),
                date_formatted: currentDate.toLocaleDateString('fr-FR', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric'
                }),
                date: currentDate
            });
        }

        return weekDays;
    }

    updateWeekDisplay(weekDays = this.weekDays) {
        const weekDisplayElement = document.getElementById('current-week-display');
        console.log('updateWeekDisplay appelée avec:', { weekDays, element: weekDisplayElement });

        if (weekDisplayElement && weekDays && weekDays.length >= 7) {
            // Vérifier quelles propriétés sont disponibles dans le premier élément
            console.log('Premier jour de la semaine:', weekDays[0]);
            console.log('Dernier jour de la semaine:', weekDays[6]);

            // Essayer différentes propriétés pour obtenir la date formatée
            let startDate, endDate;

            if (weekDays[0].date_formatted && weekDays[6].date_formatted) {
                startDate = weekDays[0].date_formatted;
                endDate = weekDays[6].date_formatted;
            } else if (weekDays[0].date_short && weekDays[6].date_short) {
                // Ajouter l'année si on n'a que le format court
                const currentYear = new Date().getFullYear();
                startDate = weekDays[0].date_short + `/${currentYear}`;
                endDate = weekDays[6].date_short + `/${currentYear}`;
            } else {
                console.error('Format de date non reconnu dans les données');
                return;
            }

            console.log('Mise à jour de l\'affichage de la semaine:', startDate, '-', endDate);
            weekDisplayElement.textContent = `${startDate} - ${endDate}`;
        } else {
            console.error('Impossible de mettre à jour l\'affichage de la semaine', {
                weekDisplayElement: !!weekDisplayElement,
                weekDays: weekDays,
                weekDaysLength: weekDays ? weekDays.length : 'undefined'
            });
        }
    }

    updateGridHeaders(weekDays) {
        const dayHeaders = document.querySelectorAll('.day-header');

        weekDays.forEach((day, index) => {
            if (dayHeaders[index]) {
                const dayName = dayHeaders[index].querySelector('.day-name');
                const dayDate = dayHeaders[index].querySelector('.day-date');

                if (dayName) dayName.textContent = day.jour_name;
                if (dayDate) dayDate.textContent = day.date_short;
            }
        });
    }
}

// Initialiser le gestionnaire d'horaires quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM chargé, initialisation des horaires...');

    const pageElement = document.querySelector('.page-creation-horaire');
    if (!pageElement) {
        console.log('Page de création d\'horaires non détectée');
        return;
    }

    console.log('Initialisation du gestionnaire d\'horaires...');
    const manager = new HoraireManager();
    
    // Attacher les événements aux cellules
    manager.bindScheduleCellEvents();
});

// Fonction utilitaire pour formater les dates
function formatDate(date, format = 'short') {
    const options = {
        short: { day: '2-digit', month: '2-digit' },
        long: { day: '2-digit', month: '2-digit', year: 'numeric' },
        full: { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' }
    };

    return date.toLocaleDateString('fr-FR', options[format] || options.short);
}
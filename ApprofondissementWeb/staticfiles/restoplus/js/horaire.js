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
        // Navigation de semaine - Utiliser les IDs pour une sélection plus précise
        const prevWeekBtn = document.getElementById('prev-week-btn');
        const nextWeekBtn = document.getElementById('next-week-btn');

        console.log('Boutons trouvés:', { prevWeekBtn, nextWeekBtn });

        if (prevWeekBtn) {
            prevWeekBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Clic sur semaine précédente');
                this.changeWeek(-1);
            });
        } else {
            console.error('Bouton semaine précédente non trouvé');
        }

        if (nextWeekBtn) {
            nextWeekBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Clic sur semaine suivante');
                this.changeWeek(1);
            });
        } else {
            console.error('Bouton semaine suivante non trouvé');
        }

        // Ajouter les événements pour les cellules d'horaire
        this.bindScheduleCellEvents();
    }

    bindScheduleCellEvents() {
        // Gérer les clics sur les cellules d'horaire
        const scheduleCells = document.querySelectorAll('.schedule-cell');
        scheduleCells.forEach(cell => {
            cell.addEventListener('click', (e) => {
                this.handleScheduleCellClick(e, cell);
            });
        });

        // Gérer les clics sur les boutons d'édition
        const editButtons = document.querySelectorAll('.edit-time-btn');
        editButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation(); // Empêcher le déclenchement du clic sur la cellule
                this.handleEditTimeClick(e, btn);
            });
        });
    }

    handleScheduleCellClick(event, cell) {
        const employeeId = cell.dataset.employeeId;
        const day = cell.dataset.day;
        const date = cell.dataset.date;

        console.log('Clic sur cellule:', { employeeId, day, date });

        // Ici vous pouvez ajouter la logique pour ouvrir un modal d'édition d'horaire
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
        // Pour l'instant, on va simplement simuler l'ajout d'un horaire
        const currentTime = cell.querySelector('.time-display');

        if (currentTime.textContent === '-') {
            // Ajouter un horaire d'exemple
            const startTime = '09:00';
            const endTime = '17:00';
            currentTime.textContent = `${startTime}-${endTime}`;
            cell.classList.add('has-schedule');
            console.log(`Horaire ajouté: ${startTime}-${endTime} pour l'employé ${employeeId} le ${day}`);
        } else {
            // Enlever l'horaire
            cell.classList.remove('has-schedule');
            console.log(`Horaire supprimé pour l'employé ${employeeId} le ${day}`);
        }

        // Ici vous pourrez ajouter plus tard la logique pour ouvrir un vrai modal
        // avec des champs de saisie pour l'heure de début et de fin
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
    console.log('DOM chargé, vérification de la page...');

    const pageElement = document.querySelector('.page-creation-horaire');
    const weekDaysElement = document.getElementById('week-days-data');
    const weekDisplayElement = document.getElementById('current-week-display');

    console.log('Éléments trouvés:', {
        pageElement: !!pageElement,
        weekDaysElement: !!weekDaysElement,
        weekDisplayElement: !!weekDisplayElement,
        weekDaysContent: weekDaysElement ? weekDaysElement.textContent : 'non trouvé'
    });

    if (pageElement) {
        console.log('Initialisation du gestionnaire d\'horaires...');
        new HoraireManager();
    } else {
        console.log('Page de création d\'horaires non détectée');
    }
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
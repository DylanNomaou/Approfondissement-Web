/**
 * Gestionnaire d'horaires pour la planification des employés
 * Gère la navigation hebdomadaire, l'édition des quarts de travail et la validation
 */




class HoraireManager {
    constructor() {
        this.currentWeekOffset = 0;
        this.currentWorkShift = null;
        this.weekDays = this.loadWeekDays();
        this.canEditWeek = this.getCanEditWeekFlag();
        // Charger l'état de publication de la semaine
        // Initialiser avec un tableau vide par défaut
        this.availabilities = [];

        // Charger les disponibilités de manière sécurisée
        try {
            this.availabilities = this.loadAvailabilities();
        } catch (error) {
            console.error("❌ Erreur lors du chargement des disponibilités:", error);
            this.availabilities = [];
        }

        console.log("🚀 Availabilities finales:", this.availabilities);
        this.init();
    }

    // ==========================================
    // INITIALISATION
    // ==========================================

    /**
     * Charge les données de la semaine depuis Django ou génère des données par défaut
     */
    loadWeekDays() {
        const weekDaysElement = document.getElementById("week-days-data");

        if (weekDaysElement?.textContent) {
            try {
                const data = JSON.parse(weekDaysElement.textContent);
                console.log("✅ Données de la semaine chargées depuis Django");
                return data;
            } catch (error) {
                console.error("❌ Erreur lors du parsing JSON:", error);
            }
        }

        console.warn("⚠️ Génération de données par défaut");
        return this.generateDefaultWeekDays();
    }

    /**
     * Charge les données de disponibilité depuis Django
     */
    loadAvailabilities() {
        const availabilityElement = document.getElementById("availability-data");
        console.log("🔍 Élément availability-data:", availabilityElement);

        if (availabilityElement?.textContent) {
            console.log("📄 Contenu brut:", availabilityElement.textContent);
            console.log("📄 Longueur:", availabilityElement.textContent.length);

            try {
                const data = JSON.parse(availabilityElement.textContent);
                console.log(
                    "✅ Données de disponibilité chargées depuis Django:",
                    data
                );
                console.log("🔍 Type des données:", typeof data, Array.isArray(data));
                console.log("🔍 Longueur:", data?.length);

                // S'assurer que c'est un tableau
                if (Array.isArray(data)) {
                    console.log("✅ C'est bien un tableau avec", data.length, "éléments");
                    return data;
                } else {
                    console.warn(
                        "⚠️ Les données de disponibilité ne sont pas un tableau, conversion..."
                    );
                    console.log("🔍 Type reçu:", typeof data);
                    console.log("🔍 Contenu:", data);

                    // Essayer de convertir en tableau si c'est un objet
                    if (typeof data === "object" && data !== null) {
                        const converted = Object.values(data);
                        console.log("🔄 Tentative de conversion:", converted);
                        return Array.isArray(converted) ? converted : [];
                    }

                    return [];
                }
            } catch (error) {
                console.error("❌ Erreur lors du parsing JSON disponibilités:", error);
                console.error(
                    "📄 Contenu qui a causé l'erreur:",
                    availabilityElement.textContent
                );
            }
        } else {
            console.warn("⚠️ Élément availability-data non trouvé ou vide");
            if (!availabilityElement) {
                console.error("❌ Élément availability-data n'existe pas dans le DOM");
            } else {
                console.error("❌ Élément availability-data existe mais est vide");
            }
        }

        console.warn("⚠️ Retour d'un tableau vide par défaut");
        return [];
    }

    /**
     * Génère les jours de la semaine par défaut (semaine courante)
     */
    generateDefaultWeekDays() {
        const today = new Date();
        const monday = this.getMondayOfWeek(today);
        return this.generateWeekDays(monday);
    }

    /**
     * Indique si on peut modifier la semaine actuelle
     * @returns Booléen indiquant si l'édition est permise
     */

    getCanEditWeekFlag() {
        const el = document.getElementById("can-edit-data");
        if (!el?.textContent) return true; // par défaut on autorise (mode brouillon)
        try {
            return JSON.parse(el.textContent.trim()) === true;
        } catch {
            return true;
        }
    }

    /**
     * Initialise le gestionnaire
     */
    init() {
        this.bindNavigationEvents();
        this.bindScheduleCellEvents();
        this.bindPublishButton(); // Nouveau : bouton publier
        this.updateWeekDisplay();
        this.updateAvailabilityIndicators();
        this.loadExistingShiftsFromStorage(); // Charger les shifts existants au démarrage

        if (!this.canEditWeek) {
            document.querySelectorAll(".delete-shift-btn").forEach((b) => b.remove());
            // désactive aussi le clic ouverture modal si jamais bindé avant (sécurité)
            document.querySelectorAll(".schedule-cell").forEach((cell) => {
                cell.style.pointerEvents = "auto"; // on laisse les tooltips
            });
        }

    }

    // ==========================================
    // GESTION DES ÉVÉNEMENTS
    // ==========================================

    /**
     * Attache les événements de navigation (boutons semaine précédente/suivante)
     */
    bindNavigationEvents() {
        const prevBtn = document.getElementById("prev-week-btn");
        const nextBtn = document.getElementById("next-week-btn");

        if (prevBtn) {
            prevBtn.addEventListener("click", (e) => {
                e.preventDefault();
                this.changeWeek(-1);
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener("click", (e) => {
                e.preventDefault();
                this.changeWeek(1);
            });
        }
    }

    /**
     * Attache l'événement du bouton publier
     */
    bindPublishButton() {
        const publishBtn = document.getElementById("publishScheduleBtn");
        if (!publishBtn) return;
        if (!this.canEditWeek) {
            publishBtn.disabled = true;
            publishBtn.title = "Cette semaine ne peut plus être modifiée";
            return;
        }
        publishBtn.addEventListener("click", (e) => {
            e.preventDefault();
            this.publishSchedule();
        });
    }

    /**
     * Attache les événements aux cellules d'horaire
     */
    bindScheduleCellEvents() {
        const scheduleCells = document.querySelectorAll(".schedule-cell");

        scheduleCells.forEach((cell) => {
            if (!this.canEditWeek) {
                // lecture seule : pas de curseur main, pas d’événements
                cell.style.cursor = "default";
                cell.title = cell.title || "Lecture seule";
                return;
            }
            cell.style.cursor = "pointer";
            cell.title = "Cliquer pour définir les horaires";

            cell.addEventListener("click", (e) => {
                if (e.target.closest(".edit-time-btn")) return;
                this.handleScheduleCellClick(cell);
            });
        });

        // Boutons d’édition spécifiques
        if (!this.canEditWeek) return; // rien à binder en lecture seule
        document.querySelectorAll(".edit-time-btn").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const cell = btn.closest(".schedule-cell");
                this.handleScheduleCellClick(cell);
            });
        });
    }

    /**
     * Gère le clic sur une cellule d'horaire
     */
    handleScheduleCellClick(cell) {
        const { employeeId, day, date } = cell.dataset;

        console.log("Clic sur cellule:", { employeeId, day, date });

        if (!employeeId || !day || !date) {
            console.error("❌ Données manquantes sur la cellule");
            return;
        }

        // Récupérer la disponibilité pour l'afficher dans le modal
        const availability = this.checkEmployeeAvailability(employeeId, day);
        console.log("Disponibilité trouvée:", availability);

        // TOUJOURS ouvrir le modal pour afficher les infos
        console.log("� Ouverture directe du modal");
        this.openTimeEditModal(employeeId, day, date, cell, availability);
    }

    // ==========================================
    // GESTION DES DISPONIBILITÉS
    // ==========================================

    /**
     * Vérifie si un employé est disponible pour un jour donné
     */
    checkEmployeeAvailability(employeeId, day) {
        console.log(" Recherche disponibilité pour:", { employeeId, day });
        console.log(" Disponibilités chargées:", this.availabilities);
        console.log(
            "🔍 Type et longueur:",
            typeof this.availabilities,
            Array.isArray(this.availabilities),
            this.availabilities?.length
        );

        // Vérifier que this.availabilities est un tableau
        if (!this.availabilities || !Array.isArray(this.availabilities)) {
            console.error(
                "❌ this.availabilities n'est pas un tableau:",
                this.availabilities
            );
            console.log("🔧 Tentative de réinitialisation...");
            this.availabilities = [];
            return null;
        }

        if (this.availabilities.length === 0) {
            console.warn("⚠️ Aucune disponibilité chargée");
            return null;
        }

        // Mapping des jours français vers les jours anglais du modèle
        const dayMapping = {
            Lundi: "monday",
            Mardi: "tuesday",
            Mercredi: "wednesday",
            Jeudi: "thursday",
            Vendredi: "friday",
            Samedi: "saturday",
            Dimanche: "sunday",
        };

        const mappedDay = dayMapping[day] || day.toLowerCase();
        console.log("Jour mappé:", { original: day, mapped: mappedDay });

        try {
            const availability = this.availabilities.find((avail) => {
                if (!avail) return false;

                const match =
                    avail.employe_id == employeeId &&
                    avail.day === mappedDay &&
                    !avail.remplie;
                console.log("Test disponibilité:", {
                    avail,
                    employeeMatch: avail.employe_id == employeeId,
                    dayMatch: avail.day === mappedDay,
                    notFilled: !avail.remplie,
                    overallMatch: match,
                });
                return match;
            });

            console.log("Résultat final:", availability);
            return availability;
        } catch (error) {
            console.error(" Erreur lors de la recherche:", error);
            return null;
        }
    }

    /**
     * Valide si un horaire proposé respecte les disponibilités
     */
    validateScheduleTime(employeeId, day, startTime, endTime) {
        const availability = this.checkEmployeeAvailability(employeeId, day);

        if (!availability) {
            return {
                valid: false,
                message: "Aucune disponibilité définie pour ce jour (weekend ?)",
            };
        }

        // Vérifier si l'horaire proposé rentre dans les créneaux de disponibilité
        if (
            startTime < availability.heure_debut ||
            endTime > availability.heure_fin
        ) {
            return {
                valid: false,
                message: `L'employé est disponible de ${availability.heure_debut} à ${availability.heure_fin}`,
            };
        }

        return { valid: true };
    }

    // ==========================================
    // GESTION DU MODAL
    // ==========================================

    /**
     * Ouvre le modal d'édition d'horaire
     */
    openTimeEditModal(employeeId, day, date, cell, availability = null) {
        // Vérifier Bootstrap
        if (typeof bootstrap === "undefined") {
            console.error("Bootstrap non disponible");
            alert("Erreur: Bootstrap n'est pas chargé. Rechargez la page.");
            return;
        }

        // Récupérer les infos de l'employé
        const employeeRow = cell.closest(".employee-row");
        const employeeName =
            employeeRow?.querySelector(".employee-name")?.textContent ||
            "Employé inconnu";
        const employeeRole =
            employeeRow?.querySelector(".employee-role")?.textContent ||
            "Rôle non défini";

        // Stocker le contexte
        this.currentWorkShift = {
            employeeId,
            day,
            date,
            employeeName,
            employeeRole,
            cell,
            availability,
        };

        // Préparer et ouvrir le modal
        this.updateModalContext();
        this.initWorkShiftForm();
        this.showModal();
    }

    /**
     * Met à jour les informations de contexte dans le modal
     */
    updateModalContext() {
        const modalInfo = document.getElementById("modal-employee-info");
        if (!modalInfo || !this.currentWorkShift) return;

        const { employeeName, employeeRole, day, date, availability } =
            this.currentWorkShift;

        let availabilityInfo = "";
        if (availability) {
            availabilityInfo = `<div class="availability-info mt-2 p-3 bg-success bg-opacity-10 rounded">
        <i class="fas fa-check-circle me-2 text-success"></i>
        <strong class="text-success"> Disponible ce jour:</strong><br>
        <span class="fw-bold fs-5">${availability.heure_debut} - ${availability.heure_fin}</span>
        <small class="d-block text-muted mt-1">Vous pouvez programmer un shift dans ces heures</small>
      </div>`;
        } else {
            availabilityInfo = `<div class="availability-info mt-2 p-3 bg-warning bg-opacity-10 border border-warning rounded">
        <i class="fas fa-exclamation-triangle me-2 text-warning"></i>
        <strong class="text-warning"> Pas de disponibilité définie</strong><br>
        <small class="text-muted">Vous pouvez programmer un shift, mais il sera hors des heures habituelles</small>
      </div>`;
        }

        modalInfo.innerHTML = `
      <div class="employee-name mb-2">
        <i class="fas fa-user me-2"></i>
        <strong>${employeeName}</strong>
      </div>
      <div class="employee-details mb-3">
        <div><strong>Rôle:</strong> ${employeeRole}</div>
        <div><strong>Jour:</strong> ${day}</div>
        <div><strong>Date:</strong> ${date}</div>
      </div>
      ${availabilityInfo}
    `;
    }

    /**
     * Affiche le modal Bootstrap
     */
    showModal() {
        const modalElement = document.getElementById("timeEditModal");

        if (!modalElement) {
            console.error("Modal introuvable");
            alert("Erreur: Modal introuvable");
            return;
        }

        try {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            console.log("Modal affiché");
        } catch (error) {
            console.error("Erreur ouverture modal:", error);
            alert("Erreur lors de l'ouverture: " + error.message);
        }
    }

    // ==========================================
    // GESTION DU FORMULAIRE
    // ==========================================

    /**
     * Initialise le formulaire d'édition d'horaire
     */
    initWorkShiftForm() {
        console.log("🎛️ Initialisation du formulaire...");

        const form = document.getElementById("workShiftForm");
        if (form) {
            form.reset();
            this.clearFormErrors();
        }

        this.bindFormEvents();
        this.loadExistingShiftData();
        // Affiche le bouton supprimer si un shift existe pour ce créneau
        this.showDeleteButtonIfNeeded();
        this.setDefaultTimesFromAvailability();

        // Calcul initial des durées
        setTimeout(() => {
            console.log("Calcul initial des durées...");
            this.calculateDurations();
        }, 100);
    }

    /**
     * Définit les heures par défaut selon la disponibilité de l'employé
     */
    setDefaultTimesFromAvailability() {
        if (!this.currentWorkShift?.availability) return;

        const { availability } = this.currentWorkShift;
        const heureDebutInput = document.getElementById("heure_debut");
        const heureFinInput = document.getElementById("heure_fin");

        // Si pas d'horaires existants, utiliser la disponibilité
        if (heureDebutInput && !heureDebutInput.value) {
            heureDebutInput.value = availability.heure_debut;
        }

        if (heureFinInput && !heureFinInput.value) {
            heureFinInput.value = availability.heure_fin;
        }

        console.log(
            ` Heures par défaut définies: ${availability.heure_debut} - ${availability.heure_fin}`
        );
    }

    /**
     * Attache les événements du formulaire
     */
    bindFormEvents() {
        // Calcul automatique des durées seulement
        ["heure_debut", "heure_fin", "pause_duree"].forEach((id) => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener("change", () => this.calculateDurations());
                input.addEventListener("input", () => this.calculateDurations());
            }
        });

        // Checkbox pause
        const hasBreak = document.getElementById("has_break");
        if (hasBreak) {
            hasBreak.addEventListener("change", () => {
                this.togglePauseControls();
                this.calculateDurations();
            });
        }

        // Boutons +/- pour la pause
        this.bindPauseControls();

        // Boutons preset de pause
        this.bindPausePresets();

        // Compteur de caractères pour la note
        this.bindNoteCounter();

        // Bouton de sauvegarde
        const saveBtn = document.getElementById("saveWorkShiftBtn");
        if (saveBtn) {
            saveBtn.addEventListener("click", () => this.saveWorkShift());
        }

        // Bouton supprimer
        const deleteBtn = document.getElementById("deleteWorkShiftBtn");
        if (deleteBtn) {
            deleteBtn.addEventListener("click", (e) => {
                e.preventDefault();
                this.confirmAndDeleteShift();
            });
        }

        // Validation temps réel
        const inputs = document.querySelectorAll(
            "#workShiftForm input, #workShiftForm textarea"
        );
        inputs.forEach((input) => {
            input.addEventListener("blur", () => this.validateField(input));
        });

        console.log("Événements du formulaire attachés");
    }

    /**
     * Valide les heures en temps réel et affiche des alertes visuelles
     */
    validateTimeInput() {
        if (!this.currentWorkShift) return;

        const heureDebutInput = document.getElementById("heure_debut");
        const heureFinInput = document.getElementById("heure_fin");
        const availability = this.currentWorkShift.availability;

        if (!heureDebutInput || !heureFinInput) return;

        const heureDebut = heureDebutInput.value;
        const heureFin = heureFinInput.value;

        // Nettoyer les messages précédents
        this.clearTimeWarnings();

        if (heureDebut && heureFin && availability) {
            // Vérifier si les heures sont dans les créneaux de disponibilité
            const isStartTimeValid = heureDebut >= availability.heure_debut;
            const isEndTimeValid = heureFin <= availability.heure_fin;

            if (!isStartTimeValid || !isEndTimeValid) {
                this.showTimeWarning(
                    `Attention: L'employé est disponible de ${availability.heure_debut} à ${availability.heure_fin}`
                );
            }
        } else if (heureDebut && heureFin && !availability) {
            this.showTimeWarning(
                `ℹInfo: Aucune disponibilité définie pour ce jour. Le shift sera programmé en dehors des heures habituelles.`
            );
        }
    }

    /**
     * Affiche un avertissement pour les heures
     */
    showTimeWarning(message) {
        let warningDiv = document.getElementById("time-warning");

        if (!warningDiv) {
            warningDiv = document.createElement("div");
            warningDiv.id = "time-warning";
            warningDiv.className = "alert alert-warning mt-2 mb-0 py-2";

            // Insérer après les champs d'heure
            const heureFinInput = document.getElementById("heure_fin");
            if (heureFinInput && heureFinInput.parentNode) {
                heureFinInput.parentNode.insertBefore(
                    warningDiv,
                    heureFinInput.nextSibling
                );
            }
        }

        warningDiv.innerHTML = `<small><i class="fas fa-exclamation-triangle me-1"></i>${message}</small>`;
        warningDiv.style.display = "block";
    }

    /**
     * Supprime les avertissements d'heure
     */
    clearTimeWarnings() {
        const warningDiv = document.getElementById("time-warning");
        if (warningDiv) {
            warningDiv.style.display = "none";
        }
    }

    /**
     * Attache les boutons +/- pour la durée de pause
     */
    bindPauseControls() {
        const pauseInput = document.getElementById("pause_duree");
        const btnDecrease = document.querySelector(".btn-pause-decrease");
        const btnIncrease = document.querySelector(".btn-pause-increase");

        if (btnDecrease && pauseInput) {
            btnDecrease.addEventListener("click", () => {
                const current = parseInt(pauseInput.value) || 0;
                pauseInput.value = Math.max(0, current - 15);
                this.calculateDurations();
            });
        }

        if (btnIncrease && pauseInput) {
            btnIncrease.addEventListener("click", () => {
                const current = parseInt(pauseInput.value) || 0;
                pauseInput.value = Math.min(120, current + 15);
                this.calculateDurations();
            });
        }
    }

    /**
     * Attache les boutons preset de pause (15min, 30min, etc.)
     */
    bindPausePresets() {
        const pauseInput = document.getElementById("pause_duree");
        const presets = document.querySelectorAll(".pause-preset");

        presets.forEach((btn) => {
            btn.addEventListener("click", () => {
                if (pauseInput) {
                    pauseInput.value = btn.dataset.duration;
                    this.calculateDurations();
                }

                // Mise à jour visuelle
                presets.forEach((p) => p.classList.remove("active"));
                btn.classList.add("active");
            });
        });
    }

    /**
     * Attache le compteur de caractères pour la note
     */
    bindNoteCounter() {
        const noteField = document.getElementById("note");
        const noteCounter = document.getElementById("note-counter");

        if (noteField && noteCounter) {
            noteField.addEventListener("input", () => {
                noteCounter.textContent = noteField.value.length;
            });
        }
    }

    /**
     * Affiche/masque les contrôles de pause
     */
    togglePauseControls() {
        const hasBreak = document.getElementById("has_break");
        const pauseControls = document.getElementById("pause-controls");
        const toggleText = document.querySelector(".toggle-text");
        const pauseInput = document.getElementById("pause_duree");

        if (!hasBreak || !pauseControls) return;

        if (hasBreak.checked) {
            pauseControls.style.display = "block";
            pauseControls.style.opacity = "1";
            if (toggleText) toggleText.textContent = "Pause activée";
        } else {
            pauseControls.style.display = "none";
            if (toggleText) toggleText.textContent = "Aucune pause";
            if (pauseInput) pauseInput.value = "0";
        }
    }

    // ==========================================
    // CALCULS ET VALIDATION
    // ==========================================

    /**
     * Calcule les durées totale et effective du quart
     */
    calculateDurations() {
        console.log("Calcul des durées...");

        const start = document.getElementById("heure_debut")?.value;
        const end = document.getElementById("heure_fin")?.value;
        const hasBreak = document.getElementById("has_break")?.checked;
        const pauseDuree = hasBreak
            ? parseInt(document.getElementById("pause_duree")?.value) || 0
            : 0;

        console.log("Valeurs récupérées:", {
            start,
            end,
            hasBreak,
            pauseDuree,
        });

        const outTotale = document.getElementById("duree-totale");
        const outEffective = document.getElementById("duree-effective");
        const outPause = document.getElementById("pause-display");

        console.log("Éléments DOM trouvés:", {
            outTotale: !!outTotale,
            outEffective: !!outEffective,
            outPause: !!outPause,
        });

        // Si les heures ne sont pas complètes
        if (!start || !end) {
            console.log(" Heures incomplètes");
            this.updateDurationDisplay(
                outTotale,
                outEffective,
                outPause,
                "--",
                "--",
                hasBreak ? "0min" : "Aucune pause"
            );
            return;
        }

        // Parser les heures
        const startMinutes = this.timeToMinutes(start);
        const endMinutes = this.timeToMinutes(end);

        console.log("Minutes calculées:", {
            startMinutes,
            endMinutes,
        });

        // Validation: fin doit être après début
        if (endMinutes <= startMinutes) {
            console.log(" Heure de fin <= heure de début");
            this.updateDurationDisplay(
                outTotale,
                outEffective,
                outPause,
                "Erreur",
                "Erreur",
                hasBreak ? `${pauseDuree}min` : "Aucune pause"
            );
            return;
        }

        // Calculs
        const totalMinutes = endMinutes - startMinutes;
        const effectiveMinutes = Math.max(0, totalMinutes - pauseDuree);

        // Formatage
        const totalFormatted = this.formatDuration(totalMinutes);
        const effectiveFormatted = this.formatDuration(effectiveMinutes);
        const pauseFormatted =
            pauseDuree > 0 ? this.formatDuration(pauseDuree) : "Aucune pause";

        console.log("📋 Durées calculées:", {
            totalMinutes,
            effectiveMinutes,
            pauseDuree,
            totalFormatted,
            effectiveFormatted,
            pauseFormatted,
        });

        this.updateDurationDisplay(
            outTotale,
            outEffective,
            outPause,
            totalFormatted,
            effectiveFormatted,
            pauseFormatted
        );
        this.updateDurationCardStyles(effectiveMinutes);
    }

    /**
     * Met à jour l'affichage des durées
     */
    updateDurationDisplay(
        outTotale,
        outEffective,
        outPause,
        total,
        effective,
        pause
    ) {
        if (outTotale) outTotale.textContent = total;
        if (outEffective) outEffective.textContent = effective;
        if (outPause) outPause.textContent = pause;
    }

    /**
     * Met à jour les styles visuels selon la durée effective
     */
    updateDurationCardStyles(effectiveMinutes) {
        const cards = document.querySelectorAll(".duration-card");
        cards.forEach((card) => {
            card.classList.remove(
                "duration-short",
                "duration-normal",
                "duration-long"
            );

            if (effectiveMinutes < 240) {
                card.classList.add("duration-short");
            } else if (effectiveMinutes > 480) {
                card.classList.add("duration-long");
            } else {
                card.classList.add("duration-normal");
            }
        });
    }

    /**
     * Valide un champ spécifique du formulaire
     */
    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = "";

        switch (field.id) {
            case "heure_debut":
            case "heure_fin":
                if (!value) {
                    isValid = false;
                    errorMessage = "Ce champ est obligatoire.";
                } else if (!/^\d{2}:\d{2}$/.test(value)) {
                    isValid = false;
                    errorMessage = "Le format doit être HH:MM.";
                } else if (field.id === "heure_fin") {
                    const start = document.getElementById("heure_debut").value;
                    if (start && this.timeToMinutes(value) <= this.timeToMinutes(start)) {
                        isValid = false;
                        errorMessage = "L'heure de fin doit être après l'heure de début.";
                    }
                }
                break;

            case "pause_duree":
                const pause = parseInt(value);
                if (value && (isNaN(pause) || pause < 0 || pause > 120)) {
                    isValid = false;
                    errorMessage = "La pause doit être entre 0 et 120 minutes.";
                }
                break;

            case "note":
                if (value.length > 500) {
                    isValid = false;
                    errorMessage = "La note ne peut pas dépasser 500 caractères.";
                }
                break;
        }

        // Appliquer le style de validation
        field.classList.remove("is-invalid", "is-valid");
        field.classList.add(isValid ? "is-valid" : "is-invalid");

        if (!isValid && field.nextElementSibling) {
            field.nextElementSibling.textContent = errorMessage;
        }

        return isValid;
    }

    /**
     * Valide le formulaire complet avant sauvegarde
     */
    validateForm() {
        this.clearFormErrors();

        const startInput = document.getElementById("heure_debut");
        const endInput = document.getElementById("heure_fin");
        const pauseInput = document.getElementById("pause_duree");

        const start = startInput?.value || "";
        const end = endInput?.value || "";
        const pause = parseInt(pauseInput?.value) || 0;

        const errors = [];

        // érifier si l'heure de début est plus petite que l'heure de fin
        if (start && end && this.timeToMinutes(end) <= this.timeToMinutes(start)) {
            endInput?.classList.add("is-invalid");
            errors.push("L'heure de fin doit être après l'heure de début.");
        }

        // Vérification des champs obligatoires
        if (!start) {
            startInput?.classList.add("is-invalid");
            errors.push("L'heure de début est obligatoire.");
        }

        if (!end) {
            endInput?.classList.add("is-invalid");
            errors.push("L'heure de fin est obligatoire.");
        }

        if (errors.length > 0) {
            this.showFormErrors(errors);
            return false;
        }

        // Vérification du format
        if (!/^\d{2}:\d{2}$/.test(start) || !/^\d{2}:\d{2}$/.test(end)) {
            errors.push("Le format des heures doit être HH:MM.");
            this.showFormErrors(errors);
            return false;
        }

        // Vérification de la logique
        const startMinutes = this.timeToMinutes(start);
        const endMinutes = this.timeToMinutes(end);

        if (endMinutes <= startMinutes) {
            endInput?.classList.add("is-invalid");
            errors.push("L'heure de fin doit être après l'heure de début.");
            this.showFormErrors(errors);
            return false;
        }

        if (errors.length > 0) {
            this.showFormErrors(errors);
            return false;
        }

        // Tout est valide
        startInput?.classList.add("is-valid");
        endInput?.classList.add("is-valid");
        return true;
    }

    /**
     * Affiche les erreurs de validation
     */
    showFormErrors(errors) {
        const errorContainer = document.getElementById("form-errors");
        const errorList = document.getElementById("error-list");

        if (!errorContainer || !errorList) return;

        if (errors.length > 0) {
            errorList.innerHTML = "";
            errors.forEach((error) => {
                const li = document.createElement("li");
                li.textContent = error;
                errorList.appendChild(li);
            });
            errorContainer.classList.remove("d-none");
        } else {
            errorContainer.classList.add("d-none");
        }
    }

    /**
     * Efface les erreurs de validation
     */
    clearFormErrors() {
        const errorContainer = document.getElementById("form-errors");
        if (errorContainer) {
            errorContainer.classList.add("d-none");
        }

        const fields = document.querySelectorAll("#workShiftForm .form-control");
        fields.forEach((field) => {
            field.classList.remove("is-invalid", "is-valid");
        });
    }

    // ==========================================
    // SAUVEGARDE ET CHARGEMENT DES DONNÉES
    // ==========================================

    /**
     * Charge les données existantes d'un quart depuis le localStorage
     */
    loadExistingShiftData() {
        const existingData = this.getStoredShiftData();
        if (!existingData) return;

        const fields = {
            heure_debut: existingData.heure_debut || "",
            heure_fin: existingData.heure_fin || "",
            pause_duree: existingData.pause_duree || 30,
            note: existingData.note || "",
        };

        Object.entries(fields).forEach(([id, value]) => {
            const input = document.getElementById(id);
            if (input) input.value = value;
        });

        this.calculateDurations();
    }

    /**
     * Récupère les données stockées pour le quart courant
     */
    getStoredShiftData() {
        if (!this.currentWorkShift) return null;

        const key = `shift_${this.currentWorkShift.employeeId}_${this.currentWorkShift.date}`;
        const stored = localStorage.getItem(key);
        return stored ? JSON.parse(stored) : null;
    }

    /**
     * Sauvegarde le quart de travail
     */
    saveWorkShift() {
        console.log("Sauvegarde du quart...");

        // Validation de base seulement
        if (!this.validateForm()) {
            console.log("Validation échouée");
            return;
        }

        // Récupération des données
        const heureDebut = document.getElementById("heure_debut").value;
        const heureFin = document.getElementById("heure_fin").value;

        console.log("✅ Sauvegarde directe sans vérification de disponibilité");

        const shiftData = {
            employee_id: this.currentWorkShift.employeeId,
            employee_name: this.currentWorkShift.employeeName,
            date: this.currentWorkShift.date,
            day: this.currentWorkShift.day,
            heure_debut: heureDebut,
            heure_fin: heureFin,
            pause_duree: parseInt(document.getElementById("pause_duree").value) || 0,
            note: document.getElementById("note").value.trim(),
            timestamp: new Date().toISOString(),
        };

        // Sauvegarde locale
        const key = `shift_${shiftData.employee_id}_${shiftData.date}`;
        localStorage.setItem(key, JSON.stringify(shiftData));

        // Mise à jour de l'affichage
        this.updateCellDisplay(shiftData);

        // Fermeture du modal
        const modal = bootstrap.Modal.getInstance(
            document.getElementById("timeEditModal")
        );
        if (modal) modal.hide();

        // Message de succès
        this.showSuccessMessage("Quart de travail enregistré avec succès !");

        console.log("Quart sauvegardé:", shiftData);
    }

    /**
     * Met à jour l'affichage de la cellule après sauvegarde
     */
    updateCellDisplay(shiftData) {
        if (!this.currentWorkShift?.cell) return;

        const cell = this.currentWorkShift.cell;
        const timeSlot = cell.querySelector(".time-slot");

        if (timeSlot) {
            const timeDisplay = timeSlot.querySelector(".time-display");
            if (timeDisplay) {
                timeDisplay.textContent = `${shiftData.heure_debut} - ${shiftData.heure_fin}`;
            }

            cell.classList.add("has-shift");

            // Ajouter un petit bouton de suppression directement dans la cellule
            this.addDeleteButtonToCell(cell);

            // Tooltip avec détails
            let tooltip = `${shiftData.heure_debut} - ${shiftData.heure_fin}`;
            if (shiftData.pause_duree > 0) {
                tooltip += `\nPause: ${shiftData.pause_duree} min`;
            }
            if (shiftData.note) {
                tooltip += `\nNote: ${shiftData.note}`;
            }
            cell.title = tooltip;
        }
    }

    /**
     * Ajoute un petit bouton de suppression directement dans la cellule
     */
    addDeleteButtonToCell(cell) {
        if (!this.canEditWeek) return; // lecture seule

        if (cell.querySelector(".delete-shift-btn")) return;

        const deleteBtn = document.createElement("button");
        deleteBtn.className = "delete-shift-btn btn btn-sm btn-danger";
        deleteBtn.innerHTML = '<i class="fas fa-times"></i>';
        deleteBtn.title = "Supprimer ce quart";
        deleteBtn.style.cssText =
            "position: absolute; top: 2px; right: 2px; padding: 2px 6px; font-size: 0.7rem; z-index: 10;";

        deleteBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            this.quickDeleteShift(cell);
        });

        const timeSlot = cell.querySelector(".time-slot");
        if (timeSlot) {
            timeSlot.style.position = "relative";
            timeSlot.appendChild(deleteBtn);
        }
    }

    /**
     * Suppression rapide depuis la cellule (sans ouvrir le modal)
     */
    quickDeleteShift(cell) {
        const employeeId = cell.dataset.employeeId;
        const date = cell.dataset.date;
        const employeeRow = cell.closest(".employee-row");
        const employeeName =
            employeeRow?.querySelector(".employee-name")?.textContent || "Employé";

        const confirmMsg = `Supprimer le quart de ${employeeName} le ${date} ?`;
        if (!confirm(confirmMsg)) return;

        const key = `shift_${employeeId}_${date}`;
        localStorage.removeItem(key);

        // Nettoyer l'affichage
        this.clearCellShiftDisplayDirect(cell);
        this.showSuccessMessage("Quart supprimé avec succès.");
    }

    /**
     * Efface l'affichage du shift dans une cellule spécifique
     */
    clearCellShiftDisplayDirect(cell) {
        const timeSlot = cell.querySelector(".time-slot");
        if (timeSlot) {
            const timeDisplay = timeSlot.querySelector(".time-display");
            if (timeDisplay) timeDisplay.textContent = "-";

            // Supprimer le bouton de suppression
            const deleteBtn = timeSlot.querySelector(".delete-shift-btn");
            if (deleteBtn) deleteBtn.remove();
        }
        cell.classList.remove("has-shift");
        cell.removeAttribute("title");
    }

    /**
     * Charge tous les shifts existants depuis localStorage au démarrage
     */
    loadExistingShiftsFromStorage() {
        console.log("🔄 Chargement des shifts existants...");

        const cells = document.querySelectorAll(".schedule-cell");
        let shiftsLoaded = 0;

        cells.forEach((cell) => {
            const employeeId = cell.dataset.employeeId;
            const date = cell.dataset.date;

            if (employeeId && date) {
                const key = `shift_${employeeId}_${date}`;
                const storedData = localStorage.getItem(key);

                if (storedData) {
                    try {
                        const shiftData = JSON.parse(storedData);
                        this.displayShiftInCell(cell, shiftData);
                        shiftsLoaded++;
                    } catch (error) {
                        console.error("Erreur parsing shift:", error);
                    }
                }
            }
        });

        console.log(`✅ ${shiftsLoaded} shifts chargés depuis localStorage`);
    }

    /**
     * Affiche un shift dans une cellule (utilisé au chargement)
     */
    displayShiftInCell(cell, shiftData) {
        const timeSlot = cell.querySelector(".time-slot");
        if (!timeSlot) return;

        const timeDisplay = timeSlot.querySelector(".time-display");
        if (timeDisplay) {
            timeDisplay.textContent = `${shiftData.heure_debut} - ${shiftData.heure_fin}`;
        }

        cell.classList.add("has-shift");
        this.addDeleteButtonToCell(cell);

        // Tooltip avec détails
        let tooltip = `${shiftData.heure_debut} - ${shiftData.heure_fin}`;
        if (shiftData.pause_duree > 0) {
            tooltip += `\nPause: ${shiftData.pause_duree} min`;
        }
        if (shiftData.note) {
            tooltip += `\nNote: ${shiftData.note}`;
        }
        cell.title = tooltip;
    }

    /**
     * Affiche le bouton supprimer dans le modal si un shift existe en localStorage
     */
    showDeleteButtonIfNeeded() {
        console.log("🔍 Vérification bouton supprimer...");
        const deleteBtn = document.getElementById("deleteWorkShiftBtn");
        console.log("🔍 Bouton trouvé:", deleteBtn);

        if (!deleteBtn || !this.currentWorkShift) {
            console.log("❌ Bouton ou currentWorkShift manquant");
            return;
        }

        const key = `shift_${this.currentWorkShift.employeeId}_${this.currentWorkShift.date}`;
        const storedData = localStorage.getItem(key);
        const exists = !!storedData;

        console.log("🔍 Clé localStorage:", key);
        console.log("🔍 Données stockées:", storedData);
        console.log("🔍 Shift existe:", exists);

        if (exists) {
            deleteBtn.classList.remove("d-none");
            console.log("✅ Bouton supprimer affiché");
        } else {
            deleteBtn.classList.add("d-none");
            console.log("⚠️ Bouton supprimer caché");
        }
    }

    /**
     * Demande confirmation puis supprime le shift localement
     */
    confirmAndDeleteShift() {
        if (!this.currentWorkShift) return;

        const confirmMsg = `Voulez-vous vraiment supprimer le quart de ${this.currentWorkShift.employeeName} le ${this.currentWorkShift.date} ?`;
        if (!confirm(confirmMsg)) return;

        this.deleteWorkShift();
    }

    /**
     * Supprime le shift du localStorage et met à jour l'UI
     */
    deleteWorkShift() {
        if (!this.currentWorkShift) return;

        const key = `shift_${this.currentWorkShift.employeeId}_${this.currentWorkShift.date}`;
        localStorage.removeItem(key);

        // Mettre à jour l'affichage de la cellule
        this.clearCellShiftDisplay();

        // Masquer le bouton supprimer
        const deleteBtn = document.getElementById("deleteWorkShiftBtn");
        if (deleteBtn) deleteBtn.classList.add("d-none");

        // Fermer le modal
        const modalEl = document.getElementById("timeEditModal");
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();

        this.showSuccessMessage("Quart supprimé avec succès.");
    }

    /**
     * Efface l'affichage du shift dans la cellule (retour à l'état vide)
     */
    clearCellShiftDisplay() {
        if (!this.currentWorkShift?.cell) return;
        this.clearCellShiftDisplayDirect(this.currentWorkShift.cell);
    }

    /**
     * Affiche un message de succès (toast Bootstrap)
     */
    showSuccessMessage(message) {
        const toast = document.createElement("div");
        toast.className =
            "toast align-items-center text-bg-success border-0 position-fixed";
        toast.style.cssText = "top: 20px; right: 20px; z-index: 9999;";
        toast.setAttribute("role", "alert");
        toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          <i class="fas fa-check-circle me-2"></i>${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    `;

        document.body.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        toast.addEventListener("hidden.bs.toast", () => {
            document.body.removeChild(toast);
        });
    }

    // ==========================================
    // NAVIGATION HEBDOMADAIRE
    // ==========================================

    /**
     * Change la semaine affichée
     */
    changeWeek(direction) {
        this.currentWeekOffset += direction;
        this.loadWeekData();
    }

    /**
     * Charge les données pour la semaine courante
     */
    loadWeekData() {
        const today = new Date();
        const targetDate = new Date(today);
        targetDate.setDate(today.getDate() + this.currentWeekOffset * 7);

        const monday = this.getMondayOfWeek(targetDate);
        this.weekDays = this.generateWeekDays(monday);

        this.updateWeekDisplay();
        this.updateGridHeaders();
    }

    /**
     * Génère les 7 jours d'une semaine à partir d'une date de début
     */
    generateWeekDays(startDate) {
        const dayNames = [
            "Lundi",
            "Mardi",
            "Mercredi",
            "Jeudi",
            "Vendredi",
            "Samedi",
            "Dimanche",
        ];
        const weekDays = [];

        for (let i = 0; i < 7; i++) {
            const date = new Date(startDate);
            date.setDate(startDate.getDate() + i);

            weekDays.push({
                jour_name: dayNames[i],
                date_short: date.toLocaleDateString("fr-FR", {
                    day: "2-digit",
                    month: "2-digit",
                }),
                date_formatted: date.toLocaleDateString("fr-FR", {
                    day: "2-digit",
                    month: "2-digit",
                    year: "numeric",
                }),
                date: date,
            });
        }

        return weekDays;
    }

    /**
     * Met à jour l'affichage de la semaine courante
     */
    updateWeekDisplay() {
        const weekDisplay = document.getElementById("current-week-display");
        if (!weekDisplay || !this.weekDays || this.weekDays.length < 7) return;

        const firstDay = this.weekDays[0];
        const lastDay = this.weekDays[6];

        const startDate = firstDay.date_formatted || firstDay.date_short;
        const endDate = lastDay.date_formatted || lastDay.date_short;

        weekDisplay.textContent = `${startDate} - ${endDate}`;
    }

    /**
     * Met à jour les en-têtes de colonnes du tableau
     */
    updateGridHeaders() {
        const dayHeaders = document.querySelectorAll(".day-header");

        this.weekDays.forEach((day, index) => {
            if (dayHeaders[index]) {
                const dayName = dayHeaders[index].querySelector(".day-name");
                const dayDate = dayHeaders[index].querySelector(".day-date");

                if (dayName) dayName.textContent = day.jour_name;
                if (dayDate) dayDate.textContent = day.date_short;
            }
        });
    }

    // ==========================================
    // UTILITAIRES
    // ==========================================

    /**
     * Convertit une heure HH:MM en minutes depuis minuit
     */
    timeToMinutes(time) {
        const [hours, minutes] = time.split(":").map(Number);
        return hours * 60 + minutes;
    }

    /**
     * Formate une durée en minutes en format HhMM ou XXmin
     */
    formatDuration(minutes) {
        if (minutes >= 60) {
            const hours = Math.floor(minutes / 60);
            const mins = minutes % 60;
            return `${hours}h${String(mins).padStart(2, "0")}`;
        }
        return `${minutes}min`;
    }

    /**
     * Retourne le lundi d'une semaine donnée
     */
    getMondayOfWeek(date) {
        const day = date.getDay();
        const diff = day === 0 ? -6 : 1 - day; // Dimanche = 0
        const monday = new Date(date);
        monday.setDate(date.getDate() + diff);
        return monday;
    }

    // ==========================================
    // INDICATEURS DE DISPONIBILITÉ
    // ==========================================

    /**
     * Met à jour les indicateurs visuels de disponibilité dans la grille
     */
    updateAvailabilityIndicators() {
        const scheduleCells = document.querySelectorAll(".schedule-cell");

        scheduleCells.forEach((cell) => {
            const { employeeId, day } = cell.dataset;

            if (!employeeId || !day) return;

            const availability = this.checkEmployeeAvailability(employeeId, day);

            // Supprimer les classes existantes
            cell.classList.remove("has-availability", "no-availability");

            if (availability) {
                cell.classList.add("has-availability");
                cell.title = `Disponible: ${availability.heure_debut} - ${availability.heure_fin}`;

                // Ajouter un petit indicateur
                if (!cell.querySelector(".availability-indicator")) {
                    const indicator = document.createElement("div");
                    indicator.className = "availability-indicator";
                    indicator.innerHTML =
                        '<i class="fas fa-check-circle text-success"></i>';
                    cell.appendChild(indicator);
                }
            } else {
                cell.classList.add("no-availability");
                cell.title = "Employé non disponible ce jour";

                // Supprimer l'indicateur s'il existe
                const indicator = cell.querySelector(".availability-indicator");
                if (indicator) {
                    indicator.remove();
                }
            }
        });
    }
}

// ==========================================
// FONCTIONS DE PUBLICATION
// ==========================================

function publishSchedule() {
    console.log("Début de la publication de l'horaire");

    const allShifts = getAllShiftsFromLocalStorage();
    if (Object.keys(allShifts).length === 0) {
        showMessage("Aucun shift à publier. Créez d'abord des shifts.", "warning");
        return;
    }

    // Demander confirmation
    if (
        !confirm(
            `Êtes-vous sûr de vouloir publier cet horaire avec ${Object.keys(allShifts).length
            } shifts?`
        )
    ) {
        return;
    }

    // Désactiver le bouton pendant la publication
    const publishBtn = document.getElementById("publishScheduleBtn");
    if (publishBtn) {
        publishBtn.disabled = true;
        publishBtn.innerHTML =
            '<i class="fas fa-spinner fa-spin"></i> Publication...';
    }

    fetch("/publish-schedule/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({
            shifts: allShifts,
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                showMessage(
                    `Horaire publié avec succès! ${data.shifts_created} shifts créés.`,
                    "success"
                );
                // Nettoyer le localStorage après publication réussie
                clearAllShiftsFromLocalStorage();
                // Rediriger vers la page de visualisation après un délai
                setTimeout(() => {
                    window.location.href = "/view-schedule/";
                }, 2000);
            } else {
                showMessage(`Erreur lors de la publication: ${data.error}`, "danger");
            }
        })
        .catch((error) => {
            console.error("Erreur lors de la publication:", error);
            showMessage("Erreur lors de la publication de l'horaire", "danger");
        })
        .finally(() => {
            // Réactiver le bouton
            if (publishBtn) {
                publishBtn.disabled = false;
                publishBtn.innerHTML =
                    '<i class="fas fa-upload"></i> Publier l\'horaire';
            }
        });
}

function getAllShiftsFromLocalStorage() {
    const allShifts = {};

    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith("shift_")) {
            try {
                const shiftData = JSON.parse(localStorage.getItem(key));
                allShifts[key] = shiftData;
            } catch (error) {
                console.error("Erreur lors de la lecture du shift:", key, error);
            }
        }
    }

    console.log(
        `${Object.keys(allShifts).length} shifts trouvés dans localStorage`
    );
    return allShifts;
}



function clearAllShiftsFromLocalStorage() {
    const keysToRemove = [];

    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith("shift_")) {
            keysToRemove.push(key);
        }
    }

    keysToRemove.forEach((key) => {
        localStorage.removeItem(key);
    });

    console.log(`${keysToRemove.length} shifts supprimés du localStorage`);
}

function getCSRFToken() {
    return document.querySelector("[name=csrfmiddlewaretoken]").value;
}

function showMessage(message, type = "info") {
    // Créer un élément d'alerte Bootstrap
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

    // Insérer l'alerte en haut de la page
    const container = document.querySelector(".container-fluid") || document.body;
    container.insertBefore(alertDiv, container.firstChild);

    // Supprimer automatiquement l'alerte après 5 secondes
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// ==========================================
// INITIALISATION
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
    console.log("Initialisation du gestionnaire d'horaires");

    const pageElement = document.querySelector(".page-creation-horaire");
    if (!pageElement) {
        console.log("Page de création d'horaires non détectée");
        return;
    }

    const manager = new HoraireManager();
    console.log("Gestionnaire d'horaires initialisé");
});

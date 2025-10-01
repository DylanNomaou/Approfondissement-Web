// ===========================
// DASHBOARD MAIN JAVASCRIPT
// ===========================

document.addEventListener('DOMContentLoaded', function() {
    
    // ===========================
    // TIME UPDATE FUNCTIONS
    // ===========================
    
    // Mise à jour de l'heure détaillée dans le dashboard
    function updateDetailedTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        const element = document.getElementById('current-detailed-time');
        if (element) {
            element.textContent = timeString;
        }
    }
    
    // Mise à jour de l'heure dans le header
    function updateHeaderTime() {
        const now = new Date();
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        const element = document.getElementById('current-time');
        if (element) {
            element.textContent = now.toLocaleDateString('fr-FR', options);
        }
    }
    
    // Mise à jour de l'heure dans le footer
    function updateFooterTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        const element = document.getElementById('footer-time');
        if (element) {
            element.textContent = timeString;
        }
    }
    
    // Initialisation et intervales des mises à jour d'heure
    updateDetailedTime();
    updateHeaderTime();
    updateFooterTime();
    
    setInterval(updateDetailedTime, 1000);
    setInterval(updateHeaderTime, 1000);
    setInterval(updateFooterTime, 60000); // Footer update every minute
    
    // ===========================
    // TASK MANAGEMENT
    // ===========================
    
    // Animation des tâches au clic
    document.querySelectorAll('.task-item').forEach(item => {
        item.addEventListener('click', function() {
            const checkbox = this.querySelector('.task-checkbox i');
            const content = this.querySelector('.task-content span');
            
            if (checkbox && checkbox.classList.contains('bi-circle')) {
                // Marquer comme complété
                checkbox.className = 'bi bi-check-circle-fill text-success fs-5';
                content.classList.add('text-decoration-line-through', 'text-muted');
                this.classList.remove('border-warning', 'bg-warning-subtle');
                this.classList.add('bg-light');
                
                // Animation de completion
                this.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 200);
            }
        });
    });
    
    // ===========================
    // ACTION BUTTONS ANIMATIONS
    // ===========================
    
    // Animation des boutons d'action
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            this.classList.add('animate__animated', 'animate__pulse');
            setTimeout(() => {
                this.classList.remove('animate__animated', 'animate__pulse');
            }, 600);
        });
    });
    
    // ===========================
    // SIDEBAR INTERACTIONS
    // ===========================
    
    // Animation pour les liens de la sidebar
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.classList.add('animate__animated', 'animate__pulse');
        });
        
        link.addEventListener('animationend', function() {
            this.classList.remove('animate__animated', 'animate__pulse');
        });
    });
    
    // ===========================
    // DASHBOARD CARDS ANIMATIONS
    // ===========================
    
    // Animation d'entrée pour les éléments
    const cards = document.querySelectorAll('.card, .dashboard-card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('animate__animated', 'animate__fadeInUp');
    });
    
    // ===========================
    // RESPONSIVE SIDEBAR TOGGLE
    // ===========================
    
    // Gestion du toggle sidebar mobile
    const sidebarToggle = document.querySelector('[data-bs-toggle="offcanvas"]');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            const sidebar = document.getElementById('sidebar');
            if (sidebar) {
                sidebar.classList.toggle('show');
            }
        });
    }
    
    // ===========================
    // NOTIFICATION INTERACTIONS
    // ===========================
    
    // Animation au hover des notifications
    document.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
    
    // ===========================
    // KEYBOARD ACCESSIBILITY
    // ===========================
    
    // Support du clavier pour les éléments interactifs
    document.querySelectorAll('.task-item, .action-btn').forEach(element => {
        element.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });
    
    // ===========================
    // UTILITY FUNCTIONS
    // ===========================
    
    // Function pour ajouter une classe temporairement
    window.addTemporaryClass = function(element, className, duration = 1000) {
        element.classList.add(className);
        setTimeout(() => {
            element.classList.remove(className);
        }, duration);
    };
    
    // Function pour créer des notifications toast (pour usage futur)
    window.showToast = function(message, type = 'info') {
        // Cette fonction pourra être développée pour afficher des toasts
        console.log(`${type}: ${message}`);
    };
});

// ===========================
// GLOBAL EVENT LISTENERS
// ===========================

// Gestion du redimensionnement de la fenêtre
window.addEventListener('resize', function() {
    // Ajustements responsive si nécessaires
    const sidebar = document.querySelector('.sidebar');
    const mainWrapper = document.querySelector('.main-wrapper');
    
    if (window.innerWidth <= 768 && sidebar && mainWrapper) {
        mainWrapper.style.marginLeft = '0';
    } else if (sidebar && mainWrapper) {
        mainWrapper.style.marginLeft = '280px';
    }
});

// Gestion du focus pour l'accessibilité
document.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
        document.body.classList.add('keyboard-navigation');
    }
});

document.addEventListener('mousedown', function() {
    document.body.classList.remove('keyboard-navigation');
});

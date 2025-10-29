document.addEventListener('DOMContentLoaded', function() {
    const usernameInput = document.getElementById('id_username');
    const usernameError = document.getElementById('username-error');
    const usernameSucces = document.getElementById('username-success');
    const submitBtn = document.getElementById('submit-btn');
    let userCheckTimeout;
    let abortController = null;

    if (usernameInput) {
        usernameInput.addEventListener('input', function() {
            const username = this.value.trim();

            clearTimeout(userCheckTimeout);

            if (abortController) {
                abortController.abort();
            }

            usernameInput.classList.remove('is-invalid', 'is-valid');
            usernameError.textContent = '';
            usernameSucces.textContent = '';

            if (username.length < 3) {
                if (username.length > 0) {
                    usernameInput.classList.add('is-invalid');
                    usernameError.textContent = 'Le nom d\'utilisateur doit contenir au moins 3 caractères.';
                    submitBtn.disabled = true;
                }
                return;
            }

            userCheckTimeout = setTimeout(() => {
                checkUsername(username);
            }, 500);
        });
    }
    async function checkUsername(username) {

        abortController = new AbortController();

        try {
            const response = await envoyerRequeteAjax(
                '/check_username/',
                'GET',
                { username: username },
                abortController
            );
            if (response.exists) {
                usernameInput.classList.add('is-invalid');
                usernameInput.classList.remove('is-valid');
                usernameError.textContent = 'Ce nom d\'utilisateur est déjà pris.';
                usernameSucces.textContent = '';
                submitBtn.disabled = true;
            } else {
                usernameInput.classList.add('is-valid');
                usernameInput.classList.remove('is-invalid');
                usernameError.textContent = '';
                usernameSucces.textContent = 'Ce nom d\'utilisateur est disponible.';
                submitBtn.disabled = false;
            }
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.log('Requête annulée');
                return;
            }
            console.error('Erreur lors de la vérification du nom d\'utilisateur:', error);
            userrnameInput.classList.add('is-invalid');
            usernameError.textContent = 'Erreur lors de la vérification du nom d\'utilisateur.';
            submitBtn.disabled = false;
        }
    }
});


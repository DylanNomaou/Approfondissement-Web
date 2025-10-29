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
        });
    }

});


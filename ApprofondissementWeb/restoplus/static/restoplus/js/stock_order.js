document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');

    document.querySelectorAll('.delete-item-btn').forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            const card = this.closest('.card');
            const checkbox = card.querySelector('input[name$="-DELETE"]');

            const visibleCards = document.querySelectorAll('.formset-item.card:not([style*="display: none"])');

            if (visibleCards.length <= 1) {
                alert('Vous devez avoir au moins un article dans la commande.');
                return;
            }

            if (checkbox) {
                checkbox.checked = true;
            }
            card.style.display = 'none';
        });
    });

    form.addEventListener('submit', function(e) {
        const visibleCards = document.querySelectorAll('.formset-item.card:not([style*="display: none"])');
        let hasValidArticle = false;

        visibleCards.forEach(function(card) {
            const select = card.querySelector('select[name*="inventory_item"]');
            const quantity = card.querySelector('input[name*="quantity"]');

            if (select && select.value && quantity && quantity.value) {
                hasValidArticle = true;
            }
        });

        if (!hasValidArticle) {
            e.preventDefault();
            alert('Vous devez avoir au moins un article valide dans la commande.');
        }
    });
});
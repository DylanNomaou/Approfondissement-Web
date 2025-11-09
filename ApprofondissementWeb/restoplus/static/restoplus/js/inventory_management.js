(function(){
  const form = document.getElementById('inventory-filter-form');
  if (!form) return;

  // Envoi quand un filtre est sélectionné
  form.querySelectorAll('select').forEach(select => {
    select.addEventListener('change', () => form.submit());
  });
})();

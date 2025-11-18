(function () {
  const form = document.getElementById('inventory-filter-form');
  if (!form) return;

  // Envoi quand un filtre est sélectionné
  form.querySelectorAll('select').forEach(select => {
    select.addEventListener('change', () => form.submit());
  });
})();


//********************
// SUGGESTIONS RECHERCHE
//******************** 

const divSuggestions = document.getElementById("suggestions");
let debounceTimer;
let controller=null;

function afficherSuggestionsDebounced() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(afficherSuggestions, 200);
}

function gererClicFenetre(evenement) {
  const div = document.getElementById("suggestions");
  const input = document.getElementById("id_recherche");

  if (!div.contains(evenement.target)&& !input.contains(evenement.target)) {
    div.replaceChildren();
    div.classList.add("masquer");
    document.removeEventListener("click", gererClicFenetre);
  }
}


async function afficherSuggestions() {
  let valeur = document.getElementById("id_recherche").value.trim();
  divSuggestions.replaceChildren();
  if (valeur.length < 3) {
    divSuggestions.classList.add("masquer");
    return;
  }
  if (controller) controller.abort();
  controller = new AbortController();
  const signal = controller.signal;
  try {
    const response = await fetch('/ajax/suggestions/' + encodeURIComponent(valeur), { signal });
    let data = await response.json();
    resultats(data.suggestions, valeur).forEach(item => {
      const a = document.createElement("a");
      a.href = "#";
      a.textContent = item.name;
      a.dataset.value = item.name; // pour remplir le champ plus tard
      divSuggestions.appendChild(a);
    });
    divSuggestions.classList.remove("masquer");
  } catch (err) {
    if (err.name === 'AbortError') return;
  }
  document.addEventListener("click", gererClicFenetre);
}

divSuggestions.addEventListener("click", (e) => {
  const lien = e.target.closest("a");
  if (!lien) return;
  e.preventDefault();
  const champ = document.getElementById("id_recherche");
  const form = document.getElementById("inventory-filter-form");
  if (champ) champ.value = lien.dataset.value || lien.textContent;
  if (form) form.submit();
  divSuggestions.replaceChildren();
  divSuggestions.classList.add("masquer");
});

function resultats(suggestions, query) {
  // Trie et récupère les 5 premiers résultats
  return suggestions
    .sort((a, b) => {
      const score = (item) => {
        if (item.name.toLowerCase().includes(query.toLowerCase())) return 3;
        if (item.sku.toLowerCase().includes(query.toLowerCase())) return 2;
        if (item.supplier.toLowerCase().includes(query.toLowerCase())) return 1;
        return 0;
      }
      return score(b) - score(a);
    })
    .slice(0, 5);
}


function initialisation() {
  document
    .getElementById("id_recherche")
    .addEventListener("input", afficherSuggestionsDebounced)
}
window.addEventListener("load", initialisation)
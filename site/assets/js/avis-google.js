/**
 * Azurine — avis Google affichés automatiquement sur avis.html.
 *
 * PRÉPARÉ MAIS PAS ENCORE ACTIVÉ. Mise en place pas à pas :
 * livraison/guide-avis-google.pdf (clé Google, identifiant du lieu, confidentialité).
 *
 * Tant que CLE_API ou IDENTIFIANT_LIEU est vide, ce script ne fait rien et rien
 * n'est chargé depuis Google. Google fournit au maximum 5 avis, choisis par lui.
 * En cas d'erreur (clé refusée, quota atteint…), la section reste cachée :
 * le bouton « Laisser un avis sur Google » reste visible en haut de la page.
 */

// À remplir au moment de l'activation (voir le guide) ------------------------------
const CLE_API = '';            // clé de l'API Google, limitée au site azurine.fr
const IDENTIFIANT_LIEU = '';   // Place ID de la fiche Google d'Azurine (commence par « ChIJ »)

// Chargement de la bibliothèque Google Maps (sans carte) ---------------------------
function chargerGoogle() {
  return new Promise((resolve, reject) => {
    window.azurineGoogleCharge = resolve;
    const parametres = new URLSearchParams({
      key: CLE_API,
      v: 'weekly',
      language: 'fr',
      region: 'FR',
      loading: 'async',
      callback: 'azurineGoogleCharge',
    });
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?${parametres}`;
    script.async = true;
    script.onerror = reject;
    document.head.append(script);
  });
}

// Étoiles : visibles à l'écran, lues « Note : 5 sur 5 » par les lecteurs d'écran
function creerEtoiles(note) {
  const etoiles = document.createElement('p');
  etoiles.className = 'google-reviews__stars';
  etoiles.setAttribute('role', 'img');
  etoiles.setAttribute('aria-label', `Note : ${note} sur 5`);
  etoiles.textContent = '★'.repeat(Math.round(note)) + '☆'.repeat(5 - Math.round(note));
  return etoiles;
}

// Un avis = un <li class="testimonial">, comme les témoignages écrits à la main
function creerAvis(avis) {
  const item = document.createElement('li');
  item.className = 'testimonial';

  if (avis.rating) item.append(creerEtoiles(avis.rating));

  const citation = document.createElement('blockquote');
  citation.className = 'testimonial__quote';
  const texte = document.createElement('p');
  texte.textContent = avis.text;
  citation.append(texte);
  item.append(citation);

  // Google impose d'afficher le nom de l'auteur, avec un lien vers son profil
  const auteur = document.createElement('p');
  auteur.className = 'testimonial__author';
  const nom = avis.authorAttribution?.displayName || 'Avis Google';
  const profil = avis.authorAttribution?.uri;
  if (profil) {
    const lien = document.createElement('a');
    lien.href = profil;
    lien.target = '_blank';
    lien.rel = 'noopener';
    lien.textContent = nom;
    auteur.append(lien);
  } else {
    auteur.append(nom);
  }
  if (avis.relativePublishTimeDescription) {
    auteur.append(`, ${avis.relativePublishTimeDescription}`);
  }
  item.append(auteur);

  return item;
}

async function afficherAvisGoogle() {
  const section = document.getElementById('avis-google');
  if (!section || !CLE_API || !IDENTIFIANT_LIEU) return;

  try {
    await chargerGoogle();
    const { Place } = await google.maps.importLibrary('places');
    const lieu = new Place({ id: IDENTIFIANT_LIEU, requestedLanguage: 'fr' });
    await lieu.fetchFields({ fields: ['rating', 'userRatingCount', 'reviews', 'googleMapsURI'] });

    const avis = (lieu.reviews || []).filter((un) => un.text);
    if (avis.length === 0) return;

    // Note moyenne et nombre d'avis
    const resume = section.querySelector('.google-reviews__summary');
    if (lieu.rating && lieu.userRatingCount) {
      const note = lieu.rating.toLocaleString('fr-FR', { maximumFractionDigits: 1 });
      resume.textContent = `${note} sur 5, d'après ${lieu.userRatingCount} avis Google`;
    }

    section.querySelector('.testimonials').append(...avis.map(creerAvis));

    const tousLesAvis = section.querySelector('.google-reviews__more');
    if (lieu.googleMapsURI) tousLesAvis.href = lieu.googleMapsURI;

    section.hidden = false;
  } catch (erreur) {
    console.warn('Avis Google indisponibles :', erreur);
  }
}

afficherAvisGoogle();

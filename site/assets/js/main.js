/**
 * Azurine — interactions du site (JavaScript vanilla, aucune dépendance).
 *
 *  1. Menu mobile : bouton « burger » qui ouvre / ferme le panneau plein écran.
 *  2. Sous-menu « Soins proposés » (clic, clavier, touche Échap).
 *  3. Carte Google Maps (salle-de-soin.html) : chargée seulement après un clic,
 *     car Google dépose des cookies (voir confidentialite.html).
 *  4. En-tête : filet et ombre dès que la page défile.
 */

// 1. Menu mobile --------------------------------------------------------------
function initMobileMenu() {
  const header = document.querySelector('.site-header');
  const toggle = header?.querySelector('.menu-toggle');
  if (!toggle) return;

  const setOpen = (open) => {
    header.classList.toggle('is-menu-open', open);
    // Bloque le défilement de la page derrière le panneau ouvert
    document.documentElement.classList.toggle('has-menu-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
  };

  toggle.addEventListener('click', () => {
    setOpen(!header.classList.contains('is-menu-open'));
  });

  // Un lien vers une ancre de la même page (#soins…) referme le panneau
  header.querySelectorAll('.main-nav a').forEach((link) => {
    link.addEventListener('click', () => setOpen(false));
  });

  // Passage en desktop avec le panneau ouvert : on le referme
  window.matchMedia('(min-width: 921px)').addEventListener('change', (event) => {
    if (event.matches) setOpen(false);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && header.classList.contains('is-menu-open')) {
      setOpen(false);
      toggle.focus();
    }
  });
}

// 2. Sous-menus -----------------------------------------------------------------
function initSubmenus() {
  const toggles = document.querySelectorAll('.main-nav__toggle');

  const closeAll = (except) => {
    toggles.forEach((toggle) => {
      if (toggle !== except) toggle.setAttribute('aria-expanded', 'false');
    });
  };

  toggles.forEach((toggle) => {
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      closeAll(toggle);
      toggle.setAttribute('aria-expanded', String(open));
    });
  });

  // Fermeture en cliquant ailleurs ou avec Échap
  document.addEventListener('click', (event) => {
    if (!event.target.closest('.main-nav__item--has-submenu')) closeAll();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    const opened = [...toggles].find((t) => t.getAttribute('aria-expanded') === 'true');
    if (opened) {
      closeAll();
      opened.focus();
    }
  });
}

// 3. Carte Google Maps chargée à la demande ------------------------------------------
// Le bloc .map__consent porte l'adresse de la carte dans data-map-src. Tant que le
// visiteur n'a pas cliqué sur « Afficher la carte », aucune requête ne part vers Google.
function initMaps() {
  document.querySelectorAll('[data-map-src]').forEach((consent) => {
    const button = consent.querySelector('[data-map-load]');
    if (!button) return;

    button.addEventListener('click', () => {
      const frame = document.createElement('iframe');
      frame.className = 'map__frame';
      frame.src = consent.dataset.mapSrc;
      frame.title = 'Localisation de la salle de soin sur Google Maps';
      frame.referrerPolicy = 'no-referrer-when-downgrade';
      consent.replaceWith(frame);
      frame.focus();
    });
  });
}

// 4. En-tête au défilement ------------------------------------------------------------
function initHeaderShadow() {
  const header = document.querySelector('.site-header');
  if (!header) return;

  const update = () => header.classList.toggle('is-scrolled', window.scrollY > 8);
  update();
  window.addEventListener('scroll', update, { passive: true });
}

initMobileMenu();
initSubmenus();
initMaps();
initHeaderShadow();

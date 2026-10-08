"""Génère le site Azurine dans le dossier public/ (pages HTML, sitemap.xml, robots.txt).

Usage, depuis la racine du dépôt :  python3 -I build.py
Netlify lance la même commande à chaque mise en ligne (voir netlify.toml) et publie public/.

- infos.toml : informations modifiables par la cliente (tarifs, horaires, coordonnées, FAQ, avis).
  Elles sont lues et vérifiées ici ; une valeur invalide arrête la génération avec un message
  en français, et Netlify garde alors la version précédente en ligne.
- static/ : fichiers copiés tels quels (images, polices, CSS, JS, icônes, configuration Netlify).
- Ce fichier : structure et textes des pages.
"""
import html
import json
import re
import shutil
import subprocess
import sys
import tomllib
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / 'public'
INFOS_FILE = ROOT / 'infos.toml'


# =============================================================================================
# LECTURE ET VÉRIFICATION DE infos.toml
# =============================================================================================
def stop(message):
    """Arrête la génération : le message apparaît dans le journal de Netlify et dans celui de la
    vérification GitHub Actions (croix rouge sur le commit, e-mail de GitHub à son auteur)."""
    sys.exit(f'\nERREUR dans infos.toml : {message}\nLe site n\'a pas été mis à jour ; '
             'la version précédente reste en ligne.\n')


try:
    INFOS = tomllib.loads(INFOS_FILE.read_text(encoding='utf-8'))
except tomllib.TOMLDecodeError as e:
    stop(f'{e}.\nVérifier les guillemets "…" et les crochets autour de cette ligne.')


def section(name):
    value = INFOS.get(name)
    if not isinstance(value, dict):
        stop(f'la rubrique [{name}] est absente.')
    return value


def text(sec, key):
    value = section(sec).get(key)
    if not isinstance(value, str) or not value.strip():
        stop(f'[{sec}] {key} doit être un texte entre guillemets, non vide.')
    return value.strip()


def number(sec, key):
    value = section(sec).get(key)
    if not isinstance(value, int) or isinstance(value, bool) or not 0 < value < 1000:
        stop(f'[{sec}] {key} doit être un nombre entier, sans guillemets ni « € » (exemple : 60).')
    return value


def url(sec, key, prefix='https://'):
    value = text(sec, key)
    if not value.startswith(prefix) or ' ' in value:
        stop(f'[{sec}] {key} doit être une adresse commençant par {prefix}')
    return value


DAYS = {'lundi': 'Monday', 'mardi': 'Tuesday', 'mercredi': 'Wednesday', 'jeudi': 'Thursday',
        'vendredi': 'Friday', 'samedi': 'Saturday', 'dimanche': 'Sunday'}


def read_hours():
    rows = INFOS.get('horaires')
    if not isinstance(rows, list) or not rows:
        stop('il faut au moins un bloc [[horaires]].')
    hours = []
    for i, row in enumerate(rows, 1):
        day = str(row.get('jour', '')).strip().lower()
        opens, closes = str(row.get('ouverture', '')), str(row.get('fermeture', ''))
        if day not in DAYS:
            stop(f'horaire n° {i} : jour « {day} » inconnu (lundi, mardi, mercredi, jeudi, vendredi, samedi ou dimanche).')
        for t in (opens, closes):
            if not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', t):
                stop(f'horaire n° {i} ({day}) : « {t} » n\'est pas une heure valide (format "11:00").')
        if opens >= closes:
            stop(f'horaire n° {i} ({day}) : l\'ouverture doit précéder la fermeture.')
        hours.append((DAYS[day], day, opens, closes))
    return hours


def read_list(name, fields):
    rows = INFOS.get(name, [])
    if not isinstance(rows, list):
        stop(f'les blocs [[{name}]] sont mal écrits.')
    out = []
    for i, row in enumerate(rows, 1):
        values = []
        for f in fields:
            v = row.get(f)
            if not isinstance(v, str) or not v.strip():
                stop(f'{name} n° {i} : « {f} » doit être un texte entre guillemets, non vide.')
            values.append(v.strip())
        out.append(tuple(values))
    return out


# --- Coordonnées ---
PHONE_TEXT = text('contact', 'telephone')
_digits = re.sub(r'\D', '', PHONE_TEXT)
if not re.fullmatch(r'0\d{9}', _digits):
    stop('[contact] telephone doit être un numéro français à 10 chiffres (exemple : "06 62 41 94 03").')
PHONE_HREF = 'tel:+33' + _digits[1:]
EMAIL_TEXT = text('contact', 'email')
if not re.fullmatch(r'[^@\s"<>]+@[^@\s"<>]+\.[a-z]{2,}', EMAIL_TEXT):
    stop('[contact] email n\'est pas une adresse e-mail valide.')
INSTAGRAM = url('contact', 'instagram', 'https://www.instagram.com/')
GOOGLE_REVIEW = url('contact', 'lien_avis_google')
# La politique de confidentialité nomme l'outil de réservation : un autre outil que Cal.com
# demande de la mettre à jour, d'où ce contrôle.
BOOKING = {'url': url('contact', 'reservation_en_ligne', 'https://cal.com/'), 'name': 'Cal.com',
           'company': 'Cal.com, Inc.', 'privacy': 'https://cal.com/privacy'}

# --- Tarifs ---
PRICES = {
    'energetique': {'adulte': number('tarifs', 'soin_energetique_adulte'),
                    'enfant': number('tarifs', 'soin_energetique_enfant')},
    'sonore': {'adulte': number('tarifs', 'massage_sonore_adulte'),
               'enfant': number('tarifs', 'massage_sonore_enfant')},
}
SONORE_MIN_AGE = number('tarifs', 'massage_sonore_age_minimum')
if SONORE_MIN_AGE >= 16:
    stop('[tarifs] massage_sonore_age_minimum doit être inférieur à 16.')
SESSION = text('tarifs', 'duree_seance')
SESSION_TEXT = text('tarifs', 'duree_seance_en_lettres')

# --- Horaires, règlement, annulation ---
HOURS = read_hours()
PAYMENT = text('pratique', 'reglement').rstrip('.')
CANCEL = text('pratique', 'annulation').rstrip('.')

# --- Avis ---
TESTIMONIALS = read_list('avis', ('texte', 'auteur'))


# =============================================================================================
# INFORMATIONS FIXES (à modifier ici, par le développeur)
# =============================================================================================
YEAR = date.today().year    # année du pied de page
SITE_URL = 'https://azurine.fr'  # domaine principal (www redirige ici, réglé dans Netlify)
STREET, POSTCODE, CITY = '18 rue de la Salle', '44470', 'Carquefou'
GEO = (47.30054, -1.45018)  # Base Adresse Nationale : à recalculer si l'adresse change

# Communes citées pour le référencement local (liste validée par la cliente)
AREA = ['Carquefou', 'Nantes', 'Sainte-Luce-sur-Loire', 'Thouaré-sur-Loire', 'La Chapelle-sur-Erdre']

# Avertissement demandé par la cliente : accueil, chaque page de soin et mentions légales.
HEALTH_NOTE = ('Les prestations proposées s\'inscrivent dans une démarche de bien-être et d\'accompagnement. '
               'Elles ne constituent pas des actes médicaux et ne remplacent en aucun cas un avis médical, '
               'un diagnostic ou un traitement prescrit par un professionnel de santé.')


def last_modified():
    """Date du dernier commit (déclarée à Google dans sitemap.xml) ; à défaut, la date du jour."""
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%cs'], cwd=ROOT, capture_output=True, text=True, timeout=10)
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', out.stdout.strip()):
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return date.today().isoformat()


LASTMOD = last_modified()


# --- Mise en forme ---------------------------------------------------------------------------
def eur(n):
    return f'{n} €'


def hour(t):
    """'11:00' → '11 h', '17:30' → '17 h 30'."""
    h, m = t.split(':')
    return f'{int(h)} h' + ('' if m == '00' else f' {m}')


def esc(s):
    """Texte de infos.toml inséré dans le HTML : <, > et & ne doivent pas casser la page."""
    return html.escape(s, quote=False)


_hours = [f'le {fr} de {hour(a)} à {hour(b)}' for _, fr, a, b in HOURS]
HOURS_TEXT = _hours[0] if len(_hours) == 1 else ', '.join(_hours[:-1]) + ' et ' + _hours[-1]
ADDRESS = f'{STREET}, {POSTCODE} {CITY}'
PHONE = f'<a href="{PHONE_HREF}">{PHONE_TEXT.replace(" ", "&nbsp;")}</a>'  # dans le texte : le numéro ne se coupe pas
EMAIL = f'<a href="mailto:{EMAIL_TEXT}">{EMAIL_TEXT}</a>'
BOOKING_URL = BOOKING['url']
MAP_QUERY = ADDRESS.replace(' ', '%20').replace(',', '%2C')
MAP_EMBED = f'https://maps.google.com/maps?q={MAP_QUERY}&amp;t=m&amp;z=15&amp;ie=UTF8&amp;output=embed'
MAP_LINK = f'https://www.google.com/maps/search/?api=1&amp;query={MAP_QUERY}'
P = PRICES
ALL_PRICES = [v for soin in PRICES.values() for v in soin.values()]
PRICE_RANGE = f'{eur(min(ALL_PRICES))} – {eur(max(ALL_PRICES))}'

# Questions fréquentes de l'accueil (infos.toml) : affichées sur la page ET déclarées à Google
# (FAQPage). Les mots entre accolades des réponses sont remplacés par l'information à jour.
PLACEHOLDERS = {
    'telephone': PHONE_TEXT, 'horaires': HOURS_TEXT, 'reglement': PAYMENT,
    'duree_seance_en_lettres': SESSION_TEXT,
    'soin_energetique_adulte': eur(P['energetique']['adulte']), 'soin_energetique_enfant': eur(P['energetique']['enfant']),
    'massage_sonore_adulte': eur(P['sonore']['adulte']), 'massage_sonore_enfant': eur(P['sonore']['enfant']),
    'massage_sonore_age_minimum': str(SONORE_MIN_AGE),
}


def fill(i, answer):
    def repl(m):
        if m.group(1) not in PLACEHOLDERS:
            stop(f'faq n° {i} : {{{m.group(1)}}} n\'est pas un mot remplaçable. '
                 f'Mots possibles : {", ".join("{" + k + "}" for k in PLACEHOLDERS)}.')
        return PLACEHOLDERS[m.group(1)]
    filled = re.sub(r'\{([^{}]*)\}', repl, answer)
    if '{' in filled or '}' in filled:
        stop(f'faq n° {i} : accolade {{ ou }} isolée dans la réponse.')
    return filled


FAQ = [(q, fill(i, a)) for i, (q, a) in enumerate(read_list('faq', ('question', 'reponse')), 1)]
if not FAQ:
    stop('il faut au moins une question [[faq]].')

# =============================================================================================
# STRUCTURE DU SITE
# =============================================================================================
# public/ est entièrement recréé à chaque génération : static/ y est copié, puis les pages écrites.
if SITE.exists():
    shutil.rmtree(SITE)
shutil.copytree(ROOT / 'static', SITE)

SOINS = [    ('soin-energetique.html', 'Soin énergétique'),
    ('massage-sonore.html', 'Massage sonore aux bols tibétains'),
    ('soin-a-distance.html', 'Soin à distance'),
]
NAV = [
    ('index.html', 'Accueil'),
    ('qui-suis-je.html', 'Qui suis-je ?'),
    ('salle-de-soin.html', 'La salle de soin'),
    ('SOINS', 'Soins proposés'),
    ('tarifs.html', 'Tarifs'),
    ('avis.html', 'Avis'),
]


# --- Icônes : dessinées à la main, trait 1,5 px, grille 24 px -------------------
def icon(paths, cls='icon'):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{paths}</svg>')


ARROW = icon('<path d="M5 12h14M13 6l6 6-6 6"/>', 'link-arrow__icon')
PHONE_ICON = icon('<path d="M6.5 3.5h2.6l1.6 4.2-2 1.3a11 11 0 0 0 6.3 6.3l1.3-2 4.2 1.6v2.6a2 2 0 0 1-2.1 2A16.5 16.5 0 0 1 4.5 5.6a2 2 0 0 1 2-2.1z"/>')
MAIL_ICON = icon('<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="m3.5 7 8.5 6 8.5-6"/>')
INSTA_ICON = icon('<rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="3.8"/><circle cx="17.2" cy="6.8" r="0.6" fill="currentColor"/>')
PIN_ICON = icon('<path d="M12 21s-6.5-5.8-6.5-11a6.5 6.5 0 0 1 13 0c0 5.2-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>')
MAP_ICON = icon('<path d="M9 4 3.5 6v14L9 18l6 2 5.5-2V4L15 6 9 4zM9 4v14M15 6v14"/>', 'map__icon')
CHEVRON = '<svg class="main-nav__chevron" viewBox="0 0 12 8" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="m1 1.5 5 5 5-5"/></svg>'


def arrow_link(href, label, extra=''):
    return f'<a class="link-arrow" href="{href}"{extra}>{label} {ARROW}</a>'


def nav_link(href, label, current):
    cur = ' aria-current="page"' if href == current else ''
    return f'<li class="main-nav__item"><a class="main-nav__link" href="{href}"{cur}>{label}</a></li>'


def header(current):
    items = []
    for href, label in NAV:
        if href != 'SOINS':
            items.append('          ' + nav_link(href, label, current))
            continue
        is_cur = ' is-current' if current in dict(SOINS) else ''
        sub = '\n'.join('              ' + nav_link(h, l, current) for h, l in SOINS)
        items.append(f'''          <li class="main-nav__item main-nav__item--has-submenu{is_cur}">
            <button class="main-nav__toggle" type="button" aria-expanded="false" aria-controls="submenu-soins">
              <span class="main-nav__toggle-label">{label}</span>
              {CHEVRON}
            </button>
            <ul class="main-nav__submenu" id="submenu-soins">
{sub}
            </ul>
          </li>''')
    nav = '\n'.join(items)
    cta_cur = ' aria-current="page"' if current == 'prendre-rdv.html' else ''
    return f'''  <!-- ===== En-tête (identique sur toutes les pages, seul aria-current change) ===== -->
  <header class="site-header">
    <div class="container site-header__inner">
      <a class="site-header__logo" href="index.html">
        <img src="assets/images/logo-azurine.png" alt="Azurine, énergéticienne – accueil" width="421" height="241">
      </a>

      <nav class="main-nav" id="main-nav" aria-label="Menu principal">
        <ul class="main-nav__list">
{nav}
        </ul>
        <a class="btn btn--primary btn--small main-nav__cta" href="prendre-rdv.html"{cta_cur}>Prendre RDV</a>
      </nav>

      <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="main-nav" aria-label="Ouvrir le menu">
        <span class="menu-toggle__bar"></span>
        <span class="menu-toggle__bar"></span>
        <span class="menu-toggle__bar"></span>
      </button>
    </div>
  </header>'''


def footer():
    soins = '\n'.join(f'            <li><a href="{h}">{l}</a></li>' for h, l in SOINS)
    return f'''  <!-- ===== Pied de page (identique sur toutes les pages) ===== -->
  <footer class="site-footer">
    <div class="container site-footer__inner">
      <div class="site-footer__brand">
        <a class="site-footer__logo" href="index.html">
          <img src="assets/images/logo-azurine.png" alt="Azurine, énergéticienne – accueil" width="421" height="241" loading="lazy">
        </a>
        <p>Énergéticienne à Carquefou.<br>Soins énergétiques, massages sonores et soins à distance.</p>
      </div>

      <nav aria-labelledby="footer-soins">
        <h2 class="site-footer__title" id="footer-soins">Soins</h2>
        <ul class="site-footer__list">
{soins}
            <li><a href="tarifs.html">Tarifs et bons cadeaux</a></li>
        </ul>
      </nav>

      <nav aria-labelledby="footer-azurine">
        <h2 class="site-footer__title" id="footer-azurine">Azurine</h2>
        <ul class="site-footer__list">
            <li><a href="qui-suis-je.html">Qui suis-je ?</a></li>
            <li><a href="salle-de-soin.html">La salle de soin</a></li>
            <li><a href="avis.html">Avis</a></li>
            <li><a href="prendre-rdv.html">Prendre rendez-vous</a></li>
        </ul>
      </nav>

      <div>
        <h2 class="site-footer__title">Contact</h2>
        <ul class="site-footer__list">
          <li><a href="{PHONE_HREF}">{PHONE_ICON}{PHONE_TEXT}</a></li>
          <li><a href="mailto:{EMAIL_TEXT}">{MAIL_ICON}{EMAIL_TEXT}</a></li>
          <li><a href="{INSTAGRAM}" target="_blank" rel="noopener">{INSTA_ICON}Instagram</a></li>
          <li><a href="salle-de-soin.html">{PIN_ICON}{STREET}, {CITY}</a></li>
        </ul>
      </div>
    </div>

    <div class="container site-footer__bottom">
      <ul class="site-footer__legal">
        <li><a href="mentions-legales.html">Mentions légales</a></li>
        <li><a href="confidentialite.html">Politique de confidentialité</a></li>
      </ul>
      <p>© {YEAR} Azurine</p>
    </div>
  </footer>'''


INDEXED = []  # pages à lister dans sitemap.xml

FAQ_SCHEMA = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    'mainEntity': [{'@type': 'Question', 'name': q,
                    'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQ],
}

# Données structurées schema.org (accueil uniquement) : nom, adresse, contact, horaires, soins.
# Lues par Google pour les résultats de recherche et le rapprochement avec la fiche Google Maps.
def offer(name, price, page):
    return {'@type': 'Offer', 'name': name, 'price': str(price), 'priceCurrency': 'EUR', 'url': f'{SITE_URL}/{page}'}


STRUCTURED_DATA = {
    '@context': 'https://schema.org',
    '@type': 'HealthAndBeautyBusiness',
    '@id': SITE_URL + '/#azurine',
    'name': 'Azurine',
    'legalName': 'Association AZURINE',
    'description': f'Énergéticienne à {CITY} : soin énergétique, massage sonore aux bols tibétains et soin à distance.',
    'url': SITE_URL + '/',
    'logo': SITE_URL + '/assets/images/logo-azurine.png',
    'image': SITE_URL + '/assets/images/accueil-papillon-lavande.jpg',
    'telephone': PHONE_HREF.removeprefix('tel:'),
    'email': EMAIL_TEXT,
    'address': {'@type': 'PostalAddress', 'streetAddress': STREET, 'postalCode': POSTCODE,
                'addressLocality': CITY, 'addressCountry': 'FR'},
    'geo': {'@type': 'GeoCoordinates', 'latitude': GEO[0], 'longitude': GEO[1]},
    'hasMap': MAP_LINK.replace('&amp;', '&'),
    'areaServed': [{'@type': 'City', 'name': c} for c in AREA],
    'founder': {'@type': 'Person', 'name': 'Karine Eude', 'jobTitle': 'Énergéticienne'},
    'knowsAbout': [name for _, name in SOINS],
    'sameAs': [INSTAGRAM],
    'priceRange': PRICE_RANGE,
    'paymentAccepted': 'Espèces, chèque',
    'openingHoursSpecification': [{'@type': 'OpeningHoursSpecification', 'dayOfWeek': day, 'opens': a, 'closes': b}
                                  for day, _, a, b in HOURS],
    'makesOffer': [
        offer(f'Soin énergétique ({SESSION}), adulte', P['energetique']['adulte'], 'soin-energetique.html'),
        offer(f'Soin énergétique ({SESSION}), enfant de moins de 16 ans', P['energetique']['enfant'], 'soin-energetique.html'),
        offer(f'Massage sonore aux bols tibétains ({SESSION}), adulte', P['sonore']['adulte'], 'massage-sonore.html'),
        offer(f'Massage sonore aux bols tibétains ({SESSION}), enfant de {SONORE_MIN_AGE} à 15 ans', P['sonore']['enfant'], 'massage-sonore.html'),
        {'@type': 'Offer', 'name': 'Soin à distance', 'url': SITE_URL + '/soin-a-distance.html'},
    ],
}

# Nom du site affiché par Google au-dessus du titre (« Azurine » plutôt que « azurine.fr »)
WEBSITE_DATA = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    '@id': SITE_URL + '/#site',
    'name': 'Azurine',
    'alternateName': ['Azurine énergéticienne', 'azurine.fr'],
    'url': SITE_URL + '/',
    'inLanguage': 'fr-FR',
    'publisher': {'@id': SITE_URL + '/#azurine'},
}


def json_ld(*blocks):
    out = ''
    for b in blocks:
        # « < » échappé : un texte de infos.toml ne peut pas fermer la balise <script>
        data = json.dumps(b, ensure_ascii=False, indent=2).replace('<', '\\u003c').replace('\n', '\n  ')
        out += f'\n  <script type="application/ld+json">\n  {data}\n  </script>'
    return out


def breadcrumb(filename, name):
    items = [{'@type': 'ListItem', 'position': 1, 'name': 'Accueil', 'item': SITE_URL + '/'}]
    if filename in dict(SOINS):
        items.append({'@type': 'ListItem', 'position': 2, 'name': 'Soins proposés', 'item': SITE_URL + '/tarifs.html'})
    items.append({'@type': 'ListItem', 'position': len(items) + 1, 'name': name, 'item': f'{SITE_URL}/{filename}'})
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': items}


def page(filename, title, description, main, current=None, noindex=False, root='', schema=(), name=None):
    """root='/' pour 404.html, servie par Netlify à n'importe quelle adresse.
    schema : blocs schema.org propres à la page ; name : nom court pour le fil d'Ariane."""
    robots = '\n  <meta name="robots" content="noindex">' if noindex else ''
    if filename == 'index.html':
        structured = json_ld(WEBSITE_DATA, STRUCTURED_DATA, FAQ_SCHEMA)
    elif not noindex:
        structured = json_ld(breadcrumb(filename, name or title.split(' | ')[0]), *schema)
    else:
        structured = ''
    page_url = SITE_URL + '/' + ('' if filename == 'index.html' else filename)
    canonical = '' if noindex else f'\n  <link rel="canonical" href="{page_url}">\n  <meta property="og:url" content="{page_url}">'
    if not noindex:
        INDEXED.append(filename)
    doc = f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">{robots}
  <meta name="theme-color" content="#fbf7f2">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="fr_FR">
  <meta property="og:site_name" content="Azurine">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="{SITE_URL}/assets/images/partage-azurine.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Logo Azurine, énergéticienne, et papillon posé sur une fleur de lavande">
  <meta name="twitter:card" content="summary_large_image">{canonical}
  <link rel="icon" href="/favicon.ico" sizes="48x48">
  <link rel="icon" href="/assets/icons/icon-192.png" type="image/png" sizes="192x192">
  <link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">

  <link rel="preload" href="assets/fonts/playfair-display-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="assets/fonts/source-sans-3-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="assets/css/variables.css">
  <link rel="stylesheet" href="assets/css/base.css">
  <link rel="stylesheet" href="assets/css/layout.css">
  <link rel="stylesheet" href="assets/css/components.css">
  <link rel="stylesheet" href="assets/css/pages.css">
  <script src="assets/js/main.js" defer></script>{structured}
</head>
<body>
  <a class="skip-link" href="#contenu">Aller au contenu</a>

{header(current or filename)}

  <main id="contenu">
{main.strip(chr(10))}
  </main>

{footer()}
</body>
</html>
'''
    if root:
        doc = doc.replace('href="assets/', f'href="{root}assets/').replace('src="assets/', f'src="{root}assets/')
        for href, _ in NAV + SOINS + [('mentions-legales.html', ''), ('confidentialite.html', ''), ('prendre-rdv.html', '')]:
            doc = doc.replace(f'href="{href}"', f'href="{root}{href}"')
    (SITE / filename).write_text(doc, encoding='utf-8')


def page_head(title, lead='', center=False, extra='', narrow=False):
    mod = ' page-head--center' if center else ''
    width = ' container--narrow' if narrow else ''
    lead_html = f'\n          <p class="page-head__lead">{lead}</p>' if lead else ''
    return f'''    <section class="page-head{mod}">
      <div class="container{width} page-head__inner">
        <h1 class="page-head__title">{title}</h1>{lead_html}{extra}
      </div>
    </section>
'''


# Contour du galet de l'accueil (même tracé que --shape-egg dans variables.css)
EGG_OUTLINE = ('<svg class="hero__outline" viewBox="0 0 200 200" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
               '<path pathLength="1" d="M121.089 0C174.339 0 200 65.9669 200 126.582C200 171.887 160.89 200 121.089 200C67.5113 200 0 187.57 0 126.582C0 53.4983 56.886 0 121.089 0Z"/></svg>')

# --------------------------------------------------------------------------- Accueil
FAQ_HTML = '\n'.join(f'''          <details class="faq__item">
            <summary class="faq__question">{esc(q).replace(' ?', '\u00a0?')}</summary>
            <p class="faq__answer">{esc(a).replace(PHONE_TEXT, PHONE)}</p>
          </details>''' for q, a in FAQ)
CARE_ITEMS = [
    ('soin-energetique.html', 'Soin énergétique', 'assets/images/karine-soin-energetique.jpg',
     'Karine pratiquant un soin énergétique sur une personne allongée', 375, 366,
     f'{SESSION_TEXT.capitalize()} à la salle de soin, pour un moment de détente et d\'apaisement.', f'{SESSION} · dès {eur(P["energetique"]["enfant"])}'),
    ('massage-sonore.html', 'Massage sonore aux bols tibétains', 'assets/images/salle-table-de-soin.jpg',
     'Table de soin recouverte d\'un plaid bleu', 375, 366,
     'Les sons et les vibrations des bols tibétains, pour un moment de détente.', f'{SESSION} · dès {eur(P["sonore"]["enfant"])}'),
    ('soin-a-distance.html', 'Soin à distance', 'assets/images/accueil-mains-lumiere.jpg',
     'Deux mains ouvertes baignées de lumière', 397, 302,
     'Un soin énergétique depuis chez vous, quand vous ne pouvez pas vous déplacer.', 'Renseignements par téléphone'),
]
care_html = '\n'.join(f'''          <li class="care-item">
            <div class="care-item__media"><img class="media" src="{src}" alt="{alt}" width="{w}" height="{h}" loading="lazy"></div>
            <h3 class="care-item__title"><a href="{href}">{title}</a></h3>
            <p class="care-item__text">{text}</p>
            <p class="care-item__meta">{meta}</p>
            <span class="link-arrow" aria-hidden="true">Découvrir {ARROW}</span>
          </li>''' for href, title, src, alt, w, h, text, meta in CARE_ITEMS)

page('index.html', 'Énergéticienne à Carquefou, près de Nantes | Azurine',
     'Karine, énergéticienne à Carquefou près de Nantes : soin énergétique, massage sonore aux bols tibétains, soin à distance. Rendez-vous en ligne.',
     f'''
    <!-- Haut de page -->
    <section class="hero">
      <div class="container hero__inner">
        <div class="hero__text">
          <h1 class="hero__title">Soins énergétiques<br> <em>&amp;</em> massages sonores<br> à Carquefou</h1>
          <p class="hero__lead">Je suis Karine, énergéticienne à Carquefou, aux portes de Nantes. Je vous accueille avec douceur et écoute pour relâcher les tensions et retrouver de l'apaisement.</p>
          <div class="actions">
            <a class="btn btn--primary" href="{BOOKING_URL}" target="_blank" rel="noopener">Prendre rendez-vous</a>
            {arrow_link('#soins', 'Découvrir les soins')}
          </div>
        </div>

        <div class="hero__media">
          {EGG_OUTLINE}
          <img class="hero__image media shape-egg" src="assets/images/accueil-papillon-lavande.jpg" alt="Papillon blanc posé sur une fleur de lavande" width="768" height="954" fetchpriority="high">
        </div>
      </div>
    </section>

    <!-- Indications -->
    <section class="section section--sand indications" aria-labelledby="indications-title">
      <div class="container indications__inner">
        <div class="indications__intro">
          <h2 class="indications__title" id="indications-title">Un moment pour vous, en cas de…</h2>
          <p class="health-note">{HEALTH_NOTE}</p>
          {arrow_link('soin-energetique.html', 'En savoir plus sur le soin énergétique')}
        </div>
        <!-- Situations de vie, pas de maladies : l'ancienne liste (eczéma, brûlures, addiction,
             inflammations…) laissait entendre un effet sur des pathologies. -->
        <ul class="indications__list">
          <li>Stress, tensions du quotidien</li>
          <li>Fatigue passagère</li>
          <li>Période de changement</li>
          <li>Besoin de calme et de détente</li>
          <li>Envie de vous recentrer</li>
        </ul>
      </div>
    </section>

    <!-- Mon activité -->
    <section class="section intro" aria-labelledby="intro-title">
      <div class="container intro__inner">
        <div class="intro__media">
          <img class="intro__portrait media shape-arch" src="assets/images/karine-portrait.jpg" alt="Portrait de Karine, énergéticienne" width="768" height="1092" loading="lazy">
          <img class="intro__badge media shape-circle" src="assets/images/accueil-papillon-bleu.jpg" alt="" width="375" height="366" loading="lazy">
        </div>
        <div class="intro__text">
          <h2 class="intro__title" id="intro-title">Mon activité</h2>
          <p>Installée à Carquefou, près de Nantes, je vous accueille dans une salle de soin calme et lumineuse pour des soins énergétiques et des massages sonores aux bols tibétains. La salle de soin est à quelques minutes de Sainte-Luce-sur-Loire, Thouaré-sur-Loire et La Chapelle-sur-Erdre. Je propose aussi des soins à distance, pour les personnes qui ne peuvent pas se déplacer.</p>
          <p>Mon accompagnement repose sur l'écoute, la douceur et la bienveillance. Chaque séance est un moment pour vous, pour relâcher les tensions et retrouver de l'apaisement.</p>
          {arrow_link('qui-suis-je.html', 'Mon parcours')}
        </div>
      </div>
    </section>

    <!-- Soins proposés -->
    <section class="section section--sand" id="soins" aria-labelledby="soins-title">
      <div class="container">
        <div class="section-head">
          <h2 class="section-head__title" id="soins-title">Soins proposés</h2>
          <p class="section-head__lead">À la salle de soin, à Carquefou, ou à distance.</p>
        </div>
        <ul class="care-list">
{care_html}
        </ul>
      </div>
    </section>

    <!-- Bons cadeaux -->
    <section class="section gift" id="bons-cadeaux" aria-labelledby="gift-title">
      <div class="container gift__inner">
        <img class="gift__image media" src="assets/images/salle-table-fenetre.jpg" alt="Table de soin installée près de la fenêtre" width="768" height="513" loading="lazy">
        <div class="gift__text">
          <h2 class="gift__title" id="gift-title">Offrir un bon cadeau</h2>
          <p>Faites plaisir à un proche en lui offrant un moment de détente, pour l'une des prestations proposées.</p>
          <p class="gift__highlight">Les bons cadeaux sont disponibles sur place, à la salle de soin, sans rendez-vous.</p>
          {arrow_link('tarifs.html#bons-cadeaux', 'Voir les tarifs')}
        </div>
      </div>
    </section>

    <!-- Questions fréquentes (aussi déclarées à Google : FAQ_SCHEMA) -->
    <section class="section section--sand faq" aria-labelledby="faq-title">
      <div class="container container--narrow">
        <h2 class="section-head__title faq__title" id="faq-title">Questions fréquentes</h2>
        <div class="faq__list">
{FAQ_HTML}
        </div>
      </div>
    </section>

    <!-- Prise de rendez-vous -->
    <section class="section closing" aria-labelledby="closing-title">
      <div class="container closing__inner">
        <h2 class="closing__title" id="closing-title">Prendre rendez-vous</h2>
        <p class="closing__text">En ligne à tout moment, ou par téléphone au {PHONE}.<br>Accueil uniquement sur rendez-vous, habituellement {HOURS_TEXT}.</p>
        <div class="actions">
          <a class="btn btn--primary" href="{BOOKING_URL}" target="_blank" rel="noopener">Réserver en ligne</a>
          <a class="btn btn--outline" href="{PHONE_HREF}">Appeler</a>
        </div>
      </div>
    </section>
''')

# --------------------------------------------------------------------------- Qui suis-je
page('qui-suis-je.html', 'Karine Eude, énergéticienne à Carquefou | Azurine',
     'Karine, créatrice d\'Azurine, énergéticienne à Carquefou : son parcours, sa formation et sa manière d\'accompagner. Formulaire de contact.',
     f'''
    <section class="about">
      <div class="container about__inner">
        <img class="about__portrait media shape-egg" src="assets/images/karine-portrait.jpg" alt="Portrait de Karine, énergéticienne" width="768" height="1092">

        <div class="about__text">
          <h1 class="about__title">Qui suis-je ?</h1>
          <p>Je suis Karine, créatrice d'Azurine et <strong>énergéticienne à Carquefou</strong>.</p>
          <p>Suite à un problème de santé en 2020, j'ai dû mettre ma vie professionnelle entre parenthèses. Durant ce moment de « pause », je me suis reconnectée au monde qui nous entoure et plus particulièrement aux énergies.</p>
          <p>Curieuse et ayant envie de comprendre mes ressentis, je me suis formée aux soins énergétiques auprès d'une <a href="https://www.seline-magnetiseuse.fr/" target="_blank" rel="noopener">magnétiseuse à Vertou</a>. J'ai également suivi les enseignements de Serge Boutboul, Luc Bodin et Sophie Guedj Mettey.</p>
          <p>Les personnes qui viennent dans ma salle de soin apprécient ma bienveillance, ma douceur et mon écoute. Après une séance, elles se sentent plus légères, libérées. Elles repartent aussi avec des outils pour comprendre leurs maux et avancer.</p>
        </div>

        <div class="about__photos">
          <img class="media" src="assets/images/karine-soin-energetique.jpg" alt="Karine pratiquant un soin énergétique sur une personne allongée" width="375" height="366" loading="lazy">
          <img class="media" src="assets/images/karine-soin-salle.jpg" alt="Karine pratiquant un soin dans la salle de soin" width="375" height="395" loading="lazy">
        </div>
      </div>
    </section>

    <!-- Contact -->
    <section class="section section--sand contact" id="contact" aria-labelledby="contact-title">
      <div class="container contact__inner">
        <div class="contact__intro">
          <h2 class="contact__title" id="contact-title">Me contacter</h2>
          <p>Une question sur les soins, un bon cadeau ou un rendez-vous ? Écrivez-moi avec ce formulaire : je vous réponds rapidement.</p>
          <ul class="contact__details">
            <li><a href="{PHONE_HREF}">{PHONE_ICON}{PHONE_TEXT}</a></li>
            <li><a href="mailto:{EMAIL_TEXT}">{MAIL_ICON}{EMAIL_TEXT}</a></li>
            <li><a href="{INSTAGRAM}" target="_blank" rel="noopener">{INSTA_ICON}azurine_energeticienne</a></li>
          </ul>
        </div>

        <!--
          FORMULAIRE DE CONTACT — Netlify Forms
          Netlify détecte ce formulaire au déploiement (data-netlify="true") et enregistre
          les messages dans l'onglet « Forms » du site. Pour les recevoir par e-mail :
          Site configuration > Forms > Form notifications > Add notification > Email.
          Le champ « bot-field » est un piège à robots : il doit rester vide et caché.
          En local (python -m http.server), l'envoi ne fonctionne pas : c'est normal.
        -->
        <form class="contact-form panel" name="contact" method="POST" action="merci.html" data-netlify="true" netlify-honeypot="bot-field">
          <input type="hidden" name="form-name" value="contact">
          <p class="visually-hidden">
            <label>Ne pas remplir ce champ : <input name="bot-field" tabindex="-1" autocomplete="off"></label>
          </p>

          <div class="contact-form__row">
            <div class="contact-form__field">
              <label class="contact-form__label" for="contact-first-name">Prénom</label>
              <input class="contact-form__input" id="contact-first-name" name="prenom" type="text" autocomplete="given-name" required>
            </div>
            <div class="contact-form__field">
              <label class="contact-form__label" for="contact-last-name">Nom <span class="contact-form__optional">(facultatif)</span></label>
              <input class="contact-form__input" id="contact-last-name" name="nom" type="text" autocomplete="family-name">
            </div>
          </div>
          <div class="contact-form__row">
            <div class="contact-form__field">
              <label class="contact-form__label" for="contact-email">E-mail</label>
              <input class="contact-form__input" id="contact-email" name="email" type="email" autocomplete="email" required>
            </div>
            <div class="contact-form__field">
              <label class="contact-form__label" for="contact-phone">Téléphone <span class="contact-form__optional">(facultatif)</span></label>
              <input class="contact-form__input" id="contact-phone" name="telephone" type="tel" autocomplete="tel">
            </div>
          </div>
          <div class="contact-form__field">
            <label class="contact-form__label" for="contact-message">Message</label>
            <textarea class="contact-form__input" id="contact-message" name="message" required></textarea>
          </div>

          <p class="contact-form__note">Vos informations servent uniquement à répondre à votre message (<a href="confidentialite.html">politique de confidentialité</a>).</p>

          <button class="btn btn--primary" type="submit">Envoyer le message</button>
        </form>
      </div>
    </section>
''')

# --------------------------------------------------------------------------- La salle de soin
# (ancienne page le-cabinet.html, redirigée dans _redirects : la cliente préfère « salle de soin » à « cabinet »)
page('salle-de-soin.html', 'Salle de soin énergétique à Carquefou | Azurine',
     f'La salle de soin d\'Azurine se trouve {ADDRESS}, aux portes de Nantes. Photos de la salle, horaires et plan d\'accès.',
     f'''
{page_head('La salle de soin', f'La salle de soin se trouve au {STREET}, à {CITY}, aux portes de Nantes. C\'est un lieu calme et lumineux, pensé pour que vous vous sentiez en confiance.')}
    <div class="container salle-gallery">
      <figure class="salle-gallery__main">
        <img class="media" src="assets/images/salle-vue-ensemble.jpg" alt="Vue d'ensemble de la salle de soin, avec la table de soin et la bibliothèque" width="768" height="512">
      </figure>
      <figure class="salle-gallery__side">
        <img class="media" src="assets/images/salle-table-fenetre.jpg" alt="Table de soin installée près de la fenêtre" width="768" height="513" loading="lazy">
      </figure>
      <figure class="salle-gallery__small">
        <img class="media" src="assets/images/salle-table-de-soin.jpg" alt="Table de soin recouverte d'un plaid bleu" width="375" height="366" loading="lazy">
        <figcaption>Les soins se font sur la table de soin.</figcaption>
      </figure>
    </div>

    <!-- Plan d'accès : Google Maps n'est chargé qu'après un clic (il dépose des cookies) -->
    <section class="section section--sand access" aria-labelledby="access-title">
      <div class="container access__inner">
        <div class="access__text">
          <h2 class="access__title" id="access-title">Plan d'accès</h2>
          <address class="access__address">{STREET}<br>{POSTCODE} {CITY}</address>
          <p>Accueil uniquement sur rendez-vous, habituellement {HOURS_TEXT}.</p>
          {arrow_link('prendre-rdv.html', 'Prendre rendez-vous')}
        </div>
        <div class="map__frame map__consent" data-map-src="{MAP_EMBED}">
          {MAP_ICON}
          <p>Le plan est fourni par Google Maps, qui dépose des cookies une fois la carte affichée.</p>
          <button class="btn btn--outline btn--small" type="button" data-map-load>Afficher la carte</button>
          <a href="{MAP_LINK}" target="_blank" rel="noopener">Ouvrir dans Google Maps</a>
        </div>
      </div>
    </section>
''')


# --------------------------------------------------------------------------- Pages de soins
def soin_page(filename, title, description, lead, image, paragraphs, facts, extra='', seo_title=None, offers=(), cta=None):
    """cta : bouton principal (par défaut, réservation en ligne)."""
    cta = cta or f'<a class="btn btn--primary" href="{BOOKING_URL}" target="_blank" rel="noopener">Prendre rendez-vous</a>'
    paras = '\n'.join(f'          <p>{p}</p>' for p in paragraphs)
    rows = '\n'.join(f'''            <div class="facts__row"><dt>{k}</dt><dd>{v}</dd></div>''' for k, v in facts)
    service = {
        '@context': 'https://schema.org', '@type': 'Service', 'name': title, 'description': lead,
        'url': f'{SITE_URL}/{filename}', 'areaServed': [{'@type': 'City', 'name': c} for c in AREA],
        'provider': {'@id': SITE_URL + '/#azurine'},
    }
    if offers:
        service['offers'] = [{'@type': 'Offer', 'name': n, 'price': str(pr), 'priceCurrency': 'EUR'} for n, pr in offers]
    page(filename, seo_title or f'{title} | Azurine, énergéticienne à Carquefou', description, schema=(service,), name=title, main=f'''
    <section class="care-page">
      <div class="container care-page__inner">
        <header class="care-page__head">
          <h1 class="page-head__title">{title}</h1>
          <p class="page-head__lead">{lead}</p>
        </header>

        <aside class="care-page__aside" aria-label="Informations pratiques">
          {image}
          <dl class="facts">
{rows}
          </dl>
          <div class="actions">
            {cta}
            {arrow_link('tarifs.html', 'Tous les tarifs')}
          </div>
        </aside>

        <div class="care-page__text prose">
{paras}
{extra}
          <p class="health-note">{HEALTH_NOTE}</p>
        </div>
      </div>
    </section>
''')


# Textes volontairement généraux : le déroulement détaillé des séances (gestes, tenue, conseils,
# façon d'utiliser les bols) reste à valider avec la cliente. Ne rien y ajouter sans son accord.
soin_page('soin-energetique.html', 'Soin énergétique',
          f'Soin énergétique à {CITY}, près de Nantes : {SESSION_TEXT} à la salle de soin, pour un moment de détente et d\'apaisement. '
          f'Adulte {eur(P["energetique"]["adulte"])}, enfant {eur(P["energetique"]["enfant"])}.',
          f'{SESSION_TEXT.capitalize()} à la salle de soin, pour un moment de détente et d\'apaisement, dans une ambiance calme et bienveillante.',
          '<img class="care-page__image media" src="assets/images/karine-soin-energetique.jpg" alt="Karine pratiquant un soin énergétique sur une personne allongée" width="375" height="366">',
          [
              'Le soin énergétique s\'inscrit dans une démarche de bien-être : un moment pour vous, pour relâcher les tensions et retrouver de l\'apaisement. Il peut vous accompagner dans les périodes de stress, de fatigue ou de tension.',
              'Il s\'adresse aux adultes comme aux enfants, sans âge minimum. Pour un mineur, la présence d\'un parent est obligatoire pendant toute la séance.',
              f'Une question sur le déroulement d\'une séance&nbsp;? Appelez-moi au {PHONE} : je vous réponds avec plaisir.',
          ],
          [('Durée', SESSION), ('Lieu', f'Salle de soin, à {CITY}'), ('Adulte', eur(P['energetique']['adulte'])),
           ('Enfant (moins de 16 ans)', eur(P['energetique']['enfant'])),
           ('Mineurs', 'Accompagnés d\'un parent')],
          seo_title='Soin énergétique à Carquefou, près de Nantes | Azurine',
          offers=(('Adulte', P['energetique']['adulte']), ('Enfant de moins de 16 ans', P['energetique']['enfant'])))

soin_page('massage-sonore.html', 'Massage sonore aux bols tibétains',
          f'Massage sonore aux bols tibétains à {CITY}, près de Nantes : {SESSION_TEXT} de détente portée par les sons des bols. '
          f'Adulte {eur(P["sonore"]["adulte"])}, enfant {eur(P["sonore"]["enfant"])}.',
          f'{SESSION_TEXT.capitalize()} de détente, portée par les sons et les vibrations des bols tibétains.',
          '<img class="care-page__image media" src="assets/images/salle-table-de-soin.jpg" alt="Table de soin recouverte d\'un plaid bleu" width="375" height="366">',
          [
              'Le massage sonore utilise les sons et les vibrations des bols tibétains. Ce moment invite à la détente du corps et de l\'esprit, pour relâcher les tensions et retrouver un état de calme.',
              f'Il est proposé aux adultes et aux enfants à partir de {SONORE_MIN_AGE} ans. Pour un mineur, la présence d\'un parent est obligatoire pendant toute la séance.',
              f'Une question sur le déroulement d\'une séance&nbsp;? Appelez-moi au {PHONE}.',
          ],
          [('Durée', SESSION), ('Lieu', f'Salle de soin, à {CITY}'), ('Adulte', eur(P['sonore']['adulte'])),
           ('Enfant (moins de 16 ans)', eur(P['sonore']['enfant'])),
           ('Âge minimum', f'{SONORE_MIN_AGE} ans'), ('Mineurs', 'Accompagnés d\'un parent')],
          seo_title='Massage sonore aux bols tibétains à Carquefou | Azurine',
          offers=(('Adulte', P['sonore']['adulte']), (f'Enfant de {SONORE_MIN_AGE} à 15 ans', P['sonore']['enfant'])),
          # Précautions communiquées par la cliente (liste non exhaustive).
          extra=
f'''          <div class="callout">
            <h2 class="callout__title">Précautions</h2>
            <p>Le massage sonore n'est pas recommandé aux personnes portant un stimulateur cardiaque (pacemaker) ou des tiges métalliques, ni aux personnes épileptiques.</p>
            <p>Un échange par téléphone est nécessaire avant de prendre rendez-vous pour les femmes enceintes, les personnes atteintes d'un cancer et les personnes souffrant de troubles psychiatriques (schizophrénie, troubles bipolaires…). En cas de doute, appelez-moi au {PHONE}.</p>
          </div>''')

soin_page('soin-a-distance.html', 'Soin à distance',
          f'Soin énergétique à distance avec Karine, énergéticienne à {CITY} : un soin depuis chez vous. Renseignements par téléphone au {PHONE_TEXT}.',
          'Un soin énergétique depuis chez vous, quand vous ne pouvez pas vous déplacer.',
          '<img class="care-page__image media" src="assets/images/accueil-mains-lumiere.jpg" alt="Deux mains ouvertes baignées de lumière" width="397" height="302">',
          [
              'Vous ne pouvez pas vous déplacer, vous habitez loin ou vous préférez rester chez vous&nbsp;? Le soin énergétique peut aussi se faire à distance.',
              f'Pour en savoir plus, appelez-moi au {PHONE} : je vous présente les modalités, la durée et le tarif du soin à distance.',
          ],
          [('Lieu', 'Chez vous'), ('Tarif et durée', 'Par téléphone'), ('Renseignements', PHONE)],
          seo_title='Soin énergétique à distance | Azurine, Carquefou',
          cta=f'<a class="btn btn--primary" href="{PHONE_HREF}">Appeler pour en savoir plus</a>')


# --------------------------------------------------------------------------- Tarifs
def price_group(href, name, duration, rows):
    dur = f' <span class="price-group__duration">{duration}</span>' if duration else ''
    lines = '\n'.join(f'''          <p class="price-row"><span class="price-row__label">{l}</span><span class="price-row__price">{p}</span></p>''' for l, p in rows)
    return f'''        <div class="price-group">
          <h2 class="price-group__title"><a href="{href}">{name}</a>{dur}</h2>
{lines}
        </div>'''


page('tarifs.html', 'Tarifs soins énergétiques et massage sonore | Azurine',
     f'Tarifs d\'Azurine : soin énergétique {eur(P["energetique"]["adulte"])} (enfant {eur(P["energetique"]["enfant"])}), '
     f'massage sonore aux bols tibétains {eur(P["sonore"]["adulte"])} (enfant {eur(P["sonore"]["enfant"])}). Bons cadeaux sur place.',
     f'''
{page_head('Tarifs', 'Séances à la salle de soin, à Carquefou, ou à distance.', narrow=True)}
    <section class="pricing">
      <div class="container container--narrow">
        <div class="price-list">
{price_group('soin-energetique.html', 'Soin énergétique', SESSION, [('Adulte', eur(P['energetique']['adulte'])), ('Enfant (moins de 16 ans)', eur(P['energetique']['enfant']))])}
{price_group('massage-sonore.html', 'Massage sonore aux bols tibétains', SESSION, [('Adulte', eur(P['sonore']['adulte'])), (f'Enfant (de {SONORE_MIN_AGE} à 15 ans)', eur(P['sonore']['enfant']))])}
{price_group('soin-a-distance.html', 'Soin à distance', '', [('Tarif et durée', 'Par téléphone')])}
        </div>
        <p class="pricing__note">Pour un mineur, la présence d'un parent est obligatoire pendant la séance. Soin à distance : renseignements au {PHONE}.</p>

        <dl class="facts pricing__facts">
          <div class="facts__row"><dt>Règlement</dt><dd>{PAYMENT}</dd></div>
          <div class="facts__row"><dt>Annulation ou report</dt><dd>{CANCEL}</dd></div>
        </dl>

        <div class="gift-panel" id="bons-cadeaux">
          <h2 class="gift-panel__title">Bons cadeaux</h2>
          <p>Envie de faire plaisir&nbsp;? Offrez à un proche l'une des prestations proposées. Les bons cadeaux sont disponibles sur place, à la salle de soin, sans rendez-vous.</p>
        </div>

        <div class="actions">
          <a class="btn btn--primary" href="prendre-rdv.html">Prendre rendez-vous</a>
          {arrow_link('qui-suis-je.html#contact', 'Poser une question')}
        </div>
      </div>
    </section>
''')

# --------------------------------------------------------------------------- Prendre RDV
page('prendre-rdv.html', 'Prendre rendez-vous | Azurine, énergéticienne à Carquefou',
     f'Prenez rendez-vous avec Azurine, énergéticienne à {CITY}, par téléphone au {PHONE_TEXT} ou en ligne.',
     f'''
{page_head('Prendre rendez-vous', 'Deux possibilités, selon ce qui vous convient le mieux.')}
    <section class="booking">
      <div class="container">
        <div class="booking__options">
          <div class="booking__option panel">
            <h2>En ligne</h2>
            <p>Choisissez votre créneau à tout moment, sur l'agenda en ligne.</p>
            <a class="btn btn--primary" href="{BOOKING_URL}" target="_blank" rel="noopener">Réserver en ligne</a>
          </div>
          <div class="booking__option panel">
            <h2>Par téléphone</h2>
            <a class="booking__phone" href="{PHONE_HREF}">{PHONE_TEXT}</a>
            <p>N'hésitez pas à laisser un message, je vous rappelle.</p>
          </div>
        </div>
        <p class="booking__info">Accueil uniquement sur rendez-vous, habituellement {HOURS_TEXT}. La salle de soin se trouve au {STREET}, à {CITY} (<a href="salle-de-soin.html">voir le plan</a>).</p>
        <dl class="facts booking__facts">
          <div class="facts__row"><dt>Règlement</dt><dd>{PAYMENT}</dd></div>
          <div class="facts__row"><dt>Annulation ou report</dt><dd>{CANCEL}</dd></div>
          <div class="facts__row"><dt>Soin à distance</dt><dd>Par téléphone, au {PHONE}</dd></div>
        </dl>
      </div>
    </section>
''')

# --------------------------------------------------------------------------- Avis
def testimonials_html():
    if not TESTIMONIALS:
        return ''
    items = '\n'.join(f'''          <li class="testimonial">
            <blockquote class="testimonial__quote"><p>{esc(quote)}</p></blockquote>
            <p class="testimonial__author">{esc(author)}</p>
          </li>''' for quote, author in TESTIMONIALS)
    return f'''    <section class="section section--sand" aria-label="Témoignages">
      <div class="container">
        <ul class="testimonials">
{items}
        </ul>
      </div>
    </section>
'''


page('avis.html', 'Avis clients | Azurine, énergéticienne à Carquefou',
     'Avis et témoignages sur les soins d\'Azurine, énergéticienne à Carquefou. Partagez votre expérience.',
     f'''
{page_head('Avis', 'Vous avez reçu un soin à la salle de soin ou à distance ? Votre retour m\'est précieux et aide d\'autres personnes à franchir le pas.', extra=chr(10) + f'          <div class="actions"><a class="btn btn--primary" href="{GOOGLE_REVIEW}" target="_blank" rel="noopener">Laisser un avis sur Google</a>' + arrow_link('qui-suis-je.html#contact', 'Ou m\'écrire directement') + '</div>')}
{testimonials_html()}''')


# --------------------------------------------------------------------------- Pages légales
def legal_page(filename, title, description, body):
    page(filename, f'{title} | Azurine', description, f'''
{page_head(title, extra=chr(10) + f'          <p class="legal__updated">Dernière mise à jour : 8 octobre {YEAR}</p>')}
    <section class="legal">
      <div class="container prose">
{body}
      </div>
    </section>
''')


legal_page('mentions-legales.html', 'Mentions légales',
           'Mentions légales du site d\'Azurine, énergéticienne à Carquefou : éditeur, hébergeur, propriété intellectuelle.',
           f'''        <h2>Éditeur du site</h2>
        <p>
          Le présent site, accessible à l'adresse <a href="https://azurine.fr">azurine.fr</a>, est édité par l'association AZURINE,
          association à but non lucratif régie par la loi du 1<sup>er</sup> juillet 1901, déclarée à la préfecture de la Loire-Atlantique le 28 novembre 2023
          (Journal officiel des associations et fondations d'entreprise du 5 décembre 2023, annonce n° 1104).
        </p>
        <ul>
          <li>Siège social : 18 rue de la Salle, 44470 Carquefou</li>
          <li>Numéro RNA : W442028955</li>
          <li>Téléphone : {PHONE}</li>
          <li>E-mail : {EMAIL}</li>
        </ul>
        <p>Directrice de la publication : Karine Eude, présidente de l'association.</p>
        <p>
          Objet de l'association : promotion et diffusion des techniques énergétiques de bien-être physique, émotionnel et mental,
          afin de les rendre accessibles à tous.
        </p>
        <p>
          Les sommes perçues pour les prestations servent au fonctionnement de l'association, notamment à l'achat de matériel,
          à la location de salles et aux formations.
        </p>

        <h2>Hébergement</h2>
        <p>
          Le site est hébergé par Netlify, Inc., 512 2nd Street, Suite 200, San Francisco, CA 94107, États-Unis
          (<a href="https://www.netlify.com" target="_blank" rel="noopener">www.netlify.com</a>).
        </p>

        <h2>Nature des prestations proposées</h2>
        <p>
          {HEALTH_NOTE}
        </p>
        <p>
          Les situations évoquées sur le site décrivent des moments de vie dans lesquels une séance peut être proposée en accompagnement.
          Elles ne constituent pas une promesse de résultat.
        </p>

        <h2>Propriété intellectuelle</h2>
        <p>
          Les textes, photographies, logos et éléments graphiques de ce site sont la propriété de l'association éditrice,
          sauf mention contraire. Toute reproduction ou réutilisation, totale ou partielle, sans autorisation écrite préalable est interdite.
        </p>
        <p>
          Les polices de caractères Playfair Display et Source Sans 3 sont utilisées sous licence SIL Open Font License.
        </p>

        <h2>Liens externes</h2>
        <p>
          Le site contient des liens vers des services tiers : {BOOKING['name']} (prise de rendez-vous en ligne), Instagram, Google Maps et Google (dépôt d'avis).
          L'association n'est pas responsable du contenu ni des pratiques de ces services, soumis à leurs propres conditions d'utilisation.
        </p>

        <h2>Données personnelles</h2>
        <p>
          Le traitement des données personnelles et l'usage des cookies sont décrits dans la
          <a href="confidentialite.html">politique de confidentialité</a>.
        </p>

        <h2>Droit applicable</h2>
        <p>Le présent site et ses mentions légales sont soumis au droit français.</p>''')

legal_page('confidentialite.html', 'Politique de confidentialité',
           'Politique de confidentialité du site d\'Azurine : données collectées, finalités, durée de conservation, cookies et droits RGPD.',
           f'''        <p class="prose__lead">
          Cette page explique quelles données personnelles sont collectées sur ce site, pourquoi, combien de temps elles sont conservées
          et comment exercer vos droits, conformément au Règlement général sur la protection des données (RGPD) et à la loi Informatique et Libertés.
        </p>

        <h2>Responsable du traitement</h2>
        <p>
          L'association AZURINE (RNA W442028955), dont le siège est situé 18 rue de la Salle, 44470 Carquefou,
          joignable à {EMAIL} ou au {PHONE}.
        </p>

        <h2>Données collectées et finalités</h2>
        <h3>Formulaire de contact</h3>
        <p>
          Lorsque vous utilisez le formulaire de contact, nous recevons votre prénom, votre adresse e-mail, votre message et,
          si vous choisissez de les indiquer, votre nom et votre numéro de téléphone.
        </p>
        <ul>
          <li>Finalité : répondre à votre demande (information, rendez-vous, bon cadeau).</li>
          <li>Base légale : votre demande et l'intérêt légitime de l'association à y répondre.</li>
          <li>Durée de conservation : le temps nécessaire au traitement de votre demande, puis au plus 3 ans après notre dernier échange.</li>
        </ul>
        <p>
          Merci de ne pas transmettre d'informations de santé détaillées par le formulaire : nous pourrons en parler de vive voix lors du rendez-vous.
        </p>

        <h3>Prise de rendez-vous en ligne</h3>
        <p>
          La prise de rendez-vous en ligne s'effectue sur le site de {BOOKING['name']} ({BOOKING['company']}, États-Unis), vers lequel les boutons de réservation vous redirigent.
          Les informations saisies (nom, e-mail, créneau choisi) sont traitées par {BOOKING['name']} pour le compte de l'association,
          selon <a href="{BOOKING['privacy']}" target="_blank" rel="noopener">sa politique de confidentialité</a>.
        </p>

        <h3>Données techniques</h3>
        <p>
          Comme tout hébergeur, Netlify enregistre automatiquement des données techniques de connexion (adresse IP, date, page demandée, navigateur)
          afin d'assurer la sécurité et le bon fonctionnement du site. Ces données ne sont pas utilisées par l'association à d'autres fins.
        </p>

        <h2>Destinataires et sous-traitants</h2>
        <p>
          Vos données sont destinées uniquement à l'association. Elles ne sont ni vendues, ni louées, ni cédées.
          Elles transitent par les prestataires techniques suivants :
        </p>
        <ul>
          <li>Netlify, Inc. (hébergement du site et réception des messages du formulaire) ;</li>
          <li>{BOOKING['company']} (prise de rendez-vous en ligne) ;</li>
          <li>OVH SAS, 2 rue Kellermann, 59100 Roubaix, France (messagerie de l'adresse contact@azurine.fr).</li>
        </ul>
        <p>
          Netlify et {BOOKING['name']} sont situés aux États-Unis. Ces transferts de données sont encadrés par le cadre de protection des données UE–États-Unis
          (Data Privacy Framework) ou par les clauses contractuelles types de la Commission européenne. La messagerie OVH est hébergée dans l'Union européenne.
        </p>

        <h2>Cookies</h2>
        <p>
          Ce site ne dépose aucun cookie de mesure d'audience ni de publicité, et n'utilise aucun outil de suivi.
          Les polices de caractères sont hébergées sur le site lui-même.
        </p>
        <p>
          Le plan de la page « La salle de soin » est fourni par Google Maps. Il n'est chargé que si vous cliquez sur « Afficher la carte » :
          Google peut alors déposer des cookies, selon <a href="https://policies.google.com/privacy?hl=fr" target="_blank" rel="noopener">sa politique de confidentialité</a>.
          Sans ce clic, aucune donnée n'est transmise à Google.
        </p>

        <h2>Vos droits</h2>
        <p>
          Vous disposez d'un droit d'accès, de rectification, d'effacement, de limitation et de portabilité de vos données,
          ainsi que d'un droit d'opposition à leur traitement. Pour les exercer, écrivez à {EMAIL}. Nous vous répondrons dans un délai d'un mois.
        </p>
        <p>
          Si vous estimez que vos droits ne sont pas respectés, vous pouvez adresser une réclamation à la CNIL
          (<a href="https://www.cnil.fr" target="_blank" rel="noopener">www.cnil.fr</a>, 3 place de Fontenoy, TSA 80715, 75334 Paris Cedex 07).
        </p>''')

# --------------------------------------------------------------------------- Merci / 404
BACK_HOME = chr(10) + '          <div class="actions"><a class="btn btn--primary" href="index.html">Retour à l\'accueil</a></div>'
page('merci.html', 'Message envoyé | Azurine', 'Votre message a bien été envoyé à Azurine.',
     page_head('Merci !', 'Votre message a bien été envoyé. Je vous réponds dans les meilleurs délais.', center=True, extra=BACK_HOME),
     current='', noindex=True)

page('404.html', 'Page introuvable | Azurine', 'Cette page n\'existe pas ou a été déplacée.',
     page_head('Page introuvable', 'Cette page n\'existe pas ou a été déplacée.', center=True, extra=BACK_HOME),
     current='', noindex=True, root='/')

# --------------------------------------------------------------------------- Référencement
urls = '\n'.join(f'  <url><loc>{SITE_URL}/{"" if f == "index.html" else f}</loc><lastmod>{LASTMOD}</lastmod></url>' for f in INDEXED)
(SITE / 'sitemap.xml').write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
''', encoding='utf-8')
(SITE / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n', encoding='utf-8')

print('ok')

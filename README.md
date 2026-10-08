# Azurine — site statique

Site vitrine d'Azurine, énergéticienne à Carquefou.
HTML, CSS et JavaScript « vanilla », générés par un script Python sans dépendance.

## Fonctionnement

Le site est **généré** : on ne modifie jamais les pages HTML à la main.

```
infos.toml    informations modifiables par la cliente : tarifs, horaires, coordonnées,
              lien de réservation, questions fréquentes, avis
build.py      générateur : structure et textes des pages ; vérifie infos.toml
static/       fichiers copiés tels quels (assets/, favicon.ico, site.webmanifest,
              _redirects, _headers)
public/       site généré (non versionné) : c'est ce dossier que Netlify publie
netlify.toml  commande de génération et dossier publié, version de Python
sources/      fichiers sources non publiés (icône du site en 512 px)
```

À chaque push sur `main`, Netlify lance `python3 -I build.py` puis publie `public/`.
Si `infos.toml` contient une erreur, la génération s'arrête avec un message en français
et **la version précédente reste en ligne**.

La même génération tourne dans GitHub Actions (`.github/workflows/verification.yml`,
gratuit) : en cas d'erreur, croix rouge à côté du commit et e-mail de GitHub à son auteur,
avec le message dans le détail de la vérification. (Les e-mails d'échec de Netlify sont
payants.)

## Modifier le site

- **Tarif, horaire, coordonnées, question fréquente, avis** : modifier `infos.toml`
  (sur GitHub : ouvrir le fichier, crayon « Edit this file », « Commit changes »).
  Le mode d'emploi est en tête du fichier.
- **Texte d'une page, menu, pied de page** : `build.py` (une section par page ;
  menu dans `NAV` / `SOINS`, pied de page dans `footer()`).
- **Styles, scripts, images** : `static/assets/`.

## Prévisualiser en local

Python 3.11 ou plus récent, aucune dépendance :

```bash
python3 -I build.py                       # génère public/
python3 -m http.server 8080 -d public     # puis http://localhost:8080/
```

Le formulaire de contact (Netlify Forms) ne fonctionne qu'une fois en ligne.

## Organisation de `public/` (généré)

```
index.html                 Accueil (activité, soins, bons cadeaux, FAQ, prise de RDV)
qui-suis-je.html           Présentation + formulaire de contact (Netlify Forms)
salle-de-soin.html         Photos de la salle de soin, horaires, plan Google Maps chargé au clic
soin-energetique.html      ┐
massage-sonore.html        ├ menu « Soins proposés »
soin-a-distance.html       ┘
tarifs.html                Tarifs, règlement, annulation, bons cadeaux (#bons-cadeaux)
prendre-rdv.html           Réservation en ligne (Cal.com) ou par téléphone
avis.html                  Lien vers les avis Google ; témoignages ([[avis]] de infos.toml)
mentions-legales.html      ┐ pages légales
confidentialite.html       ┘
merci.html                 Page affichée après l'envoi du formulaire
404.html                   Page d'erreur Netlify (chemins absolus /assets/…)
sitemap.xml, robots.txt    lastmod = date du dernier commit
```

`static/assets/` :

```
css/
  variables.css    couleurs, échelle typographique fluide, espacements, formes
  base.css         polices locales, remise à zéro, utilitaires
  layout.css       conteneur, grille 12 colonnes, en-tête, menu, pied de page
  components.css   boutons, photos et formes, titres, fiche pratique, encarts, formulaire
  pages.css        styles propres à chaque page (sommaire en tête de fichier)
js/main.js         menu mobile, sous-menu, carte Google Maps chargée au clic
icons/             icônes du site (papillon du logo) : 192, 512 px et apple-touch-icon
images/            photos nommées par page (accueil-, karine-, salle-) ; partage-azurine.jpg
                   = image d'aperçu 1200 × 630 pour les réseaux sociaux
fonts/             Playfair Display et Source Sans 3 (woff2 variables, normal + italique)
```

## Conventions

- **CSS** : jetons de `variables.css` plutôt que des valeurs en dur ; nommage BEM ;
  « mobile d'abord », un seul point d'arrêt à 921 px (`@media (min-width: 921px)` = desktop).
- **Photos** : classe `media` (coins arrondis). Formes organiques `shape-egg`, `shape-organic`,
  `shape-circle`, `shape-arch` réservées à quelques photos clés. Plusieurs photos ne font que
  375 px de large : ne pas les afficher plus grand tant que les originaux HD ne sont pas fournis.
- **Vocabulaire** : registre du bien-être (« salle de soin », « séance », « accompagner ») ;
  aucune maladie ni promesse de résultat.
- **Services externes** : Cal.com, Google Maps (au clic), Instagram, Netlify Forms. Tout nouveau
  service doit être ajouté à `EXTERNAL-ASSETS.txt` et à la politique de confidentialité.

## Mise en ligne

| Élément | Où | Compte |
|---|---|---|
| Code source | GitHub `AzurineWeb/azurine` (privé), branche `main` | organisation AzurineWeb |
| Hébergement | Netlify, déploiement automatique à chaque push sur `main` | compte Netlify de la cliente |
| Domaine `azurine.fr` + boîte `contact@azurine.fr` | OVH (zone DNS gérée chez OVH) | compte OVH de la cliente |
| Réservation en ligne | Cal.com (`cal.com/azurine`) | compte de la cliente |

**Netlify** : commande `python3 -I build.py`, dossier publié `public/`, Python 3.12 (tout est dans `netlify.toml`, prioritaire sur l'interface).
L'application GitHub de Netlify n'a accès qu'au dépôt `azurine` (« Only select repositories »).

- **Formulaire de contact** : détecté automatiquement (`data-netlify="true"` dans
  `qui-suis-je.html`). Notification vers `contact@azurine.fr` : *Project configuration > Forms >
  Form notifications > Email notification*.
- **Domaine** : la zone DNS reste chez OVH (pour ne pas toucher aux enregistrements de la
  messagerie). `azurine.fr` pointe vers Netlify par un enregistrement **A** et `www.azurine.fr`
  par un **CNAME** vers `<site>.netlify.app`. Les enregistrements **MX / SPF** d'OVH ne doivent
  pas être modifiés. Le domaine principal est `azurine.fr` (sans www) : il est défini par
  `SITE_URL` dans `build.py` (balises `canonical` / `og:`, `sitemap.xml`, `robots.txt`).

# Azurine — site statique

Site vitrine d'Azurine, énergéticienne à Carquefou.
HTML, CSS et JavaScript « vanilla » : aucun framework, aucune dépendance, aucune étape de build côté hébergeur.

## Lancer le site

```bash
python -m http.server 8080
```

Puis ouvrir <http://localhost:8080/>. L'extension VS Code **Live Server** fonctionne aussi.
Le formulaire de contact (Netlify Forms) ne fonctionne qu'une fois en ligne.

## Modifier le site

Les pages HTML sont **générées** par `build.py`, conservé hors du dépôt (dossier voisin `../outils/`,
pour qu'il ne soit pas publié). Une modification faite directement dans un `.html` serait écrasée
à la prochaine génération.

1. Ouvrir `../outils/build.py`.
2. Pour une information courante (tarif, horaire, téléphone, adresse, lien de réservation,
   question fréquente, avis), modifier le bloc **« INFORMATIONS À METTRE À JOUR »** en tête du
   fichier : chaque information y est écrite une seule fois et reprise partout (pages, FAQ,
   données lues par Google).
3. Pour un texte de page, chercher la page dans le reste du fichier (une section par page).
4. Régénérer, vérifier, publier :

```bash
cd ../outils && python3 -I build.py ../azurine-clean
cd ../azurine-clean && git status   # ne doit montrer que les changements voulus
```

Penser à mettre à jour `LASTMOD` (date déclarée à Google) à chaque mise en ligne de contenu.

## Organisation

```
index.html                 Accueil (activité, soins, bons cadeaux, FAQ, prise de RDV)
qui-suis-je.html           Présentation + formulaire de contact (Netlify Forms)
salle-de-soin.html         Photos de la salle de soin, horaires, plan Google Maps chargé au clic
soin-energetique.html      ┐
massage-sonore.html        ├ menu « Soins proposés »
soin-a-distance.html       ┘
tarifs.html                Tarifs, règlement, annulation, bons cadeaux (#bons-cadeaux)
prendre-rdv.html           Réservation en ligne (Cal.com) ou par téléphone
avis.html                  Lien vers les avis Google ; témoignages (liste TESTIMONIALS de build.py)
mentions-legales.html      ┐ pages légales
confidentialite.html       ┘
merci.html                 Page affichée après l'envoi du formulaire
404.html                   Page d'erreur Netlify (chemins absolus /assets/…)
favicon.ico, site.webmanifest   Icône du site (onglet, résultats Google, écran d'accueil)
sitemap.xml, robots.txt    Générés par build.py
_redirects, _headers       Configuration Netlify (anciennes adresses → nouvelles pages, sécurité)
assets/
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

**Netlify** : pas de commande de build, dossier de publication = racine du dépôt.
L'application GitHub de Netlify n'a accès qu'au dépôt `azurine` (« Only select repositories »).

- **Formulaire de contact** : détecté automatiquement (`data-netlify="true"` dans
  `qui-suis-je.html`). Notification vers `contact@azurine.fr` : *Project configuration > Forms >
  Form notifications > Email notification*.
- **Domaine** : la zone DNS reste chez OVH (pour ne pas toucher aux enregistrements de la
  messagerie). `azurine.fr` pointe vers Netlify par un enregistrement **A** et `www.azurine.fr`
  par un **CNAME** vers `<site>.netlify.app`. Les enregistrements **MX / SPF** d'OVH ne doivent
  pas être modifiés. Le domaine principal est `azurine.fr` (sans www) : il est défini par
  `SITE_URL` dans `build.py` (balises `canonical` / `og:`, `sitemap.xml`, `robots.txt`).

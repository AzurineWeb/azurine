# Azurine — site statique

Site vitrine d'Azurine, énergéticienne à Carquefou.
HTML, CSS et JavaScript « vanilla » : aucun framework, aucune dépendance, aucune étape de build.

## Lancer le site

```bash
python -m http.server 8080
```

Puis ouvrir <http://localhost:8080/>. L'extension VS Code **Live Server** fonctionne aussi.

## Organisation

```
index.html                 Accueil (activité, soins, bons cadeaux, prise de RDV)
qui-suis-je.html           Présentation + formulaire de contact (Netlify Forms)
le-cabinet.html            Photos du cabinet + plan Google Maps chargé au clic
soin-energetique.html      ┐
massage-sonore.html        ├ menu « Soins proposés »
soin-a-distance.html       ┘
tarifs.html                Tarifs + bons cadeaux (#bons-cadeaux)
prendre-rdv.html
avis.html                  Invitation à laisser un avis (modèle de témoignages en commentaire)
mentions-legales.html      ┐ pages légales (champs [À COMPLÉTER] surlignés en jaune)
confidentialite.html       ┘
merci.html                 Page affichée après l'envoi du formulaire
404.html                   Page d'erreur Netlify (chemins absolus /assets/…)
_redirects, _headers       Configuration Netlify (anciennes adresses → nouvelles pages)
assets/
  css/
    variables.css    couleurs, échelle typographique fluide, espacements, formes
    base.css         polices locales, remise à zéro, utilitaires
    layout.css       conteneur, grille 12 colonnes, en-tête, menu, pied de page
    components.css   boutons, formes d'images, titres, bandeaux, formulaire, .todo
    pages.css        styles propres à chaque page (sommaire en tête de fichier)
  js/main.js         menu mobile, sous-menu, carte Google Maps chargée au clic
  images/            images nommées par page (accueil-, karine-, cabinet-)
  fonts/             Playfair Display et Source Sans 3 (woff2 variables, normal + italique)
```

## Modifier le site

- **Textes** : directement dans les fichiers `.html`.
- **Couleurs, polices, tailles** : `assets/css/variables.css`.
- **Menu et pied de page** : ils sont recopiés à l'identique dans chaque page
  (blocs balisés `En-tête` et `Pied de page`). Pour ajouter un lien, le faire
  dans toutes les pages ; la page courante est marquée par `aria-current="page"`
  (et `is-current` sur « Soins proposés » pour les pages de soins).
- **Responsive** : écrit « mobile d'abord », un seul point d'arrêt à 921 px
  (`@media (min-width: 921px)` = desktop).
- **Photos** : classe `media` (coins arrondis). Formes organiques `shape-egg`,
  `shape-organic`, `shape-circle`, `shape-arch` réservées à quelques photos clés.
- **Tailles de texte** : fluides (`--step-*` dans `variables.css`), pas besoin de media query.

## Mise en ligne (Netlify)

Déposer le dossier sur Netlify (glisser-déposer sur app.netlify.com ou dépôt Git) : aucune
commande de build, dossier de publication = racine du site.

- **Formulaire de contact** : détecté automatiquement (`data-netlify="true"` dans
  `qui-suis-je.html`). Pour recevoir les messages par e-mail : *Site configuration > Forms >
  Form notifications > Email*. En local, l'envoi ne fonctionne pas : c'est normal.
- **Nom de domaine** : *Domain management*. Penser à mettre à jour les mentions légales si
  l'hébergeur change.

## Pages légales

`mentions-legales.html` et `confidentialite.html` sont rédigées pour une association. Les
informations manquantes (nom officiel, siège, RNA, SIRET, président·e) sont marquées
`<mark class="todo">[À COMPLÉTER : …]</mark>` : chercher « À COMPLÉTER » avant la mise en ligne.
Le site ne dépose aucun cookie ; Google Maps n'est chargé qu'après un clic sur « Afficher la carte ».

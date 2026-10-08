# Azurine — site internet

Site vitrine d'Azurine, énergéticienne à Carquefou : https://azurine.fr

Le site est fait de pages HTML et de feuilles de style CSS, sans outil ni étape de génération :
ce qui est dans le dossier `site/` est exactement ce qui est mis en ligne.

## Organisation

```
site/                      LE SITE (seul dossier mis en ligne)
  index.html               Accueil : présentation, soins, bons cadeaux, questions fréquentes
  qui-suis-je.html         Présentation de Karine + formulaire de contact
  salle-de-soin.html       Photos de la salle de soin + plan d'accès
  soin-energetique.html    ┐
  massage-sonore.html      ├ pages des soins
  soin-a-distance.html     ┘
  tarifs.html              Tarifs, règlement, bons cadeaux
  prendre-rdv.html         Réservation en ligne, téléphone, horaires, annulation
  avis.html                Lien vers les avis Google (+ modèle de témoignages)
  mentions-legales.html    ┐ pages légales
  confidentialite.html     ┘
  merci.html               Page affichée après l'envoi du formulaire
  404.html                 Page « introuvable »
  assets/                  CSS, JavaScript, polices, images, icônes
  favicon.ico, site.webmanifest, sitemap.xml, robots.txt, _redirects, _headers
sources/                   Fichiers de travail non publiés (icône en grand format)
netlify.toml               Réglage Netlify : publier le dossier site/
```

## Modifier le site

### 1. Ouvrir le projet

Dans VS Code : *Fichier → Ouvrir le dossier…* et choisir le dossier du dépôt (celui qui
contient `site/`). Au premier lancement, VS Code propose d'installer l'extension
**Live Server** : accepter.

### 2. Modifier et vérifier

1. Ouvrir la page dans `site/` (voir le tableau ci-dessous) et modifier le texte.
   Ne changer que le texte entre les balises, pas ce qui est entre `<` et `>`.
2. Enregistrer (`Ctrl+S`).
3. Cliquer sur **Go Live** en bas à droite de VS Code : le site s'ouvre dans le navigateur
   et se met à jour à chaque enregistrement. Vérifier la page sur ordinateur, puis en
   réduisant la fenêtre (affichage téléphone).

Le formulaire de contact ne fonctionne qu'une fois en ligne : c'est normal.

### 3. Publier

1. Dans VS Code, ouvrir l'onglet **Contrôle de code source** (icône à gauche, ou `Ctrl+Maj+G`).
2. Écrire un court message (par exemple « Nouveau tarif du massage sonore »).
3. Cliquer sur **Valider** (*Commit*), puis sur **Synchroniser les modifications** (*Sync* / *Push*).
4. Le site est en ligne environ une minute plus tard (Netlify publie automatiquement).

**Regrouper les modifications.** Chaque publication coûte 15 crédits Netlify, et l'offre gratuite
en compte 300 par mois, soit une vingtaine de publications. Faire toutes ses modifications,
les vérifier avec Live Server, puis publier une seule fois. On peut faire plusieurs *Valider*
(commits) et un seul *Synchroniser* à la fin : c'est le *Synchroniser* qui publie. Une
modification qui ne touche pas le dossier `site/` (ce README par exemple) n'est pas publiée
et ne coûte rien.
Netlify envoie un e-mail à 50 % puis à 100 % des crédits du mois.

## Où modifier quoi

Chaque information est écrite le moins souvent possible. Quand elle figure à plusieurs
endroits, un commentaire `<!-- … -->` dans le code le rappelle.

| Pour changer… | Fichier(s) dans `site/` |
|---|---|
| Un **prix** | `tarifs.html` **et** la page du soin (`soin-energetique.html` ou `massage-sonore.html`) |
| Les **horaires** | `prendre-rdv.html` (seul endroit) + la fiche Google |
| Les conditions d'**annulation** | `prendre-rdv.html` (seul endroit) |
| Les modes de **règlement** | `tarifs.html` (seul endroit) |
| Le lien de **réservation en ligne** (Cal.com) | `prendre-rdv.html` (seul endroit) ; si l'outil change, aussi `confidentialite.html` et `mentions-legales.html` |
| Les **questions fréquentes** | `index.html`, section « Questions fréquentes » (un bloc `<details>` par question) |
| Un **avis** | `avis.html` : mode d'emploi en commentaire dans la page |
| Le **texte d'un soin** | la page du soin |
| La **présentation de Karine** | `qui-suis-je.html` |
| Le **téléphone**, l'**e-mail**, l'**adresse** | toutes les pages (pied de page) : utiliser *Édition → Remplacer dans les fichiers* (`Ctrl+Maj+H`) ; aussi les informations pour Google en haut de `index.html` |
| Le **menu** | toutes les pages (en-tête) |
| Une **photo** | remplacer le fichier dans `site/assets/images/` en gardant **exactement le même nom** (JPG, environ 1200 px de large, moins de 300 Ko) |
| Le titre et la description d'une page **dans Google** | les lignes `<title>` et `<meta name="description">` en haut de la page |

À ne pas modifier sans connaître le CSS : `site/assets/css/` (couleurs, polices, mise en page).

## Revenir en arrière

Rien n'est perdu : GitHub garde toutes les versions de chaque fichier.

- **Avant de publier** (modification pas encore validée) : dans *Contrôle de code source*,
  survoler le fichier puis cliquer sur la flèche **Ignorer les modifications** (*Discard Changes*) :
  le fichier revient à sa dernière version publiée.
- **Après publication** : sur GitHub, ouvrir le fichier et cliquer sur
  **History** (historique). Chaque ligne est une version, avec sa date et son message.
  Sur la version voulue, cliquer sur l'icône **`<>`** (*Browse repository at this point*),
  rouvrir le fichier, puis copier son contenu (bouton **Copy raw file**). Le recoller dans
  VS Code, vérifier avec Live Server, puis publier.

Pour un développeur : `git revert <commit>` annule proprement une publication.

## Conventions du code

- **CSS** chargé dans cet ordre : `variables.css` (couleurs, tailles, espacements),
  `base.css`, `layout.css` (grille, en-tête, pied de page), `components.css` (boutons,
  photos, fiches, encarts, formulaire), `pages.css` (styles propres à chaque page, sommaire en
  tête). Écrit « mobile d'abord », un seul point de rupture à 921 px, tailles fluides (`clamp`).
- **Nommage BEM** : `.bloc__element--variante`.
- **En-tête et pied de page** identiques sur les 13 pages, entre des commentaires bien visibles.
  Seule différence : `aria-current="page"` sur le lien de la page affichée.
- `404.html` utilise des chemins absolus (`/assets/…`) car Netlify l'affiche à n'importe
  quelle adresse.
- **Vocabulaire du bien-être** : « salle de soin », « séance », « accompagner » ; aucune maladie
  ni promesse de résultat. Avertissement santé sur l'accueil et les 3 pages de soins.
- **Services externes** : Cal.com (simple lien), Google Maps (chargé au clic), Instagram,
  Netlify Forms. Tout nouveau service doit être ajouté à `EXTERNAL-ASSETS.txt` et à la politique
  de confidentialité.

## Mise en ligne

| Élément | Où | Compte |
|---|---|---|
| Code source | GitHub `AzurineWeb/azurine` (privé), branche `main` | organisation AzurineWeb |
| Hébergement | Netlify, publication automatique à chaque push sur `main` (dossier `site/`, voir `netlify.toml`) | compte Netlify de la cliente |
| Domaine `azurine.fr` + boîte `contact@azurine.fr` | OVH (zone DNS gérée chez OVH) | compte OVH de la cliente |
| Réservation en ligne | Cal.com (`cal.com/azurine`) | compte de la cliente |

- **Formulaire de contact** : Netlify Forms (`data-netlify="true"` dans `qui-suis-je.html`),
  notification vers `contact@azurine.fr`.
- **Domaine** : `azurine.fr` pointe vers Netlify (enregistrement A), `www.azurine.fr` par un
  CNAME. Ne pas modifier les enregistrements MX / SPF d'OVH (messagerie).
- **Anciennes adresses** (ancien site Hostinger, `le-cabinet.html`) : redirigées par `site/_redirects`.

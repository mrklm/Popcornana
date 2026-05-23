# Changelog

Toutes les modifications notables de Popcornana sont documentées ici.

Le projet suit une logique de versionnement sémantique: `MAJEUR.MINEUR.CORRECTIF`.

## [1.0.60] - 2026-05-23

- Création automatique des fichiers portables `cover.*` et `Popinfo.txt` dans le dossier du film après enrichissement ou édition d'une fiche, sans écraser les fichiers déjà présents.

## [1.0.59] - 2026-05-23

- Remplacement de `Choisir dossier` par `Ajouter dossier` pour permettre plusieurs sources de médiathèque.
- Ajout d'une fenêtre `Gérer les sources` permettant de voir les sources disponibles ou absentes et de retirer celles qui ne doivent plus être suivies.
- Le scan parcourt désormais les sources disponibles sans supprimer les fiches des disques absents, qui restent cachées tant que la source n'est pas reconnectée.

## [1.0.58] - 2026-05-23

- Agrandissement de la hauteur du zoom fiche et réduction de la hauteur des boutons d'action.

## [1.0.57] - 2026-05-23

- Correction de l'authentification utilisée pour publier automatiquement les releases GitHub.

## [1.0.56] - 2026-05-23

- Ajout d'une marge dans les résumés du zoom fiche pour éviter que la barre de défilement masque des lettres.
- Publication automatique d'une release GitHub après chaque build multi-OS réussi.

## [1.0.55] - 2026-05-23

- Déclenchement automatique du build multi-OS lors des pushes sur la branche `main`.

## [1.0.54] - 2026-05-23

- Réduction de l'espace vide entre le titre et les informations dans le zoom fiche.

## [1.0.53] - 2026-05-23

- Extension des boutons du zoom fiche sur toute la largeur disponible pour rendre les actions plus visibles.

## [1.0.52] - 2026-05-23

- Suppression de la mention `MANUEL` dans les fiches tout en conservant leur protection contre les enrichissements automatiques.
- Ouverture du choix d'affiche manuelle directement dans le dossier du film édité.

## [1.0.51] - 2026-05-23

- Agrandissement des boutons du zoom fiche pour faciliter les actions `Retour à la liste` et `Visionner`.

## [1.0.50] - 2026-05-23

- Linux: correction du placement initial des vignettes de la médiathèque en recalculant la grille à l'ouverture et au redimensionnement de la fenêtre.
- Windows: amélioration de la détection de VLC en recherchant aussi `vlc.exe` dans les dossiers d'installation classiques afin de fiabiliser le lancement en plein écran.

## [1.0.49] - 2026-05-23

- Linux: stabilisation du placement des vignettes de la médiathèque après actualisation en forçant le flux gauche-droite et un relayout explicite de la grille.

## [1.0.48] - 2026-05-23

- Linux: le scan ignore désormais les fichiers artefacts `._*`, `.DS_Store` et `Thumbs.db` pour éviter les doublons fantômes dans la médiathèque.
- Le rafraîchissement nettoie aussi les anciennes entrées parasites déjà présentes dans la base locale.

## [1.0.47] - 2026-05-22

- Conservation des boutons de fenêtre natifs sous Windows et Linux en ouvrant l'application maximisée plutôt qu'en plein écran exclusif.

## [1.0.46] - 2026-05-22

- Correction du débordement des titres longs dans le zoom fiche pour éviter tout empiètement sur l'affiche.

## [1.0.45] - 2026-05-22

- Réduction de l'affiche dans le zoom fiche pour privilégier la lisibilité du texte.

## [1.0.44] - 2026-05-22

- Ajout d'un défilement dédié aux titres longs dans le zoom fiche pour éviter tout chevauchement avec l'affiche.

## [1.0.43] - 2026-05-22

- Ouverture du zoom fiche au double-clic et meilleur espacement des titres longs dans la grille.

## [1.0.42] - 2026-05-22

- Forçage des polices du zoom fiche pour garantir une meilleure lisibilité sous macOS Catalina.

## [1.0.41] - 2026-05-22

- Ajout d'une section développeurs dans l'aide intégrée avec les détails d'architecture du code.

## [1.0.40] - 2026-05-22

- Mise à jour du README et de l'aide intégrée pour documenter les derniers usages de la médiathèque.

## [1.0.39] - 2026-05-22

- Agrandissement du zoom fiche pour améliorer la lisibilité des titres, résumés et actions.

## [1.0.38] - 2026-05-22

- Correction du tri alphabétique commun entre films et dossiers de films.

## [1.0.37] - 2026-05-22

- Ajout d'un défilement dans le zoom fiche pour préserver l'affiche et les boutons avec les longs résumés.

## [1.0.36] - 2026-05-22

- Francisation du type de média affiché dans les fiches avec `Film` au lieu de `MOVIE`.

## [1.0.35] - 2026-05-21

- Rétablissement du lancement VLC en plein écran pour le visionnage des vidéos.

## [1.0.34] - 2026-05-21

- Ajout d'un visuel dédié pour les dossiers de films sans modifier les fiches des films contenus.

## [1.0.33] - 2026-05-21

- Simplification des dossiers de films en entrées de navigation affichant la liste des films sans modifier leurs fiches.

## [1.0.32] - 2026-05-21

- Correction du menu contextuel des dossiers de films et ajout de l'édition commune de leurs métadonnées.

## [1.0.31] - 2026-05-21

- Regroupement des catégories `Dossier de films` en dossiers navigables dans la médiathèque.

## [1.0.30] - 2026-05-21

- Affichage des sections `Films` et `Séries` comme grands séparateurs pleine largeur dans la médiathèque.

## [1.0.29] - 2026-05-21

- Ajustement de la fiche agrandie en fenêtre centrée plus compacte, avec texte plus grand et aligné à gauche.
- Ajout du bouton `Visionner` dans la fiche agrandie et correction de l'affichage des titres longs.

## [1.0.28] - 2026-05-21

- Déclenchement du mode fiche plein écran depuis le panneau détail plutôt que depuis la liste.

## [1.0.27] - 2026-05-21

- Ajout d'un mode fiche plein écran au clic sur un film, un épisode ou une série.
- Amélioration de la lisibilité des affiches et résumés avec un bouton `Retour à la liste`.

## [1.0.26] - 2026-05-21

- Ajout de la catégorie `Dossier de séries` et séparation visuelle des films et séries.
- Les catégories manuelles corrigent désormais le type des fiches même si elles sont verrouillées.

## [1.0.25] - 2026-05-21

- Ajout d'un bouton `Annuler` pendant la mise à jour globale des fiches.
- Mise à jour automatique limitée aux fiches sans métadonnées utiles.

## [1.0.24] - 2026-05-21

- Ajout d'un réglage de vitesse de défilement dans les options de thème.
- Défilement de la médiathèque adouci pour faciliter la revue des films.

## [1.0.23] - 2026-05-21

- Ajout de la catégorie `Dossier de films` pour les répertoires contenant plusieurs films indépendants.
- Renommage de la catégorie `Film` en `Film unique` dans la gestion des catégories.

## [1.0.22] - 2026-05-21

- Utilisation de l'image `popcornana.png` pour l'icône de fenêtre, l'écran de démarrage et les icônes générées.

## [1.0.21] - 2026-05-21

- Mise à jour des images Popcornana et de l'icône macOS.

## [1.0.20] - 2026-05-21

- Correction de la génération AppImage Linux quand l'icône `.DirIcon` est créée.

## [1.0.19] - 2026-05-21

- Ajout d'un onglet `Aide` avec logo, présentation du programme, liens API et section technique.

## [1.0.18] - 2026-05-21

- Ajout de cases à cocher devant les sources TMDb et OMDb pour clarifier leur sélection.

## [1.0.17] - 2026-05-21

- Ajout de l'édition des métadonnées communes d'une série.
- Application de l'affiche, du résumé général, du réalisateur et de l'année à tous les épisodes sans modifier leurs titres.

## [1.0.16] - 2026-05-21

- Ajout d'une gestion manuelle des catégories de dossiers de médiathèque.
- Possibilité de forcer un dossier en `Auto`, `Film`, `Série` ou `Ignorer`.

## [1.0.15] - 2026-05-21

- Ajout du réalisateur aux métadonnées affichées, enrichies et éditables.

## [1.0.14] - 2026-05-21

- Repositionnement de la fenêtre de démarrage légèrement plus haut à l'ouverture.

## [1.0.13] - 2026-05-21

- Ajout d'un artefact Linux `.AppImage` aux builds de release.
- Ouverture de l'application directement en plein écran, y compris pour la variante Catalina.

## [1.0.12] - 2026-05-21

- Réorganisation du bloc `Options avancées` avec une ligne par source et un bouton d'enregistrement par clé API.

## [1.0.11] - 2026-05-21

- Protection des fiches modifiées manuellement contre l'enrichissement automatique.
- Fusion des boutons `Scanner` et `Rafraîchir` en `Actualiser`.
- Affichage d'une fenêtre de progression pendant la mise à jour des fiches.

## [1.0.10] - 2026-05-20

- Suppression du bouton `Recherche manuelle` dans l'onglet Options.
- Ajout d'un menu clic droit sur les médias avec recherches TMDb/OMDb et édition manuelle.
- Ajout d'une saisie manuelle du titre, de l'année, du résumé et de l'affiche.

## [1.0.9] - 2026-05-20

- Build Catalina: collecte complète de PySide6 pour embarquer les plugins Qt nécessaires aux images PNG.

## [1.0.8] - 2026-05-20

- Recherche des images embarquées dans plusieurs emplacements possibles du bundle macOS `.app`.

## [1.0.7] - 2026-05-20

- Commande de build Catalina complétée avec l'icône macOS `assets/popcornana.icns`.

## [1.0.6] - 2026-05-20

- Compatibilité macOS Catalina: épinglage de `PySide6==6.2.4`.
- Compatibilité Python 3.8: remplacement des dataclasses avec `slots=True`.
- Documentation Catalina mise à jour avec Python 3.8, PyInstaller et lancement via `dist/Popcornana.app`.
- Commande de build Catalina corrigée pour inclure les images du dossier `assets`.
- Lancement VLC corrigé sur macOS pour ouvrir le lecteur au premier plan.
- Regroupement des épisodes dans des dossiers de séries.
- Détection des structures de séries `Saison/Episode` et `Season/Episode`.

## [1.0.5] - 2026-05-20

- Ajout de champs API OMDb/TMDb et application du thème à la fenêtre de démarrage.

## [1.0.4] - 2026-05-20

- Utilisation du runner `macos-15-intel` pour le build macOS Intel.
- Utilisation de `popcornana_ico.png` comme icône applicative multi-OS.

## [1.0.3] - 2026-05-20

- Agrandissement du logo dans l'onglet Options.
- Remplacement du message de barre d'état par le nombre de médias trouvés.
- Ajout d'un workflow de build multi-OS avec artefacts macOS Intel, Windows et Linux.

## [1.0.2] - 2026-05-20

- Ajout d'un message de patience et du statut d'actualisation au démarrage.

## [1.0.1] - 2026-05-20

- Ajustement de la fenêtre de démarrage en superposition de l'application.

## [1.0.0] - 2026-05-20

### État actuel

Version initiale stable de Popcornana: application desktop locale PySide6 pour scanner une médiathèque vidéo, l'afficher en grille, enrichir les métadonnées via OMDb/TMDb, mettre en cache les affiches et lancer la lecture avec VLC quand il est disponible.

### Ajouté

- Interface en deux onglets: `Général` pour la médiathèque, `Options` pour la configuration et les actions.
- Grille visuelle des médias avec affiches, titre, année et sélection.
- Panneau détail avec affiche, titre, métadonnées, résumé scrollable, chemin du fichier et bouton `Visionner`.
- Sélecteur de thèmes persistant avec thèmes sombres, clairs et colorés.
- Logo applicatif depuis `assets/popcornana.png`.
- Scan récursif des fichiers vidéo `.mkv`, `.mp4`, `.avi`, `.mov`.
- Nettoyage des noms de fichiers et détection des films/séries/épisodes.
- Base SQLite locale `media.db` pour les médias et réglages.
- Nettoyage des entrées dont les fichiers n'existent plus via `Rafraîchir`.
- Enrichissement automatique OMDb avec cache local des affiches.
- Support TMDb conservé pour enrichissement automatique et recherche manuelle.
- Sélection persistante des sources de métadonnées `TMDb` et `OMDb` dans `Options avancées`.
- Contour coloré sur les boutons de sources sélectionnées.
- Enrichissement automatique unifié: TMDb d'abord, OMDb en secours si les deux sources sont sélectionnées.
- Lecture via VLC si disponible, avec détection automatique des sous-titres dans le même dossier.
- Fallback vers le lecteur par défaut du système si VLC n'est pas trouvé.

### Comportement des sous-titres

- Priorité au fichier sous-titre portant exactement le même nom que la vidéo.
- Sinon, utilisation du premier fichier sous-titre trouvé dans le même dossier.
- Extensions reconnues: `.srt`, `.ass`, `.ssa`, `.sub`, `.vtt`.

### Notes

- `OMDB_API_KEY` et `TMDB_API_KEY` se configurent dans `.env`.
- Les valeurs placeholder comme `xxxxxxxx` ne sont pas considérées comme des clés valides.
- Le produit utilise l'API TMDb sans être approuvé ni certifié par TMDb.

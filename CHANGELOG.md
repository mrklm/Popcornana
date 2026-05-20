# Changelog

Toutes les modifications notables de Popcornana sont documentées ici.

Le projet suit une logique de versionnement sémantique: `MAJEUR.MINEUR.CORRECTIF`.

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

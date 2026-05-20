# Changelog

Toutes les modifications notables de Popcornana sont documentées ici.

Le projet suit une logique de versionnement sémantique: `MAJEUR.MINEUR.CORRECTIF`.

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

# Popcornana

Version actuelle: **1.0.0**

Popcornana est une application desktop locale pour indexer une médiathèque de films et séries, récupérer des métadonnées TMDb, garder un cache local d'affiches, puis lancer la lecture avec le lecteur système.

This product uses the TMDB API but is not endorsed or certified by TMDB.

## Fonctionnalités V1

- Choix d'un dossier avec une boîte native Qt.
- Scan récursif des fichiers `.mkv`, `.mp4`, `.avi`, `.mov`.
- Détection films et épisodes avec les formats `S01E01`, `1x01`, `Season 01 Episode 01`.
- Nettoyage des noms de fichiers courants: qualité, codec, source, langue, rip tags.
- Sauvegarde SQLite dans `media.db`.
- Enrichissement automatique TMDb si une correspondance est assez fiable.
- Enrichissement automatique OMDb en alternative si une clé OMDb est configurée.
- Sélection persistante des sources de métadonnées dans les options avancées.
- Recherche manuelle TMDb sur le média sélectionné.
- Cache d'affiches dans `data/posters/`.
- Grille visuelle, panneau détail et bouton de visionnage.
- Lecture via VLC si disponible, avec sous-titre détecté automatiquement dans le même dossier.
- Thèmes visuels persistants.

## Installation

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Ajoute ensuite ta clé TMDb dans `.env`:

```env
TMDB_API_KEY=xxxxxxxx
OMDB_API_KEY=xxxxxxxx
```

## Lancement

```bash
python main.py
```

## Structure

```text
app/
  database/   SQLite et réglages
  models/     modèles Python
  scanner/    scan vidéo et parsing de noms
  tmdb/       client TMDb et téléchargement affiches
  ui/         interface PySide6
  utils/      chemins et lecture média
data/
  posters/    cache local des affiches
  cache/      réservé pour les futurs caches
media.db      base locale créée au premier lancement
```

## Packaging

Windows:

```bash
pyinstaller --onefile --windowed main.py
```

macOS:

```bash
pyinstaller --windowed main.py
```

Linux:

```bash
pyinstaller --onefile --windowed main.py
```

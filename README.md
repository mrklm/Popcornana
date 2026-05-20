# Popcornana

Version actuelle: **1.0.2**

Popcornana est une application desktop locale pour organiser une médiathèque de films et séries. Elle scanne un dossier de vidéos, nettoie les noms de fichiers, affiche les médias dans une grille visuelle, récupère des métadonnées depuis OMDb et/ou TMDb, garde les affiches en cache local, puis lance la lecture avec VLC quand il est disponible.

L'application est pensée pour rester simple et locale: les fichiers vidéo restent sur la machine, la base de données est un fichier SQLite local, et les affiches téléchargées sont stockées dans `data/posters/`.

This product uses the TMDB API but is not endorsed or certified by TMDB.

## Fonctionnalités

- Scan récursif d'un dossier de médias.
- Prise en charge des vidéos `.mkv`, `.mp4`, `.avi`, `.mov`.
- Détection des films et épisodes de séries avec les formats `S01E01`, `1x01`, `Season 01 Episode 01`.
- Nettoyage automatique des noms de fichiers: qualité, codec, source, langue, tags de release.
- Affichage en grille avec affiche, titre et année.
- Panneau détail avec affiche, titre, note, résumé, chemin du fichier et bouton `Visionner`.
- Résumé long contenu dans une zone scrollable.
- Enrichissement automatique via OMDb.
- Support TMDb conservé pour enrichissement automatique et recherche manuelle.
- Choix persistant des sources de métadonnées dans `Options avancées`.
- Si OMDb et TMDb sont sélectionnés ensemble, TMDb est essayé en premier puis OMDb sert de secours.
- Cache local des affiches dans `data/posters/`.
- Nettoyage des fichiers disparus via `Rafraîchir`.
- Sélecteur de thème persistant.
- Lecture via VLC si disponible, sinon lecteur par défaut du système.
- Détection automatique des sous-titres présents dans le même dossier que la vidéo.

## Interface

L'interface est divisée en deux onglets.

**Général**

Affiche la médiathèque sous forme de grille. La sélection d'un média met à jour le panneau de droite avec les détails et le bouton `Visionner`.

**Options**

Regroupe les actions et réglages:

- `Choisir dossier`: définit le dossier à scanner.
- `Scanner`: analyse le dossier choisi et ajoute les vidéos détectées.
- `Rafraîchir`: recharge la médiathèque et retire les entrées dont le fichier n'existe plus.
- `Enrichir auto`: récupère les métadonnées avec les sources sélectionnées.
- `Recherche manuelle`: lance la recherche TMDb sur le média sélectionné.
- `Options avancées`: permet de choisir OMDb, TMDb ou les deux.
- `Thème`: change le thème visuel de l'application.

## Métadonnées

Les clés API sont configurées dans le fichier `.env`.

```env
TMDB_API_KEY=xxxxxxxx
OMDB_API_KEY=xxxxxxxx
```

`OMDB_API_KEY` est actuellement la source la plus utile si TMDb ne permet pas encore de récupérer une clé. Les valeurs placeholder comme `xxxxxxxx` sont ignorées par l'application et ne sont pas considérées comme des clés valides.

## Sous-titres

Quand VLC est disponible, Popcornana cherche automatiquement un sous-titre dans le même dossier que la vidéo.

Règle de sélection:

1. priorité au fichier de sous-titre portant exactement le même nom que la vidéo ;
2. sinon, utilisation du premier fichier de sous-titre trouvé dans le dossier.

Extensions reconnues:

```text
.srt
.ass
.ssa
.sub
.vtt
```

Exemples:

```text
Film.mkv
Film.srt
```

ou:

```text
Film.mkv
sous_titre_francais.srt
```

## Installation

Depuis la racine du projet:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Puis renseigner les clés API dans `.env`.

## Lancement

```bash
.venv/bin/python main.py
```

Ou, si l'environnement virtuel est activé:

```bash
python main.py
```

## Données locales

```text
media.db        base SQLite locale
data/posters/   cache local des affiches
data/cache/     dossier réservé aux caches futurs
.env            clés API locales, ignorées par git
```

## Structure du projet

```text
app/
  database/   accès SQLite et réglages persistants
  models/     modèles de données
  omdb/       client OMDb
  scanner/    scan vidéo et parsing de noms
  tmdb/       client TMDb
  ui/         interface PySide6
  utils/      chemins, lecture média, helpers
assets/        logo et images de l'application
data/          cache local créé/utilisé par l'application
main.py        point d'entrée
VERSION        version applicative
CHANGELOG.md   historique des versions
```

## Build multi-OS

Il n'y a pas encore de build multi-OS automatisé en place.

État actuel:

- pas de fichier `.spec` PyInstaller versionné ;
- pas de workflow GitHub Actions ;
- pas de script de build unique ;
- pas de génération automatique macOS/Windows/Linux.

Les commandes PyInstaller ci-dessous sont des bases de travail, mais elles n'ont pas encore été stabilisées en pipeline de release.

macOS:

```bash
pyinstaller --windowed --name Popcornana main.py
```

Windows:

```bash
pyinstaller --onefile --windowed --name Popcornana main.py
```

Linux:

```bash
pyinstaller --onefile --name Popcornana main.py
```

Pour un vrai build multi-OS, la prochaine étape serait d'ajouter:

- un fichier `Popcornana.spec` ;
- l'inclusion explicite de `assets/`, `.env.example` et des dossiers `data/cache`, `data/posters` ;
- un script `scripts/build.py` ou `Makefile` ;
- un workflow CI qui construit séparément sur macOS, Windows et Linux.

## Version

La version actuelle est `1.0.0`.

Voir [CHANGELOG.md](CHANGELOG.md) pour le détail de l'état de la release.

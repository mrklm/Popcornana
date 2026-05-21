# Popcornana

Version actuelle: **1.0.26**

Popcornana est une application desktop locale pour organiser une médiathèque de films et séries. Elle scanne un dossier de vidéos, nettoie les noms de fichiers, affiche les médias dans une grille visuelle, récupère des métadonnées depuis OMDb et/ou TMDb, garde les affiches en cache local, puis lance la lecture avec VLC avc le sous titre quand il est disponible.

L'application est pensée pour rester simple et locale: les fichiers vidéo restent sur la machine, la base de données est un fichier SQLite local, et les affiches téléchargées sont stockées dans `data/posters/`.


## Fonctionnalités

- Scan récursif d'un dossier de médias.
- Prise en charge des vidéos `.mkv`, `.mp4`, `.avi`, `.mov`.
- Détection des films et épisodes de séries avec les formats `S01E01`, `1x01`, `Season 01 Episode 01`, `Saison 01 Episode 01` et les dossiers `Saison 01/Episode 01`.
- Nettoyage automatique des noms de fichiers: qualité, codec, source, langue, tags de release.
- Affichage en grille avec affiche, titre et année.
- Regroupement des épisodes dans des dossiers de séries pour garder la médiathèque lisible.
- Panneau détail avec affiche, titre, note, résumé, chemin du fichier et bouton `Visionner`.
- Résumé long contenu dans une zone scrollable.
- Enrichissement automatique via OMDb.
- Recherches contextuelles TMDb/OMDb et édition manuelle des métadonnées depuis la grille.
- Choix persistant des sources de métadonnées dans `Options avancées`.
- Si OMDb et TMDb sont sélectionnés ensemble, TMDb est essayé en premier puis OMDb sert de secours.
- Cache local des affiches dans `data/posters/`.
- Actualisation unique de la médiathèque: ajout des nouveaux fichiers et retrait des fichiers disparus.
- Sélecteur de thème persistant.
- Lecture via VLC si disponible, sinon lecteur par défaut du système.
- Détection automatique des sous-titres présents dans le même dossier que la vidéo.

## Interface

L'interface est divisée en deux onglets.

**Général**

Affiche la médiathèque sous forme de grille. Les séries apparaissent comme des dossiers ouvrables, puis leurs épisodes sont listés à l'intérieur. La sélection d'un média met à jour le panneau de droite avec les détails et le bouton `Visionner`.

Un clic droit sur un film ou un épisode permet de lancer une recherche TMDb, une recherche OMDb ou une saisie manuelle du titre, de l'année, du résumé et de l'affiche.

**Options**

Regroupe les actions et réglages:

- `Choisir dossier`: définit le dossier à scanner.
- `Actualiser`: analyse le dossier choisi, ajoute les vidéos détectées et retire les entrées dont le fichier n'existe plus.
- `Mettre à jour les fiches`: récupère les métadonnées avec les sources sélectionnées et affiche une fenêtre de progression.
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

Le projet dispose d'un workflow GitHub Actions pour générer des releases distinctes par OS.

Artefacts produits:

- `Popcornana-macos-intel.zip`: application `.app` macOS Intel ;
- `Popcornana-windows-x64.zip`: exécutable Windows x64 ;
- `Popcornana-linux-x64.tar.gz`: exécutable Linux x64 ;
- `Popcornana-linux-x64.AppImage`: application Linux x64 portable.

Le workflow est défini dans `.github/workflows/release.yml`. Il peut être lancé manuellement depuis l'onglet Actions de GitHub, ou automatiquement en poussant un tag `v*`.

Exemple de release:

```bash
git tag v1.0.13
git push origin main
git push origin v1.0.13
```

Sur un tag, GitHub Actions construit les trois artefacts et les ajoute à la release GitHub correspondante.

Pour construire localement sur l'OS courant:

```bash
python -m pip install -r requirements.txt -r requirements-build.txt
python scripts/build_release.py --target macos-intel
python scripts/build_release.py --target windows-x64
python scripts/build_release.py --target linux-x64
```

Seule la cible correspondant au système courant est réellement prévue pour un build local fiable. Le build multi-OS complet passe par GitHub Actions.

macOS:

```bash
python scripts/build_release.py --target macos-intel
```

Windows:

```bash
python scripts/build_release.py --target windows-x64
```

Linux:

```bash
python scripts/build_release.py --target linux-x64
```

La cible Linux nécessite `appimagetool` dans le `PATH` pour générer l'artefact `.AppImage`.

## Build macOS Catalina legacy

Une branche dédiée `legacy-macos-catalina` prépare une variante pour les Macs Intel limités à macOS Catalina 10.15.

Sur cette branche, `requirements.txt` épingle directement `PySide6==6.2.4` pour conserver la compatibilité avec Catalina et Python 3.8.2.

Build local recommandé depuis un Mac Intel sous Catalina:

```bash
python3.8 -m venv .venv-catalina
source .venv-catalina/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-build-macos-catalina.txt
python -m PyInstaller --windowed --name Popcornana --icon assets/popcornana.icns --add-data "assets:assets" --collect-all PySide6 main.py
```

L'application générée se trouve dans `dist/Popcornana.app`.

Voir [docs/MACOS_CATALINA.md](docs/MACOS_CATALINA.md) pour les détails et limites.

## Version

La version actuelle est `1.0.13`.

Voir [CHANGELOG.md](CHANGELOG.md) pour le détail de l'état de la release.

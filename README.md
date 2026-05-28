# Popcornana

Version actuelle: **1.0.61**

Popcornana est une application desktop locale pour organiser une médiathèque de films et séries. Elle scanne un dossier de vidéos, nettoie les noms de fichiers, affiche les médias dans une grille visuelle, récupère des métadonnées depuis OMDb et/ou TMDb, garde les affiches en cache local, puis lance la lecture avec VLC en plein écran quand il est disponible, avec sous-titre détecté automatiquement.

L'application est pensée pour rester simple et locale: les fichiers vidéo restent sur la machine, la base de données est un fichier SQLite local, et les affiches téléchargées sont stockées dans `data/posters/`.

## Aperçu

![Popcornana](screenshots/popcornana1.png)
![Popcornana](screenshots/popcornana2.png)
![Popcornana](screenshots/popcornana3.png)


## Fonctionnalités

- Scan récursif d'un dossier de médias.
- Prise en charge des vidéos `.mkv`, `.mp4`, `.avi`, `.mov`.
- Détection des films et épisodes de séries avec les formats `S01E01`, `1x01`, `Season 01 Episode 01`, `Saison 01 Episode 01` et les dossiers `Saison 01/Episode 01`.
- Nettoyage automatique des noms de fichiers: qualité, codec, source, langue, tags de release.
- Affichage en grille avec affiche, titre et année.
- Regroupement des épisodes dans des dossiers de séries pour garder la médiathèque lisible.
- Regroupement des répertoires de films en dossiers navigables, avec visuel dédié possible.
- Séparation visuelle des sections `Films` et `Séries`.
- Panneau détail avec affiche, titre, durée, note, résumé, chemin du fichier et bouton `Visionner`.
- Zoom fiche au clic sur le panneau détail, avec texte agrandi, résumé scrollable et bouton `Visionner`.
- Résumés longs contenus dans des zones scrollables.
- Enrichissement automatique via OMDb.
- Recherches contextuelles TMDb/OMDb et édition manuelle des métadonnées depuis la grille.
- Création de `cover.*` et `Popinfo.txt` dans le dossier du film quand une fiche est enrichie sur une source autorisée, sans écraser les fichiers existants.
- Synchronisation des métadonnées entre sources avant les appels TMDb/OMDb quand un doublon local fiable possède déjà `cover.*` ou `Popinfo.txt`.
- Édition commune des métadonnées de série sans modifier les titres des épisodes.
- Choix persistant des sources de métadonnées dans `Options avancées`.
- Si OMDb et TMDb sont sélectionnés ensemble, TMDb est essayé en premier puis OMDb sert de secours.
- Cache local des affiches dans `data/posters/`.
- Actualisation unique de la médiathèque: ajout des nouveaux fichiers et retrait des fichiers disparus.
- Sélecteur de thème et vitesse de défilement persistants.
- Lecture via VLC en plein écran si disponible, sinon lecteur par défaut du système.
- Détection automatique des sous-titres présents dans le même dossier que la vidéo.

## Interface

L'interface est divisée en trois onglets.

**Général**

Affiche la médiathèque sous forme de grille, séparée en sections `Films` et `Séries`. Les séries apparaissent comme des dossiers ouvrables, puis leurs épisodes sont listés à l'intérieur. Les dossiers de films apparaissent comme des dossiers navigables sans modifier les fiches des films contenus.

La sélection d'un média met à jour le panneau de droite avec les détails et le bouton `Visionner`. Un clic sur ce panneau ouvre le zoom fiche, plus lisible, avec résumé scrollable et bouton de lecture.

Un clic droit sur un film ou un épisode permet de lancer une recherche TMDb, une recherche OMDb ou une saisie manuelle du titre, de l'année, du réalisateur, du résumé et de l'affiche. Un clic droit sur une série permet d'appliquer une affiche, une année, un réalisateur et un résumé général aux épisodes sans changer leurs titres. Un clic droit sur un dossier de films permet de l'ouvrir ou de choisir son visuel propre.

**Options**

Regroupe les actions et réglages:

- `Ajouter dossier`: ajoute une source à la médiathèque sans remplacer les autres.
- `Gérer les sources`: affiche les sources connues, permet de retirer celles qui ne doivent plus être suivies et d'autoriser la synchronisation locale.
- `Actualiser`: analyse les sources disponibles, ajoute les vidéos détectées et retire les entrées dont le fichier n'existe plus dans ces sources.
- `Mettre à jour les fiches`: récupère les métadonnées avec les sources sélectionnées et affiche une fenêtre de progression.
- `Gérer les catégories`: force un dossier en Auto, Film unique, Dossier de films, Série, Dossier de séries ou Ignorer.
- `Options avancées`: permet de choisir OMDb, TMDb ou les deux et d'enregistrer les clés API.
- `Thème`: change le thème visuel de l'application et ajuste la vitesse de défilement.

**Aide**

Décrit le fonctionnement de Popcornana, donne les adresses pour obtenir les clés API TMDb/OMDb et résume les choix techniques dans une section `Pour les Geeks`.

## Métadonnées

Avant d'appeler Internet, `Mettre à jour les fiches` cherche d'abord un doublon local fiable dans les autres sources. Si un dossier équivalent possède déjà `cover.*` ou `Popinfo.txt`, Popcornana copie uniquement les fichiers manquants vers la source cible lorsque sa case `Synchro autorisée` est cochée.

L'autorisation est mémorisée dans `.popcornana-source` à la racine de la source. Ce fichier limite l'écriture aux fichiers de métadonnées portables et conserve la version du format utilisé.

Les clés API peuvent être enregistrées depuis `Options avancées`. Elles peuvent aussi être placées dans le fichier `.env`.

```env
TMDB_API_KEY=xxxxxxxx
OMDB_API_KEY=xxxxxxxx
```

Les valeurs placeholder comme `xxxxxxxx` sont ignorées par l'application et ne sont pas considérées comme des clés valides.

Adresses utiles:

- TMDb: <https://www.themoviedb.org/settings/api>
- OMDb: <https://www.omdbapi.com/apikey.aspx>

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
git tag v1.0.50 main
git push origin main
git push origin v1.0.50
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

## Version

La version actuelle est `1.0.50`.

Voir [CHANGELOG.md](CHANGELOG.md) pour le détail de l'état de la release.

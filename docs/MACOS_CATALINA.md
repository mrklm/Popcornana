# Build macOS Catalina

Cette branche sert de piste legacy pour produire une application Popcornana compatible avec les Macs Intel limités à macOS Catalina 10.15.

## Principe

La branche principale utilise une pile récente (`PySide6>=6.7`) et les runners GitHub Actions modernes. Cette combinaison vise les versions récentes de macOS.

Pour Catalina, on isole une pile plus ancienne:

- Python 3.8 compatible Catalina ;
- PySide6 6.2.4 obligatoire ;
- PyInstaller pour générer l'application `.app`.

## Build recommandé

Le build Catalina doit idéalement être lancé depuis un Mac Intel sous macOS Catalina 10.15.

```bash
python3.8 -m venv .venv-catalina
source .venv-catalina/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
python main.py
python -m PyInstaller --windowed --name Popcornana --icon assets/popcornana.icns --add-data "assets:assets" main.py
```

Artefact attendu:

```text
dist/Popcornana.app
```

## Limite importante

Construire cette cible depuis un macOS plus récent peut produire une application qui refuse encore de se lancer sur Catalina. Pour une vraie compatibilité avec une vieille machine, le plus fiable reste de bâtir l'application sur la plus vieille version de macOS supportée, donc Catalina dans notre cas.

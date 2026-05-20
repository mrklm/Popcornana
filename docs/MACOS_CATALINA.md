# Build macOS Catalina

Cette branche sert de piste legacy pour produire une application Popcornana compatible avec les Macs Intel limités à macOS Catalina 10.15.

## Principe

La branche principale utilise une pile récente (`PySide6>=6.7`) et les runners GitHub Actions modernes. Cette combinaison vise les versions récentes de macOS.

Pour Catalina, on isole une pile plus ancienne:

- Python 3.10 ;
- PySide6 6.2.4 ;
- PyInstaller 5.13.2 ;
- cible de build `macos-catalina-intel` ;
- variable `MACOSX_DEPLOYMENT_TARGET=10.15` définie par le script de build.

## Build recommandé

Le build Catalina doit idéalement être lancé depuis un Mac Intel sous macOS Catalina 10.15.

```bash
python3.10 -m venv .venv-catalina
source .venv-catalina/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-macos-catalina.txt -r requirements-build-macos-catalina.txt
python scripts/build_release.py --target macos-catalina-intel
```

Artefact attendu:

```text
dist/Popcornana-macos-catalina-intel.zip
```

## Limite importante

Construire cette cible depuis un macOS plus récent peut produire une application qui refuse encore de se lancer sur Catalina. Pour une vraie compatibilité avec une vieille machine, le plus fiable reste de bâtir l'application sur la plus vieille version de macOS supportée, donc Catalina dans notre cas.

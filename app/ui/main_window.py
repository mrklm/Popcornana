from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSize, QTimer, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.database.repository import MediaRepository
from app.models.media import MediaItem
from app.omdb.client import OmdbClient
from app.scanner.video_scanner import scan_videos
from app.tmdb.client import TmdbClient, TmdbResult, apply_tmdb_result
from app.utils.paths import POSTERS_DIR, ensure_data_dirs, resource_path
from app.utils.player import open_media
from app.version import APP_VERSION


ASSETS_DIR = resource_path("assets")
LOGO_PATH = ASSETS_DIR / "popcornana.png"
STARTUP_IMAGE_PATH = ASSETS_DIR / "popcornana_ico.png"

THEMES = {
    "[Sombre] Midnight Garage": dict(
        BG="#151515", PANEL="#1F1F1F", FIELD="#2A2A2A",
        FG="#EAEAEA", FIELD_FG="#F0F0F0", ACCENT="#FF9800"
    ),
    "[Sombre] AIR-KLM Night flight": dict(
        BG="#0B1E2D", PANEL="#102A3D", FIELD="#16384F",
        FG="#EAF6FF", FIELD_FG="#FFFFFF", ACCENT="#00A1DE"
    ),
    "[Sombre] Café Serré": dict(
        BG="#1B120C", PANEL="#2A1C14", FIELD="#3A281D",
        FG="#F2E6D8", FIELD_FG="#FFF4E6", ACCENT="#C28E5C"
    ),
    "[Sombre] Matrix Déjà Vu": dict(
        BG="#000A00", PANEL="#001F00", FIELD="#003300",
        FG="#00FF66", FIELD_FG="#66FF99", ACCENT="#00FF00"
    ),
    "[Sombre] Miami Vice 1987": dict(
        BG="#14002E", PANEL="#2B0057", FIELD="#004D4D",
        FG="#FFF0FF", FIELD_FG="#FFFFFF", ACCENT="#00FFD5"
    ),
    "[Sombre] Cyber Licorne": dict(
        BG="#1A0026", PANEL="#2E004F", FIELD="#3D0066",
        FG="#F6E7FF", FIELD_FG="#FFFFFF", ACCENT="#FF2CF7"
    ),
    "[Clair] AIR-KLM Day flight": dict(
        BG="#EAF6FF", PANEL="#D6EEF9", FIELD="#FFFFFF",
        FG="#0B2A3F", FIELD_FG="#0B2A3F", ACCENT="#00A1DE"
    ),
    "[Clair] Matin Brumeux": dict(
        BG="#E6E7E8", PANEL="#D4D7DB", FIELD="#FFFFFF",
        FG="#1E1F22", FIELD_FG="#1E1F22", ACCENT="#6B7C93"
    ),
    "[Clair] Latte Vanille": dict(
        BG="#FAF6F1", PANEL="#EFE6DC", FIELD="#FFFFFF",
        FG="#3D2E22", FIELD_FG="#3D2E22", ACCENT="#D8B892"
    ),
    "[Clair] Miellerie La Divette": dict(
        BG="#E6B65C", PANEL="#F5E6CC", FIELD="#FFFFFF",
        FG="#50371A", FIELD_FG="#50371A", ACCENT="#F2B705"
    ),
    "[Pouêt] Chewing-gum Océan": dict(
        BG="#00A6C8", PANEL="#0083A1", FIELD="#00C7B7",
        FG="#082026", FIELD_FG="#082026", ACCENT="#FF4FD8"
    ),
    "[Pouêt] Pamplemousse": dict(
        BG="#FF4A1C", PANEL="#E63B10", FIELD="#FF7A00",
        FG="#1A0B00", FIELD_FG="#1A0B00", ACCENT="#00E5FF"
    ),
    "[Pouêt] Raisin Toxique": dict(
        BG="#7A00FF", PANEL="#5B00C9", FIELD="#B000FF",
        FG="#0F001A", FIELD_FG="#0F001A", ACCENT="#39FF14"
    ),
    "[Pouêt] Citron qui pique": dict(
        BG="#FFF200", PANEL="#E6D800", FIELD="#FFF7A6",
        FG="#1A1A00", FIELD_FG="#1A1A00", ACCENT="#0066FF"
    ),
    "[Pouêt] Barbie Apocalypse": dict(
        BG="#FF1493", PANEL="#004D40", FIELD="#1B5E20",
        FG="#E8FFF8", FIELD_FG="#FFFFFF", ACCENT="#FFEB3B"
    ),
    "[Pouêt] Compagnie Créole": dict(
        BG="#8B3A1A", PANEL="#F2C94C", FIELD="#FFFFFF",
        FG="#5A2E0C", FIELD_FG="#5A2E0C", ACCENT="#8B3A1A"
    ),
}
DEFAULT_THEME = "[Sombre] Midnight Garage"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        ensure_data_dirs()
        self.repository = MediaRepository()
        self.tmdb = TmdbClient()
        self.omdb = OmdbClient()
        self.items: list[MediaItem] = []
        self.current_item: MediaItem | None = None

        self.setWindowTitle(f"Popcornana {APP_VERSION}")
        self.resize(1180, 760)
        self._build_ui()
        self._load_saved_state()

    def _build_ui(self) -> None:
        page = QWidget()
        page.setObjectName("page")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(18, 16, 18, 12)
        page_layout.setSpacing(12)

        tabs = QTabWidget()
        tabs.setObjectName("mainTabs")

        self.grid = QListWidget()
        self.grid.setObjectName("libraryGrid")
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setIconSize(QSize(150, 225))
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setMovement(QListWidget.Static)
        self.grid.setSpacing(14)
        self.grid.setUniformItemSizes(True)
        self.grid.currentRowChanged.connect(self.select_item)

        self.poster_label = QLabel()
        self.poster_label.setObjectName("posterLabel")
        self.poster_label.setFixedSize(180, 270)
        self.poster_label.setAlignment(Qt.AlignCenter)
        self.poster_label.setStyleSheet("background: #202124; color: #cfd2d6;")

        self.title_label = QLabel("Popcornana")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: 700;")

        self.meta_label = QLabel("")
        self.meta_label.setObjectName("metaLabel")
        self.meta_label.setStyleSheet("color: #6b7280;")

        self.overview_label = QLabel("Choisis un dossier, scanne tes vidéos, puis enrichis avec TMDb.")
        self.overview_label.setObjectName("overviewLabel")
        self.overview_label.setWordWrap(True)
        self.overview_label.setAlignment(Qt.AlignTop)

        overview_scroll = QScrollArea()
        overview_scroll.setObjectName("overviewScroll")
        overview_scroll.setWidgetResizable(True)
        overview_scroll.setFrameShape(QScrollArea.NoFrame)
        overview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        overview_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        overview_scroll.setWidget(self.overview_label)
        overview_scroll.setMinimumHeight(110)
        overview_scroll.setMaximumHeight(190)

        self.path_label = QLabel("")
        self.path_label.setObjectName("pathLabel")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: #6b7280;")

        play_button = QPushButton("Visionner")
        play_button.clicked.connect(self.play_current)

        details = QWidget()
        details.setObjectName("detailsPanel")
        details.setFixedWidth(390)
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(18, 18, 18, 18)
        details_layout.setSpacing(8)
        details_layout.addWidget(self.poster_label, alignment=Qt.AlignHCenter)
        details_layout.addWidget(self.title_label)
        details_layout.addWidget(self.meta_label)
        details_layout.addWidget(overview_scroll)
        details_layout.addWidget(self.path_label)
        details_layout.addWidget(play_button)

        general_tab = QWidget()
        general_tab.setObjectName("generalTab")
        general_layout = QHBoxLayout(general_tab)
        general_layout.setContentsMargins(0, 0, 0, 0)
        general_layout.setSpacing(18)
        general_layout.addWidget(self.grid, stretch=1)
        general_layout.addWidget(details)
        tabs.addTab(general_tab, "Général")

        options_tab = QWidget()
        options_tab.setObjectName("optionsTab")
        options_layout = QVBoxLayout(options_tab)
        options_layout.setContentsMargins(18, 18, 18, 18)
        options_layout.setSpacing(16)

        self.logo_label = QLabel()
        self.logo_label.setObjectName("logoLabel")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(320, 240)
        self._load_logo()
        options_layout.addWidget(self.logo_label, alignment=Qt.AlignHCenter)

        actions_section = QWidget()
        actions_section.setObjectName("optionSection")
        actions_layout = QVBoxLayout(actions_section)
        actions_layout.setContentsMargins(16, 16, 16, 16)
        actions_layout.setSpacing(10)

        actions_title = QLabel("Médiathèque")
        actions_title.setObjectName("sectionTitle")
        actions_layout.addWidget(actions_title)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)

        choose_button = QPushButton("Choisir dossier")
        choose_button.clicked.connect(self.choose_folder)
        buttons_layout.addWidget(choose_button)

        scan_button = QPushButton("Scanner")
        scan_button.clicked.connect(self.scan_current_folder)
        buttons_layout.addWidget(scan_button)

        refresh_button = QPushButton("Rafraîchir")
        refresh_button.clicked.connect(lambda: self.reload_library())
        buttons_layout.addWidget(refresh_button)

        enrich_button = QPushButton("Enrichir auto")
        enrich_button.clicked.connect(self.enrich_library_with_selected_sources)
        buttons_layout.addWidget(enrich_button)

        manual_button = QPushButton("Recherche manuelle")
        manual_button.clicked.connect(self.manual_search_current)
        buttons_layout.addWidget(manual_button)
        buttons_layout.addStretch()
        actions_layout.addLayout(buttons_layout)

        self.folder_label = QLabel("Aucun dossier choisi")
        self.folder_label.setObjectName("folderLabel")
        self.folder_label.setWordWrap(True)
        actions_layout.addWidget(self.folder_label)
        options_layout.addWidget(actions_section)

        advanced_section = QWidget()
        advanced_section.setObjectName("optionSection")
        advanced_layout = QVBoxLayout(advanced_section)
        advanced_layout.setContentsMargins(16, 16, 16, 16)
        advanced_layout.setSpacing(10)

        advanced_title = QLabel("Options avancées")
        advanced_title.setObjectName("sectionTitle")
        advanced_layout.addWidget(advanced_title)

        sources_layout = QHBoxLayout()
        sources_layout.setContentsMargins(0, 0, 0, 0)
        sources_layout.setSpacing(8)

        self.tmdb_source_button = QPushButton("TMDb")
        self.tmdb_source_button.setObjectName("sourceButton")
        self.tmdb_source_button.setCheckable(True)
        self.tmdb_source_button.toggled.connect(self.save_source_preferences)
        sources_layout.addWidget(self.tmdb_source_button)

        self.omdb_source_button = QPushButton("OMDb")
        self.omdb_source_button.setObjectName("sourceButton")
        self.omdb_source_button.setCheckable(True)
        self.omdb_source_button.toggled.connect(self.save_source_preferences)
        sources_layout.addWidget(self.omdb_source_button)
        sources_layout.addStretch()
        advanced_layout.addLayout(sources_layout)

        source_hint = QLabel("Sources utilisées par Enrichir auto. Si les deux sont sélectionnées, TMDb est essayé en premier, OMDb sert de secours.")
        source_hint.setObjectName("hintLabel")
        source_hint.setWordWrap(True)
        advanced_layout.addWidget(source_hint)
        options_layout.addWidget(advanced_section)

        theme_section = QWidget()
        theme_section.setObjectName("optionSection")
        theme_layout = QHBoxLayout(theme_section)
        theme_layout.setContentsMargins(16, 16, 16, 16)
        theme_layout.setSpacing(12)

        theme_label = QLabel("Thème")
        theme_label.setObjectName("sectionTitle")
        theme_layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(THEMES.keys())
        self.theme_combo.setMinimumWidth(260)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        options_layout.addWidget(theme_section)
        options_layout.addStretch()
        tabs.addTab(options_tab, "Options")

        page_layout.addWidget(tabs, stretch=1)
        self.setCentralWidget(page)

        self.setStatusBar(QStatusBar())
        self.show_media_count_status()

    def _load_saved_state(self) -> None:
        folder = self.repository.get_setting("media_folder")
        if folder:
            self.folder_label.setText(folder)
        self.load_source_preferences()
        theme_name = self.repository.get_setting("theme") or DEFAULT_THEME
        if theme_name not in THEMES:
            theme_name = DEFAULT_THEME
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentText(theme_name)
        self.theme_combo.blockSignals(False)
        self.apply_theme(theme_name)

    def _load_logo(self) -> None:
        if not LOGO_PATH.exists():
            return
        pixmap = QPixmap(str(LOGO_PATH)).scaled(320, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo_label.setPixmap(pixmap)

    def change_theme(self, theme_name: str) -> None:
        if theme_name not in THEMES:
            return
        self.repository.set_setting("theme", theme_name)
        self.apply_theme(theme_name)

    def load_source_preferences(self) -> None:
        tmdb_enabled = self.repository.get_setting("metadata_source_tmdb") == "1"
        omdb_enabled = self.repository.get_setting("metadata_source_omdb")
        omdb_enabled = True if omdb_enabled is None else omdb_enabled == "1"

        self.tmdb_source_button.blockSignals(True)
        self.omdb_source_button.blockSignals(True)
        self.tmdb_source_button.setChecked(tmdb_enabled)
        self.omdb_source_button.setChecked(omdb_enabled)
        self.tmdb_source_button.blockSignals(False)
        self.omdb_source_button.blockSignals(False)

    def save_source_preferences(self, _checked: bool | None = None) -> None:
        self.repository.set_setting("metadata_source_tmdb", "1" if self.tmdb_source_button.isChecked() else "0")
        self.repository.set_setting("metadata_source_omdb", "1" if self.omdb_source_button.isChecked() else "0")

    def apply_theme(self, theme_name: str) -> None:
        theme = THEMES[theme_name]
        self.setStyleSheet(build_stylesheet(theme))
        self.poster_label.setStyleSheet(
            f"background: {theme['FIELD']}; color: {theme['FIELD_FG']}; border: 1px solid {theme['PANEL']};"
        )
        self.meta_label.setStyleSheet(f"color: {theme['ACCENT']};")
        self.path_label.setStyleSheet(f"color: {theme['FG']};")

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier de médias")
        if not folder:
            return
        self.repository.set_setting("media_folder", folder)
        self.folder_label.setText(folder)
        self.scan_current_folder()

    def scan_current_folder(self) -> None:
        folder = self.repository.get_setting("media_folder")
        if not folder:
            QMessageBox.information(self, "Popcornana", "Choisis d'abord un dossier à scanner.")
            return

        scanned = scan_videos(folder)
        for item in scanned:
            self.repository.upsert_media(item)
        self.refresh_library()
        self.show_media_count_status()

    def reload_library(self, show_status: bool = True) -> None:
        removed = self.repository.delete_missing_media()
        self.refresh_library()
        if not show_status:
            return
        if removed:
            self.statusBar().showMessage(f"{len(self.items)} média(s) trouvé(s), {removed} fichier(s) absent(s) retiré(s).")
        else:
            self.show_media_count_status()

    def enrich_library_with_selected_sources(self) -> None:
        use_tmdb = self.tmdb_source_button.isChecked()
        use_omdb = self.omdb_source_button.isChecked()
        if not use_tmdb and not use_omdb:
            QMessageBox.information(self, "Popcornana", "Sélectionne au moins une source dans Options avancées.")
            return

        available_tmdb = use_tmdb and self.tmdb.is_configured
        available_omdb = use_omdb and self.omdb.is_configured
        if use_tmdb and not self.tmdb.is_configured:
            self.statusBar().showMessage("TMDb sélectionné, mais TMDB_API_KEY n'est pas configurée.")
        if use_omdb and not self.omdb.is_configured:
            self.statusBar().showMessage("OMDb sélectionné, mais OMDB_API_KEY n'est pas configurée.")
        if not available_tmdb and not available_omdb:
            QMessageBox.warning(self, "Métadonnées", "Aucune source sélectionnée n'est configurée dans le fichier .env.")
            return

        updated = 0
        for item in self.repository.list_media():
            before = media_signature(item)
            try:
                enriched = item
                if available_tmdb:
                    enriched = self.tmdb.enrich_automatically(enriched)
                    if enriched.poster_path:
                        self.tmdb.download_poster(enriched.poster_path)

                tmdb_changed = media_signature(enriched) != before
                if available_omdb and not tmdb_changed:
                    enriched = self.omdb.enrich_automatically(enriched)

                if media_signature(enriched) != before:
                    self.repository.upsert_media(enriched)
                    updated += 1
            except Exception as exc:
                self.statusBar().showMessage(f"Erreur métadonnées pour {item.title}: {exc}")

        self.refresh_library()
        sources = []
        if available_tmdb:
            sources.append("TMDb")
        if available_omdb:
            sources.append("OMDb")
        self.statusBar().showMessage(f"{updated} média(s) enrichi(s) avec {' + '.join(sources)}.")

    def enrich_library(self) -> None:
        if not self.tmdb.is_configured:
            QMessageBox.warning(self, "TMDb", "Ajoute TMDB_API_KEY dans un fichier .env pour récupérer les métadonnées.")
            return

        updated = 0
        for item in self.repository.list_media():
            if item.tmdb_id:
                continue
            try:
                enriched = self.tmdb.enrich_automatically(item)
                if enriched.poster_path:
                    self.tmdb.download_poster(enriched.poster_path)
                self.repository.upsert_media(enriched)
                if enriched.tmdb_id:
                    updated += 1
            except Exception as exc:
                self.statusBar().showMessage(f"Erreur TMDb pour {item.title}: {exc}")
        self.refresh_library()
        self.statusBar().showMessage(f"{updated} média(s) enrichi(s) automatiquement.")

    def enrich_library_with_omdb(self) -> None:
        if not self.omdb.is_configured:
            QMessageBox.warning(self, "OMDb", "Ajoute OMDB_API_KEY dans un fichier .env pour récupérer les métadonnées.")
            return

        updated = 0
        for item in self.repository.list_media():
            try:
                before = (item.title, item.year, item.overview, item.genres, item.vote_average, item.poster_path)
                enriched = self.omdb.enrich_automatically(item)
                after = (
                    enriched.title,
                    enriched.year,
                    enriched.overview,
                    enriched.genres,
                    enriched.vote_average,
                    enriched.poster_path,
                )
                if after != before:
                    self.repository.upsert_media(enriched)
                    updated += 1
            except Exception as exc:
                self.statusBar().showMessage(f"Erreur OMDb pour {item.title}: {exc}")
        self.refresh_library()
        self.statusBar().showMessage(f"{updated} média(s) enrichi(s) avec OMDb.")

    def manual_search_current(self) -> None:
        if not self.current_item:
            return
        if not self.tmdb.is_configured:
            QMessageBox.warning(self, "TMDb", "Ajoute TMDB_API_KEY dans un fichier .env pour lancer la recherche.")
            return
        try:
            results = self.tmdb.search(self.current_item)
        except Exception as exc:
            QMessageBox.critical(self, "TMDb", f"Recherche impossible: {exc}")
            return
        dialog = ManualMatchDialog(self.current_item, results, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_result:
            item = apply_tmdb_result(self.current_item, dialog.selected_result)
            if item.poster_path:
                self.tmdb.download_poster(item.poster_path)
            self.repository.upsert_media(item)
            self.refresh_library()

    def refresh_library(self) -> None:
        self.items = self.repository.list_media()
        self.grid.clear()
        for index, item in enumerate(self.items):
            label = item.title
            if item.year:
                label += f"\n{item.year}"
            if item.media_type == "tv" and item.season and item.episode:
                label += f"\nS{item.season:02d}E{item.episode:02d}"
            list_item = QListWidgetItem(self._icon_for_item(item), label)
            list_item.setTextAlignment(Qt.AlignCenter)
            list_item.setData(Qt.UserRole, index)
            list_item.setSizeHint(QSize(180, 285))
            self.grid.addItem(list_item)
        if self.items:
            self.grid.setCurrentRow(0)
        else:
            self._show_empty_details()

    def show_media_count_status(self) -> None:
        self.statusBar().showMessage(f"{len(self.items)} média(s) trouvé(s).")

    def select_item(self, row: int) -> None:
        if row < 0 or row >= len(self.items):
            self.current_item = None
            return
        item = self.items[row]
        self.current_item = item
        self.title_label.setText(item.title)
        meta = [item.media_type.upper()]
        if item.year:
            meta.append(str(item.year))
        if item.vote_average:
            meta.append(f"{item.vote_average:.1f}/10")
        if item.media_type == "tv" and item.season and item.episode:
            meta.append(f"S{item.season:02d}E{item.episode:02d}")
        self.meta_label.setText(" | ".join(meta))
        self.overview_label.setText(item.overview or "Résumé non disponible.")
        self.path_label.setText(str(item.filepath))
        self._set_detail_poster(item)

    def play_current(self) -> None:
        if not self.current_item:
            return
        open_media(self.current_item.filepath)

    def _show_empty_details(self) -> None:
        self.current_item = None
        self.poster_label.setText("Aucune affiche")
        self.title_label.setText("Médiathèque vide")
        self.meta_label.setText("")
        self.overview_label.setText("Choisis un dossier puis lance un scan.")
        self.path_label.setText("")

    def _icon_for_item(self, item: MediaItem) -> QIcon:
        poster = local_poster_path(item.poster_path)
        if poster and poster.exists():
            return QIcon(str(poster))
        pixmap = QPixmap(150, 225)
        pixmap.fill(Qt.darkGray)
        return QIcon(pixmap)

    def _set_detail_poster(self, item: MediaItem) -> None:
        poster = local_poster_path(item.poster_path)
        if not poster or not poster.exists():
            self.poster_label.setText("Aucune affiche")
            self.poster_label.setPixmap(QPixmap())
            return
        pixmap = QPixmap(str(poster)).scaled(self.poster_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.poster_label.setText("")
        self.poster_label.setPixmap(pixmap)


class StartupDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Popcornana")
        self.setModal(True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        image_width = 286
        image_height = 286
        margin = 22
        width = image_width + margin * 2
        height = image_height + 172
        self.setFixedSize(width, height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(10)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        if STARTUP_IMAGE_PATH.exists():
            image = QPixmap(str(STARTUP_IMAGE_PATH)).scaled(
                image_width,
                image_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            image_label.setPixmap(image)
            image_width = image.width()
        image_label.setFixedSize(image_width, image_height)
        layout.addWidget(image_label, alignment=Qt.AlignHCenter)

        message_label = QLabel("actualisation de la bibliothèque")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setObjectName("startupMessage")
        message_label.setWordWrap(True)
        message_label.setFixedSize(image_width, 42)
        layout.addWidget(message_label, alignment=Qt.AlignHCenter)

        wait_label = QLabel("Merci de patienter")
        wait_label.setAlignment(Qt.AlignCenter)
        wait_label.setObjectName("startupWait")
        wait_label.setFixedWidth(image_width)
        layout.addWidget(wait_label, alignment=Qt.AlignHCenter)

        self.status_label = QLabel("scan en cours...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("startupStatus")
        self.status_label.setWordWrap(True)
        self.status_label.setFixedSize(image_width, 34)
        layout.addWidget(self.status_label, alignment=Qt.AlignHCenter)
        layout.addStretch()

        self.setStyleSheet(
            """
            QDialog {
                background: #151515;
                color: #EAEAEA;
                border: 1px solid #FF9800;
            }
            QLabel#startupMessage {
                color: #EAEAEA;
                font-size: 16px;
                font-weight: 700;
            }
            QLabel#startupWait {
                color: #EAEAEA;
                font-size: 13px;
                font-weight: 600;
            }
            QLabel#startupStatus {
                color: #FF9800;
                font-size: 12px;
                font-weight: 600;
            }
            """
        )

    def show_centered_over_parent(self) -> None:
        parent = self.parentWidget()
        if parent:
            parent_geometry = parent.frameGeometry()
            self.move(parent_geometry.center() - self.rect().center())
        self.show()

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)


class ManualMatchDialog(QDialog):
    def __init__(self, item: MediaItem, results: list[TmdbResult], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.selected_result: TmdbResult | None = None
        self.results = results
        self.setWindowTitle("Validation manuelle TMDb")
        self.resize(560, 420)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Fichier: {item.filepath.name}"))

        self.list_widget = QListWidget()
        for index, result in enumerate(results):
            year = f" ({result.year})" if result.year else ""
            row = QListWidgetItem(f"{result.title}{year} - score {result.score:.0f}")
            row.setData(Qt.UserRole, index)
            self.list_widget.addItem(row)
        if results:
            self.list_widget.setCurrentRow(0)
        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Ignore | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Ignore).clicked.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:
        row = self.list_widget.currentRow()
        if row >= 0:
            self.selected_result = self.results[row]
        super().accept()


def local_poster_path(poster_path: str | None) -> Path | None:
    if not poster_path:
        return None
    return POSTERS_DIR / poster_path.lstrip("/")


def media_signature(item: MediaItem) -> tuple:
    return (
        item.title,
        item.original_title,
        item.year,
        item.overview,
        item.genres,
        item.vote_average,
        item.poster_path,
        item.backdrop_path,
        item.tmdb_id,
    )


def build_stylesheet(theme: dict[str, str]) -> str:
    return f"""
        QMainWindow, QWidget#page {{
            background: {theme["BG"]};
            color: {theme["FG"]};
        }}
        QWidget#generalTab, QWidget#optionsTab {{
            background: {theme["BG"]};
        }}
        QWidget#detailsPanel, QWidget#optionSection {{
            background: {theme["PANEL"]};
            border-radius: 8px;
        }}
        QTabWidget#mainTabs::pane {{
            background: {theme["BG"]};
            border: none;
            top: -1px;
        }}
        QTabWidget#mainTabs::tab-bar {{
            alignment: left;
        }}
        QTabBar::tab {{
            background: {theme["PANEL"]};
            color: {theme["FG"]};
            border: 1px solid {theme["PANEL"]};
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 9px 18px;
            margin-right: 6px;
            font-weight: 700;
        }}
        QTabBar::tab:selected {{
            background: {theme["ACCENT"]};
            color: {theme["BG"]};
            border-color: {theme["ACCENT"]};
        }}
        QTabBar::tab:hover:!selected {{
            border-color: {theme["ACCENT"]};
        }}
        QStatusBar {{
            background: {theme["PANEL"]};
            color: {theme["FG"]};
            border: none;
        }}
        QLabel {{
            color: {theme["FG"]};
            background: transparent;
        }}
        QLabel#folderLabel, QLabel#pathLabel {{
            color: {theme["FG"]};
        }}
        QLabel#hintLabel {{
            color: {theme["FG"]};
        }}
        QLabel#themeLabel, QLabel#metaLabel, QLabel#sectionTitle {{
            color: {theme["ACCENT"]};
            font-weight: 700;
        }}
        QPushButton {{
            background: {theme["FIELD"]};
            color: {theme["FIELD_FG"]};
            border: 1px solid {theme["PANEL"]};
            border-radius: 6px;
            padding: 8px 12px;
            min-height: 24px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: {theme["ACCENT"]};
            color: {theme["BG"]};
            border-color: {theme["ACCENT"]};
        }}
        QPushButton:pressed {{
            background: {theme["PANEL"]};
            color: {theme["FG"]};
        }}
        QPushButton#sourceButton {{
            border: 2px solid {theme["PANEL"]};
            min-width: 88px;
        }}
        QPushButton#sourceButton:checked {{
            border: 2px solid {theme["ACCENT"]};
            color: {theme["ACCENT"]};
        }}
        QPushButton#sourceButton:checked:hover {{
            background: {theme["FIELD"]};
            color: {theme["ACCENT"]};
        }}
        QComboBox {{
            background: {theme["FIELD"]};
            color: {theme["FIELD_FG"]};
            border: 1px solid {theme["PANEL"]};
            border-radius: 6px;
            padding: 8px 10px;
            min-height: 24px;
            font-weight: 600;
        }}
        QComboBox:hover {{
            border-color: {theme["ACCENT"]};
        }}
        QComboBox QAbstractItemView {{
            background: {theme["FIELD"]};
            color: {theme["FIELD_FG"]};
            selection-background-color: {theme["ACCENT"]};
            selection-color: {theme["BG"]};
            outline: none;
        }}
        QListWidget#libraryGrid {{
            background: {theme["BG"]};
            color: {theme["FG"]};
            border: none;
        }}
        QListWidget#libraryGrid::item {{
            background: {theme["PANEL"]};
            color: {theme["FG"]};
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 8px;
        }}
        QListWidget#libraryGrid::item:selected {{
            background: {theme["ACCENT"]};
            color: {theme["BG"]};
            border-color: {theme["ACCENT"]};
        }}
        QLabel#posterLabel {{
            background: {theme["FIELD"]};
            color: {theme["FIELD_FG"]};
            border: 1px solid {theme["FIELD"]};
            border-radius: 4px;
        }}
        QScrollArea#overviewScroll {{
            background: transparent;
            border: none;
        }}
        QScrollArea#overviewScroll > QWidget > QWidget {{
            background: transparent;
        }}
        QScrollBar:vertical {{
            background: {theme["PANEL"]};
            width: 12px;
        }}
        QScrollBar::handle:vertical {{
            background: {theme["ACCENT"]};
            border-radius: 6px;
        }}
        QMessageBox, QDialog {{
            background: {theme["BG"]};
            color: {theme["FG"]};
        }}
    """


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Popcornana")
    window = MainWindow()
    startup = StartupDialog(window)

    def finish_startup() -> None:
        startup.close()

    def refresh_during_startup() -> None:
        startup.set_status("scan en cours...")
        QApplication.processEvents()
        removed = window.repository.delete_missing_media()
        window.refresh_library()
        if removed:
            startup.set_status(f"{len(window.items)} média(s), {removed} retiré(s)")
        else:
            startup.set_status(f"{len(window.items)} média(s) dans la bibliothèque")

    window.show()
    startup.show_centered_over_parent()
    QTimer.singleShot(100, refresh_during_startup)
    QTimer.singleShot(5000, finish_startup)
    sys.exit(app.exec())

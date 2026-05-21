from __future__ import annotations

from dataclasses import dataclass
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QSize, QTimer, Qt
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.repository import MediaRepository
from app.models.media import MediaItem
from app.omdb.client import OmdbClient, apply_omdb_result
from app.scanner.name_cleaner import is_video_file
from app.scanner.video_scanner import scan_videos
from app.tmdb.client import TmdbClient, apply_tmdb_result
from app.utils.paths import POSTERS_DIR, ensure_data_dirs, resource_path
from app.utils.player import open_media
from app.version import APP_VERSION


ASSETS_DIR = resource_path("assets")
LOGO_PATH = ASSETS_DIR / "popcornana.png"
STARTUP_IMAGE_PATH = ASSETS_DIR / "popcornana_ico.png"
APP_ICON_PATH = STARTUP_IMAGE_PATH
CATEGORY_LABELS = {
    "auto": "Auto",
    "movie": "Film",
    "tv": "Série",
    "ignore": "Ignorer",
}
CATEGORY_VALUES = {label: value for value, label in CATEGORY_LABELS.items()}

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


@dataclass
class LibraryEntry:
    kind: str
    title: str
    items: list[MediaItem]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        ensure_data_dirs()
        self.repository = MediaRepository()
        self.tmdb = TmdbClient()
        self.omdb = OmdbClient()
        self.items: list[MediaItem] = []
        self.current_item: MediaItem | None = None
        self.entries: list[LibraryEntry] = []
        self.current_entry: LibraryEntry | None = None
        self.current_series_title: str | None = None

        self.setWindowTitle(f"Popcornana {APP_VERSION}")
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.resize(1180, 760)
        self._build_ui()
        self._load_saved_state()

    def _build_ui(self) -> None:
        page = QWidget()
        page.setObjectName("page")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(18, 16, 18, 12)
        page_layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")

        self.grid = QListWidget()
        self.grid.setObjectName("libraryGrid")
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setIconSize(QSize(150, 225))
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setMovement(QListWidget.Static)
        self.grid.setSpacing(14)
        self.grid.setUniformItemSizes(True)
        self.grid.currentRowChanged.connect(self.select_item)
        self.grid.itemActivated.connect(self.activate_item)
        self.grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self.show_library_context_menu)

        self.back_button = QPushButton("Retour")
        self.back_button.clicked.connect(self.close_series_folder)
        self.back_button.setVisible(False)

        self.library_context_label = QLabel("Médiathèque")
        self.library_context_label.setObjectName("sectionTitle")

        library_header = QWidget()
        library_header_layout = QHBoxLayout(library_header)
        library_header_layout.setContentsMargins(0, 0, 0, 0)
        library_header_layout.setSpacing(8)
        library_header_layout.addWidget(self.back_button)
        library_header_layout.addWidget(self.library_context_label)
        library_header_layout.addStretch()

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

        self.play_button = QPushButton("Visionner")
        self.play_button.clicked.connect(self.play_current)

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
        details_layout.addWidget(self.play_button)

        general_tab = QWidget()
        general_tab.setObjectName("generalTab")
        general_layout = QHBoxLayout(general_tab)
        general_layout.setContentsMargins(0, 0, 0, 0)
        general_layout.setSpacing(18)
        library_panel = QWidget()
        library_layout = QVBoxLayout(library_panel)
        library_layout.setContentsMargins(0, 0, 0, 0)
        library_layout.setSpacing(8)
        library_layout.addWidget(library_header)
        library_layout.addWidget(self.grid, stretch=1)
        general_layout.addWidget(library_panel, stretch=1)
        general_layout.addWidget(details)
        self.tabs.addTab(general_tab, "Général")

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

        refresh_button = QPushButton("Actualiser")
        refresh_button.clicked.connect(self.refresh_current_folder)
        buttons_layout.addWidget(refresh_button)

        categories_button = QPushButton("Gérer les catégories")
        categories_button.clicked.connect(self.manage_categories)
        buttons_layout.addWidget(categories_button)

        enrich_button = QPushButton("Mettre à jour les fiches")
        enrich_button.clicked.connect(self.update_metadata_with_progress)
        buttons_layout.addWidget(enrich_button)

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

        advanced_header_layout = QHBoxLayout()
        advanced_header_layout.setContentsMargins(0, 0, 0, 0)
        advanced_header_layout.setSpacing(12)

        advanced_title = QLabel("Options avancées")
        advanced_title.setObjectName("sectionTitle")
        advanced_header_layout.addWidget(advanced_title)

        source_hint = QLabel("Sources utilisées par Mettre à jour les fiches. Si les deux sont sélectionnées, TMDb est essayé en premier, OMDb sert de secours.")
        source_hint.setObjectName("hintLabel")
        source_hint.setWordWrap(True)
        advanced_header_layout.addWidget(source_hint, stretch=1)
        advanced_layout.addLayout(advanced_header_layout)

        self.tmdb_source_button = QPushButton("TMDb")
        self.tmdb_source_button.setObjectName("sourceButton")
        self.tmdb_source_button.setCheckable(True)
        self.tmdb_source_button.toggled.connect(self.save_source_preferences)

        tmdb_key_layout = QHBoxLayout()
        tmdb_key_layout.setContentsMargins(0, 0, 0, 0)
        tmdb_key_layout.setSpacing(8)
        tmdb_key_layout.addWidget(self.tmdb_source_button)
        tmdb_key_label = QLabel("Clé TMDb")
        tmdb_key_label.setObjectName("fieldLabel")
        self.tmdb_key_field = QLineEdit()
        self.tmdb_key_field.setObjectName("apiKeyField")
        self.tmdb_key_field.setEchoMode(QLineEdit.Password)
        self.tmdb_key_field.setPlaceholderText("TMDB_API_KEY")
        self.tmdb_key_field.setMinimumWidth(180)
        self.tmdb_key_field.setMaximumWidth(240)
        tmdb_key_layout.addWidget(tmdb_key_label)
        tmdb_key_layout.addWidget(self.tmdb_key_field)
        save_tmdb_key_button = QPushButton("Enregistrer la clé API TMDb")
        save_tmdb_key_button.clicked.connect(self.save_tmdb_api_key)
        tmdb_key_layout.addWidget(save_tmdb_key_button)
        tmdb_key_layout.addStretch()
        advanced_layout.addLayout(tmdb_key_layout)

        self.omdb_source_button = QPushButton("OMDb")
        self.omdb_source_button.setObjectName("sourceButton")
        self.omdb_source_button.setCheckable(True)
        self.omdb_source_button.toggled.connect(self.save_source_preferences)

        omdb_key_layout = QHBoxLayout()
        omdb_key_layout.setContentsMargins(0, 0, 0, 0)
        omdb_key_layout.setSpacing(8)
        omdb_key_layout.addWidget(self.omdb_source_button)
        omdb_key_label = QLabel("Clé OMDb")
        omdb_key_label.setObjectName("fieldLabel")
        self.omdb_key_field = QLineEdit()
        self.omdb_key_field.setObjectName("apiKeyField")
        self.omdb_key_field.setEchoMode(QLineEdit.Password)
        self.omdb_key_field.setPlaceholderText("OMDB_API_KEY")
        self.omdb_key_field.setMinimumWidth(180)
        self.omdb_key_field.setMaximumWidth(240)
        omdb_key_layout.addWidget(omdb_key_label)
        omdb_key_layout.addWidget(self.omdb_key_field)
        save_omdb_key_button = QPushButton("Enregistrer la clé API OMDb")
        save_omdb_key_button.clicked.connect(self.save_omdb_api_key)
        omdb_key_layout.addWidget(save_omdb_key_button)
        omdb_key_layout.addStretch()
        advanced_layout.addLayout(omdb_key_layout)
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
        self.tabs.addTab(options_tab, "Options")

        page_layout.addWidget(self.tabs, stretch=1)
        self.setCentralWidget(page)

        self.setStatusBar(QStatusBar())
        self.show_media_count_status()

    def _load_saved_state(self) -> None:
        folder = self.repository.get_setting("media_folder")
        if folder:
            self.folder_label.setText(folder)
        self.load_source_preferences()
        self.load_api_keys()
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

    def load_api_keys(self) -> None:
        omdb_key = self.repository.get_setting("omdb_api_key") or self.omdb.api_key or ""
        tmdb_key = self.repository.get_setting("tmdb_api_key") or self.tmdb.api_key or ""
        self.omdb_key_field.setText(omdb_key)
        self.tmdb_key_field.setText(tmdb_key)
        self.omdb.set_api_key(omdb_key)
        self.tmdb.set_api_key(tmdb_key)

    def save_omdb_api_key(self) -> None:
        omdb_key = self.omdb_key_field.text().strip()
        self.repository.set_setting("omdb_api_key", omdb_key)
        self.omdb.set_api_key(omdb_key)
        self.statusBar().showMessage("Clé API OMDb enregistrée.")

    def save_tmdb_api_key(self) -> None:
        tmdb_key = self.tmdb_key_field.text().strip()
        self.tmdb.set_api_key(tmdb_key)
        self.repository.set_setting("tmdb_api_key", tmdb_key)
        self.statusBar().showMessage("Clé API TMDb enregistrée.")

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
        self.refresh_current_folder()

    def refresh_current_folder(self) -> None:
        folder = self.repository.get_setting("media_folder")
        if not folder:
            QMessageBox.information(self, "Popcornana", "Choisis d'abord un dossier de médias.")
            return

        root = Path(folder).expanduser()
        before_paths = {str(item.filepath) for item in self.repository.list_media()}
        scanned = scan_videos(root, self.repository.list_folder_categories())
        for item in scanned:
            self.repository.upsert_media(item)
        scanned_paths = {str(item.filepath) for item in scanned}
        removed = self.repository.delete_missing_media()
        removed += self.repository.delete_media_not_in_scan(root, scanned_paths)
        after_paths = {str(item.filepath) for item in self.repository.list_media()}
        added = len(after_paths - before_paths)
        self.refresh_library()

        message = f"{len(self.items)} média(s), {added} ajouté(s)"
        if removed:
            message += f", {removed} retiré(s)"
        message += "."
        self.statusBar().showMessage(message)

    def manage_categories(self) -> None:
        folder = self.repository.get_setting("media_folder")
        if not folder:
            QMessageBox.information(self, "Popcornana", "Choisis d'abord un dossier de médias.")
            return

        dialog = FolderCategoriesDialog(
            Path(folder).expanduser(),
            self.repository.list_folder_categories(),
            self,
        )
        if dialog.exec() != QDialog.Accepted:
            return

        for folder_path, category in dialog.selected_categories().items():
            self.repository.set_folder_category(folder_path, category)
        self.refresh_current_folder()

    def update_metadata_with_progress(self) -> None:
        self.tabs.setCurrentIndex(0)
        theme_name = self.repository.get_setting("theme") or DEFAULT_THEME
        progress = StartupDialog(
            THEMES.get(theme_name, THEMES[DEFAULT_THEME]),
            self,
            message="mise à jour des fiches",
            status="préparation...",
        )
        progress.show_centered_over_parent()
        QApplication.processEvents()
        try:
            self.enrich_library_with_selected_sources(progress.set_status)
        finally:
            progress.close()

    def enrich_library_with_selected_sources(self, progress_callback=None) -> None:
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
        skipped_locked = 0
        items = self.repository.list_media()
        total = len(items)
        for index, item in enumerate(items, start=1):
            if progress_callback:
                progress_callback(f"{index}/{total} - {item.title[:32]}")
                QApplication.processEvents()
            if item.metadata_locked:
                skipped_locked += 1
                continue
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
        message = f"{updated} média(s) enrichi(s) avec {' + '.join(sources)}."
        if skipped_locked:
            message += f" {skipped_locked} média(s) verrouillé(s) ignoré(s)."
        self.statusBar().showMessage(message)

    def enrich_library(self) -> None:
        if not self.tmdb.is_configured:
            QMessageBox.warning(self, "TMDb", "Ajoute TMDB_API_KEY dans un fichier .env pour récupérer les métadonnées.")
            return

        updated = 0
        for item in self.repository.list_media():
            if item.metadata_locked:
                continue
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
            if item.metadata_locked:
                continue
            try:
                before = (
                    item.title,
                    item.year,
                    item.overview,
                    item.genres,
                    item.director,
                    item.vote_average,
                    item.poster_path,
                )
                enriched = self.omdb.enrich_automatically(item)
                after = (
                    enriched.title,
                    enriched.year,
                    enriched.overview,
                    enriched.genres,
                    enriched.director,
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

    def search_tmdb_current(self) -> None:
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
        if not results:
            QMessageBox.information(self, "TMDb", "Aucun résultat trouvé.")
            return
        dialog = MetadataMatchDialog("TMDb", self.current_item, results, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_result:
            item = apply_tmdb_result(self.current_item, self.tmdb.with_director(dialog.selected_result))
            item.metadata_locked = True
            if item.poster_path:
                self.tmdb.download_poster(item.poster_path)
            self.repository.upsert_media(item)
            self.refresh_library()

    def search_omdb_current(self) -> None:
        if not self.current_item:
            return
        if not self.omdb.is_configured:
            QMessageBox.warning(self, "OMDb", "Ajoute OMDB_API_KEY dans un fichier .env pour lancer la recherche.")
            return
        try:
            results = self.omdb.search(self.current_item)
        except Exception as exc:
            QMessageBox.critical(self, "OMDb", f"Recherche impossible: {exc}")
            return
        if not results:
            QMessageBox.information(self, "OMDb", "Aucun résultat trouvé.")
            return
        dialog = MetadataMatchDialog("OMDb", self.current_item, results, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_result:
            previous_poster = self.current_item.poster_path
            item = apply_omdb_result(self.current_item, dialog.selected_result)
            poster = self.omdb.download_poster(dialog.selected_result)
            if poster:
                item.poster_path = str(poster.relative_to(POSTERS_DIR))
            else:
                item.poster_path = previous_poster
            item.metadata_locked = True
            self.repository.upsert_media(item)
            self.refresh_library()

    def edit_metadata_current(self) -> None:
        if not self.current_item:
            return
        dialog = ManualMetadataDialog(self.current_item, self)
        if dialog.exec() != QDialog.Accepted:
            return
        item = self.current_item
        item.title = dialog.title
        item.year = dialog.year
        item.director = dialog.director
        item.overview = dialog.overview
        item.metadata_locked = True
        if dialog.poster_path:
            saved_poster = save_manual_poster(dialog.poster_path)
            item.poster_path = str(saved_poster.relative_to(POSTERS_DIR))
        self.repository.upsert_media(item)
        self.refresh_library()

    def refresh_library(self) -> None:
        self.items = self.repository.list_media()
        if self.current_series_title and not self._series_items(self.current_series_title):
            self.current_series_title = None
        self.entries = self._visible_entries()
        self.grid.clear()
        self.back_button.setVisible(self.current_series_title is not None)
        self.library_context_label.setText(self.current_series_title or "Médiathèque")

        for index, entry in enumerate(self.entries):
            list_item = QListWidgetItem(self._icon_for_entry(entry), self._label_for_entry(entry))
            list_item.setTextAlignment(Qt.AlignCenter)
            list_item.setData(Qt.UserRole, index)
            list_item.setSizeHint(QSize(180, 285))
            self.grid.addItem(list_item)
        if self.entries:
            self.grid.setCurrentRow(0)
        else:
            self._show_empty_details()

    def show_media_count_status(self) -> None:
        self.statusBar().showMessage(f"{len(self.items)} média(s) trouvé(s).")

    def select_item(self, row: int) -> None:
        if row < 0 or row >= len(self.entries):
            self.current_item = None
            self.current_entry = None
            return
        entry = self.entries[row]
        self.current_entry = entry
        if entry.kind == "series":
            self._show_series_details(entry)
            return

        item = entry.items[0]
        self.current_item = item
        self.play_button.setText("Visionner")
        self.play_button.setEnabled(True)
        self.title_label.setText(item.title)
        meta = [item.media_type.upper()]
        if item.year:
            meta.append(str(item.year))
        if item.vote_average:
            meta.append(f"{item.vote_average:.1f}/10")
        if item.director:
            meta.append(f"Réalisateur: {item.director}")
        if item.media_type == "tv" and item.season and item.episode:
            meta.append(f"S{item.season:02d}E{item.episode:02d}")
        if item.metadata_locked:
            meta.append("MANUEL")
        self.meta_label.setText(" | ".join(meta))
        self.overview_label.setText(item.overview or "Résumé non disponible.")
        self.path_label.setText(str(item.filepath))
        self._set_detail_poster(item)

    def play_current(self) -> None:
        if self.current_entry and self.current_entry.kind == "series":
            self.open_series_folder(self.current_entry.title)
            return
        if not self.current_item:
            return
        open_media(self.current_item.filepath)

    def activate_item(self, _item: QListWidgetItem) -> None:
        if self.current_entry and self.current_entry.kind == "series":
            self.open_series_folder(self.current_entry.title)
        else:
            self.play_current()

    def show_library_context_menu(self, position: QPoint) -> None:
        list_item = self.grid.itemAt(position)
        if not list_item:
            return
        row = self.grid.row(list_item)
        if row < 0 or row >= len(self.entries):
            return
        self.grid.setCurrentRow(row)
        entry = self.entries[row]
        if entry.kind == "series":
            return

        menu = QMenu(self)
        tmdb_action = QAction("Recherche TMDb", self)
        tmdb_action.triggered.connect(self.search_tmdb_current)
        menu.addAction(tmdb_action)

        omdb_action = QAction("Recherche OMDb", self)
        omdb_action.triggered.connect(self.search_omdb_current)
        menu.addAction(omdb_action)

        manual_action = QAction("Recherche manuelle", self)
        manual_action.triggered.connect(self.edit_metadata_current)
        menu.addAction(manual_action)

        menu.exec(self.grid.mapToGlobal(position))

    def open_series_folder(self, title: str) -> None:
        self.current_series_title = title
        self.refresh_library()

    def close_series_folder(self) -> None:
        self.current_series_title = None
        self.refresh_library()

    def _show_empty_details(self) -> None:
        self.current_item = None
        self.current_entry = None
        self.poster_label.setText("Aucune affiche")
        self.title_label.setText("Médiathèque vide")
        self.meta_label.setText("")
        self.overview_label.setText("Choisis un dossier puis lance un scan.")
        self.path_label.setText("")
        self.play_button.setText("Visionner")
        self.play_button.setEnabled(False)

    def _show_series_details(self, entry: LibraryEntry) -> None:
        self.current_item = None
        seasons = sorted({item.season for item in entry.items if item.season})
        meta = ["SERIE", f"{len(entry.items)} épisode(s)"]
        if seasons:
            meta.append(f"{len(seasons)} saison(s)")
        self.title_label.setText(entry.title)
        self.meta_label.setText(" | ".join(meta))
        self.overview_label.setText("Ouvre la série pour afficher ses épisodes.")
        self.path_label.setText("")
        self.play_button.setText("Ouvrir la série")
        self.play_button.setEnabled(True)
        self._set_detail_poster(entry.items[0])

    def _visible_entries(self) -> list[LibraryEntry]:
        if self.current_series_title:
            return [
                LibraryEntry("episode", item.title, [item])
                for item in self._series_items(self.current_series_title)
            ]

        entries: list[LibraryEntry] = []
        series_groups: dict[str, list[MediaItem]] = {}
        series_titles: dict[str, str] = {}
        for item in self.items:
            if item.media_type == "tv":
                key = series_key(item.title)
                series_groups.setdefault(key, []).append(item)
                series_titles.setdefault(key, item.title)
            else:
                entries.append(LibraryEntry("movie", item.title, [item]))

        for key, group_items in series_groups.items():
            group_items.sort(key=episode_sort_key)
            entries.append(LibraryEntry("series", series_titles[key], group_items))

        return sorted(entries, key=lambda entry: entry.title.casefold())

    def _series_items(self, title: str) -> list[MediaItem]:
        key = series_key(title)
        episodes = [
            item for item in self.items
            if item.media_type == "tv" and series_key(item.title) == key
        ]
        return sorted(episodes, key=episode_sort_key)

    def _label_for_entry(self, entry: LibraryEntry) -> str:
        if entry.kind == "series":
            seasons = sorted({item.season for item in entry.items if item.season})
            season_label = f"{len(seasons)} saison(s)" if seasons else "Série"
            return f"{entry.title}\n{season_label}\n{len(entry.items)} épisode(s)"

        item = entry.items[0]
        label = item.title
        if item.year:
            label += f"\n{item.year}"
        if entry.kind == "episode" and item.season and item.episode:
            label += f"\nS{item.season:02d}E{item.episode:02d}"
        return label

    def _icon_for_entry(self, entry: LibraryEntry) -> QIcon:
        return self._icon_for_item(entry.items[0])

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
    def __init__(
        self,
        theme: dict[str, str],
        parent: QWidget | None = None,
        message: str = "actualisation de la bibliothèque",
        wait: str = "Merci de patienter",
        status: str = "scan en cours...",
    ) -> None:
        super().__init__(parent)
        self.theme = theme
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

        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setObjectName("startupMessage")
        message_label.setWordWrap(True)
        message_label.setFixedSize(image_width, 42)
        layout.addWidget(message_label, alignment=Qt.AlignHCenter)

        wait_label = QLabel(wait)
        wait_label.setAlignment(Qt.AlignCenter)
        wait_label.setObjectName("startupWait")
        wait_label.setFixedWidth(image_width)
        layout.addWidget(wait_label, alignment=Qt.AlignHCenter)

        self.status_label = QLabel(status)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("startupStatus")
        self.status_label.setWordWrap(True)
        self.status_label.setFixedSize(image_width, 34)
        layout.addWidget(self.status_label, alignment=Qt.AlignHCenter)
        layout.addStretch()

        self.apply_theme()

    def apply_theme(self) -> None:
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {self.theme["BG"]};
                color: {self.theme["FG"]};
                border: 1px solid {self.theme["ACCENT"]};
            }}
            QLabel#startupMessage {{
                color: {self.theme["FG"]};
                font-size: 16px;
                font-weight: 700;
            }}
            QLabel#startupWait {{
                color: {self.theme["FG"]};
                font-size: 13px;
                font-weight: 600;
            }}
            QLabel#startupStatus {{
                color: {self.theme["ACCENT"]};
                font-size: 12px;
                font-weight: 600;
            }}
            """
        )

    def show_centered_over_parent(self) -> None:
        parent = self.parentWidget()
        if parent:
            parent_geometry = parent.frameGeometry()
            position = parent_geometry.center() - self.rect().center()
            position.setY(max(parent_geometry.top() + 24, position.y() - 90))
            self.move(position)
        self.show()

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)


class MetadataMatchDialog(QDialog):
    def __init__(self, source_name: str, item: MediaItem, results: list, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.selected_result = None
        self.results = results
        self.setWindowTitle(f"Validation {source_name}")
        self.resize(560, 420)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Fichier: {item.filepath.name}"))

        self.list_widget = QListWidget()
        for index, result in enumerate(results):
            year = f" ({result.year})" if result.year else ""
            score = f" - score {result.score:.0f}" if result.score is not None else ""
            row = QListWidgetItem(f"{result.title}{year}{score}")
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


class FolderCategoriesDialog(QDialog):
    def __init__(self, root: Path, categories: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.root = root
        self.rows = discover_video_directories(root)
        self.category_combos: dict[str, QComboBox] = {}
        self.setWindowTitle("Gérer les catégories")
        self.resize(760, 520)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(len(self.rows), 3)
        self.table.setHorizontalHeaderLabels(["Répertoire", "Vidéos", "Catégorie"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().resizeSection(0, 470)
        self.table.horizontalHeader().resizeSection(1, 80)
        self.table.horizontalHeader().resizeSection(2, 150)

        for row_index, (folder_path, video_count) in enumerate(self.rows):
            folder_label = "Dossier racine" if folder_path == "." else folder_path
            folder_item = QTableWidgetItem(folder_label)
            folder_item.setFlags(folder_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            count_item = QTableWidgetItem(str(video_count))
            count_item.setFlags(count_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            combo = QComboBox()
            combo.addItems(CATEGORY_VALUES.keys())
            combo.setCurrentText(CATEGORY_LABELS.get(categories.get(folder_path, "auto"), "Auto"))

            self.table.setItem(row_index, 0, folder_item)
            self.table.setItem(row_index, 1, count_item)
            self.table.setCellWidget(row_index, 2, combo)
            self.category_combos[folder_path] = combo

        layout.addWidget(self.table)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_categories(self) -> dict[str, str]:
        return {
            folder_path: CATEGORY_VALUES[combo.currentText()]
            for folder_path, combo in self.category_combos.items()
        }


class ManualMetadataDialog(QDialog):
    def __init__(self, item: MediaItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.poster_path: Path | None = None
        self.title = item.title
        self.year = item.year
        self.director = item.director
        self.overview = item.overview
        self.setWindowTitle("Recherche manuelle")
        self.resize(620, 520)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Fichier: {item.filepath.name}"))

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        title_layout.addWidget(QLabel("Titre"))
        self.title_field = QLineEdit(item.title)
        title_layout.addWidget(self.title_field, stretch=1)
        layout.addLayout(title_layout)

        year_layout = QHBoxLayout()
        year_layout.setContentsMargins(0, 0, 0, 0)
        year_layout.setSpacing(8)
        year_layout.addWidget(QLabel("Année"))
        self.year_field = QLineEdit(str(item.year) if item.year else "")
        self.year_field.setPlaceholderText("ex: 1999")
        year_layout.addWidget(self.year_field, stretch=1)
        layout.addLayout(year_layout)

        director_layout = QHBoxLayout()
        director_layout.setContentsMargins(0, 0, 0, 0)
        director_layout.setSpacing(8)
        director_layout.addWidget(QLabel("Réalisateur"))
        self.director_field = QLineEdit(item.director or "")
        director_layout.addWidget(self.director_field, stretch=1)
        layout.addLayout(director_layout)

        layout.addWidget(QLabel("Résumé"))
        self.overview_field = QTextEdit()
        self.overview_field.setPlainText(item.overview or "")
        layout.addWidget(self.overview_field, stretch=1)

        poster_layout = QHBoxLayout()
        poster_layout.setContentsMargins(0, 0, 0, 0)
        poster_layout.setSpacing(8)
        self.poster_label_field = QLineEdit()
        self.poster_label_field.setReadOnly(True)
        self.poster_label_field.setPlaceholderText("Aucune nouvelle affiche choisie")
        browse_button = QPushButton("Parcourir")
        browse_button.clicked.connect(self.choose_poster)
        poster_layout.addWidget(QLabel("Affiche"))
        poster_layout.addWidget(self.poster_label_field, stretch=1)
        poster_layout.addWidget(browse_button)
        layout.addLayout(poster_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def choose_poster(self) -> None:
        filename, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Choisir une affiche",
            "",
            "Images (*.png *.jpg *.jpeg *.webp)",
        )
        if not filename:
            return
        self.poster_path = Path(filename)
        self.poster_label_field.setText(filename)

    def accept(self) -> None:
        title = self.title_field.text().strip()
        if not title:
            QMessageBox.warning(self, "Recherche manuelle", "Le titre ne peut pas être vide.")
            return

        year_text = self.year_field.text().strip()
        year = None
        if year_text:
            if not year_text.isdigit() or len(year_text) != 4:
                QMessageBox.warning(self, "Recherche manuelle", "L'année doit contenir 4 chiffres.")
                return
            year = int(year_text)

        self.title = title
        self.year = year
        self.director = self.director_field.text().strip() or None
        self.overview = self.overview_field.toPlainText().strip() or None
        super().accept()


def local_poster_path(poster_path: str | None) -> Path | None:
    if not poster_path:
        return None
    path = Path(poster_path)
    if path.is_absolute():
        return path
    return POSTERS_DIR / poster_path.lstrip("/")


def discover_video_directories(root: Path) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for path in sorted(root.rglob("*")):
        if not is_video_file(path):
            continue
        try:
            relative_parent = path.parent.relative_to(root)
        except ValueError:
            continue
        for directory in (relative_parent, *relative_parent.parents):
            key = "." if str(directory) == "." else directory.as_posix()
            counts[key] = counts.get(key, 0) + 1

    return sorted(counts.items(), key=lambda item: (item[0] != ".", item[0].casefold()))


def save_manual_poster(source: Path) -> Path:
    target_dir = POSTERS_DIR / "manual"
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.lower() or ".jpg"
    base_name = "".join(char if char.isalnum() else "_" for char in source.stem).strip("_") or "poster"
    target = target_dir / f"{base_name}{suffix}"
    counter = 1
    while target.exists():
        target = target_dir / f"{base_name}_{counter}{suffix}"
        counter += 1
    shutil.copy2(source, target)
    return target


def media_signature(item: MediaItem) -> tuple:
    return (
        item.title,
        item.original_title,
        item.year,
        item.overview,
        item.genres,
        item.director,
        item.vote_average,
        item.poster_path,
        item.backdrop_path,
        item.tmdb_id,
    )


def series_key(title: str) -> str:
    return " ".join(title.casefold().split())


def episode_sort_key(item: MediaItem) -> tuple:
    return (
        item.season if item.season is not None else 999,
        item.episode if item.episode is not None else 999,
        item.title.casefold(),
        str(item.filepath).casefold(),
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
        QLabel#fieldLabel {{
            color: {theme["FG"]};
            min-width: 72px;
            font-weight: 700;
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
        QLineEdit#apiKeyField {{
            background: {theme["FIELD"]};
            color: {theme["FIELD_FG"]};
            border: 1px solid {theme["PANEL"]};
            border-radius: 6px;
            padding: 8px 10px;
            min-height: 24px;
            font-weight: 600;
        }}
        QLineEdit#apiKeyField:hover, QLineEdit#apiKeyField:focus {{
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
    theme_name = window.repository.get_setting("theme") or DEFAULT_THEME
    startup = StartupDialog(THEMES.get(theme_name, THEMES[DEFAULT_THEME]), window)

    def force_full_screen() -> None:
        window.setWindowState(window.windowState() | Qt.WindowFullScreen)
        window.showFullScreen()
        window.raise_()
        window.activateWindow()

    def finish_startup() -> None:
        startup.close()
        force_full_screen()

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
    QTimer.singleShot(0, force_full_screen)
    QTimer.singleShot(100, refresh_during_startup)
    QTimer.singleShot(5000, finish_startup)
    sys.exit(app.exec())

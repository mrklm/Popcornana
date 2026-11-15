"""Fenêtre de comparaison de deux sources, paire de vidéos par paire de vidéos."""
from __future__ import annotations

import html
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QInputDialog,
    QLabel, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from app.utils.source_compare import (
    Choice, SideFiles, editable_name, format_size, row_files, row_identical, row_keys, validate_name,
)

ROW_LABELS = {"video": "Fichier vidéo", "folder": "Dossier", "cover": "Image (cover)"}
LANGUAGE_LABELS = {"fr": "français", "en": "anglais", "": "sans langue"}
PREVIEW_SIZE = (150, 220)


def row_label(key: str) -> str:
    if key.startswith("sub:"):
        return f"Sous-titre ({LANGUAGE_LABELS.get(key[4:], key[4:])})"
    return ROW_LABELS[key]


class CompareCard(QFrame):
    clicked = Signal()
    rename_requested = Signal()

    def __init__(self, key: str, side: SideFiles, theme: dict[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.key = key
        self.theme = theme
        self.path = row_files(side, key)
        self.available = self.path is not None and (key != "folder" or side.folder_renamable)
        self.setObjectName("compareCard")
        self.setCursor(Qt.PointingHandCursor if self.available else Qt.ArrowCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        caption = QLabel(row_label(key))
        caption.setStyleSheet(f"color: {theme['ACCENT']}; font-weight: 600;")
        layout.addWidget(caption)

        self.dimensions = ""
        text_layout = layout
        if key == "cover" and self.path is not None:
            # Aperçu à gauche, informations à droite : la ligne reste compacte.
            body = QHBoxLayout()
            body.setSpacing(14)
            preview = QLabel()
            preview.setAlignment(Qt.AlignCenter)
            preview.setFixedSize(*PREVIEW_SIZE)
            pixmap = QPixmap(str(self.path))
            if not pixmap.isNull():
                preview.setPixmap(pixmap.scaled(*PREVIEW_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.dimensions = f"{pixmap.width()} × {pixmap.height()} px"
            else:
                preview.setText("Aperçu indisponible")
            body.addWidget(preview)
            text_layout = QVBoxLayout()
            body.addLayout(text_layout, stretch=1)
            layout.addLayout(body)

        self.name_label = QLabel()
        self.name_label.setWordWrap(True)
        self.name_label.setTextFormat(Qt.RichText)
        self.name_label.setTextInteractionFlags(Qt.NoTextInteraction)
        text_layout.addWidget(self.name_label)
        self.detail_label = QLabel(self._details(side))
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("color: gray;")
        text_layout.addWidget(self.detail_label)
        if text_layout is not layout:
            text_layout.addStretch()

        self.rename_button = None
        if key != "cover" and self.available:
            self.rename_button = QPushButton("Renommer…")
            self.rename_button.setCursor(Qt.PointingHandCursor)
            self.rename_button.clicked.connect(self.rename_requested.emit)
            layout.addWidget(self.rename_button, alignment=Qt.AlignLeft)
        layout.addStretch()
        self.set_state(False, None)

    def _details(self, side: SideFiles) -> str:
        if self.path is None:
            return "Absent"
        if self.key == "folder":
            return "Racine de la source : non renommable" if not side.folder_renamable else ""
        try:
            size = self.path.stat().st_size
        except OSError:
            return ""
        text = format_size(size)
        if self.key == "video":
            text += f"  ({size:,} octets)".replace(",", " ")
        if self.key == "cover" and self.dimensions:
            text += "\n" + self.dimensions
        return text

    def set_state(self, selected: bool, new_name: str | None) -> None:
        border = f"3px solid {self.theme['ACCENT']}" if selected else f"1px solid {self.theme['FIELD']}"
        background = self.theme["PANEL"] if self.available else self.theme["BG"]
        self.setStyleSheet(f"QFrame#compareCard {{ border: {border}; border-radius: 8px; background: {background}; }}")
        name = html.escape(self.path.name) if self.path is not None else "—"
        if new_name is not None and self.path is not None:
            suffix = "" if self.key == "folder" else self.path.suffix
            name = f"<b>{html.escape(new_name + suffix)}</b><br><i>(nouveau nom)</i>"
        self.name_label.setText(name)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self.available:
            self.clicked.emit()
        super().mousePressEvent(event)


class SourceCompareDialog(QDialog):
    def __init__(
        self,
        pairs: list[dict[str, SideFiles]],
        theme: dict[str, str],
        apply_choices: Callable[[dict[str, SideFiles], dict[str, Choice]], str | None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.pairs = pairs
        self.theme = theme
        self.apply_choices = apply_choices
        self.index = 0
        self.saved = 0
        self.skipped = 0
        self.choices: dict[str, Choice] = {}
        self.cards: dict[str, dict[str, CompareCard]] = {}
        self.setWindowTitle("Comparer les sources")
        self.resize(1100, 820)

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.counter_label = QLabel()
        self.counter_label.setStyleSheet("font-weight: 700; font-size: 16px;")
        top.addWidget(self.counter_label)
        top.addStretch()
        skip_button = QPushButton("Passer")
        skip_button.setToolTip("Ignorer cette comparaison sans rien modifier")
        skip_button.clicked.connect(self.skip_pair)
        top.addWidget(skip_button)
        close_button = QPushButton("Fermer")
        close_button.setToolTip("Arrêter la comparaison. Les paires déjà enregistrées sont conservées.")
        close_button.clicked.connect(self.reject)
        top.addWidget(close_button)
        layout.addLayout(top)

        headers = QHBoxLayout()
        self.left_header = QLabel()
        self.right_header = QLabel()
        for label in (self.left_header, self.right_header):
            label.setWordWrap(True)
            label.setStyleSheet("font-weight: 600;")
            headers.addWidget(label, stretch=1)
        layout.addLayout(headers)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(self.scroll, stretch=1)

        bottom = QHBoxLayout()
        hint = QLabel("Cliquez sur la version à conserver pour chaque élément. Les éléments non choisis restent inchangés.")
        hint.setWordWrap(True)
        bottom.addWidget(hint, stretch=1)
        self.save_button = QPushButton("Enregistrer")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.save_pair)
        bottom.addWidget(self.save_button)
        layout.addLayout(bottom)
        self.load_pair()

    def load_pair(self) -> None:
        if self.index >= len(self.pairs):
            self.accept()
            return
        sides = self.pairs[self.index]
        self.choices = {}
        self.cards = {}
        self.counter_label.setText(f"Comparaison {self.index + 1} / {len(self.pairs)}")
        self.left_header.setText(f"Source : {sides['left'].root}")
        self.right_header.setText(f"Source : {sides['right'].root}")

        content = QWidget()
        content.setObjectName("compareContent")
        content.setStyleSheet(f"QWidget#compareContent {{ background: {self.theme['BG']}; }}")
        grid = QGridLayout(content)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        for row, key in enumerate(row_keys(sides["left"], sides["right"])):
            identical = row_identical(sides["left"], sides["right"], key)
            self.cards[key] = {}
            for column, side_name in enumerate(("left", "right")):
                card = CompareCard(key, sides[side_name], self.theme)
                card.clicked.connect(lambda key=key, side_name=side_name: self.choose(key, side_name))
                card.rename_requested.connect(lambda key=key, side_name=side_name: self.rename(key, side_name))
                self.cards[key][side_name] = card
                grid.addWidget(card, row, column)
            if identical:
                for card in self.cards[key].values():
                    card.set_state(card.available, None)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(grid.rowCount(), 1)
        self.scroll.setWidget(content)

    def _refresh_row(self, key: str) -> None:
        choice = self.choices.get(key)
        for side_name, card in self.cards[key].items():
            selected = choice is not None and choice.side == side_name
            original = editable_name(card.path, key) if card.path is not None else None
            renamed = choice.name if selected and choice.name != original else None
            card.set_state(selected, renamed)

    def choose(self, key: str, side_name: str) -> None:
        card = self.cards[key][side_name]
        sides = self.pairs[self.index]
        if row_identical(sides["left"], sides["right"], key) and key not in self.choices:
            return
        current = self.choices.get(key)
        if current is not None and current.side == side_name:
            return
        self.choices[key] = Choice(side_name, editable_name(card.path, key))
        self._refresh_row(key)

    def rename(self, key: str, side_name: str) -> None:
        card = self.cards[key][side_name]
        current = self.choices.get(key)
        default = current.name if current is not None and current.side == side_name else editable_name(card.path, key)
        extension = "" if key == "folder" else f"\n(l’extension {card.path.suffix} est conservée)"
        name, accepted = QInputDialog.getText(self, "Renommer", f"Nouveau nom pour les deux sources :{extension}", text=default)
        if not accepted:
            return
        name = name.strip()
        error = validate_name(name)
        if error:
            QMessageBox.warning(self, "Renommer", error)
            return
        self.choices[key] = Choice(side_name, name)
        self._refresh_row(key)

    def skip_pair(self) -> None:
        self.skipped += 1
        self.index += 1
        self.load_pair()

    def save_pair(self) -> None:
        if not self.choices:
            self.skip_pair()
            return
        error = self.apply_choices(self.pairs[self.index], dict(self.choices))
        if error:
            QMessageBox.warning(self, "Comparer les sources", error)
            return
        self.saved += 1
        self.index += 1
        self.load_pair()


class SourcePairDialog(QDialog):
    """Choix des deux sources à comparer."""

    def __init__(self, sources: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Comparer les sources")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Choisissez les deux sources à comparer :"))
        form = QFormLayout()
        self.left_combo = QComboBox()
        self.right_combo = QComboBox()
        for combo in (self.left_combo, self.right_combo):
            combo.addItems(sources)
            combo.setMinimumWidth(420)
        self.right_combo.setCurrentIndex(1 if len(sources) > 1 else 0)
        form.addRow("Source de gauche", self.left_combo)
        form.addRow("Source de droite", self.right_combo)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected(self) -> tuple[Path, Path]:
        return Path(self.left_combo.currentText()).expanduser(), Path(self.right_combo.currentText()).expanduser()

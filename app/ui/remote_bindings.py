"""Boutons de télécommande assignés par l'utilisateur, en plus des boutons par défaut."""
from __future__ import annotations

import json
from typing import Callable

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import (
    QAbstractSpinBox, QApplication, QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

SETTING_KEY = "remote_bindings"


def _int(value) -> int:
    """Valeur entière d'une énumération Qt (PySide6 6.2 comme versions récentes)."""
    try:
        return int(value)
    except TypeError:
        return int(value.value)


# (action, libellé, boutons par défaut affichés)
ACTIONS = (
    ("up", "Flèche haut", "Flèche haut"),
    ("down", "Flèche bas", "Flèche bas"),
    ("left", "Flèche gauche", "Flèche gauche"),
    ("right", "Flèche droite", "Flèche droite"),
    ("validate", "Valider (OK)", "Entrée, Entrée du pavé numérique, Select"),
    ("back", "Retour", "Échap, Retour, Effacement arrière, bouton souris Précédent, appui long sur le clic droit"),
    ("menu", "Menu d’édition", "Clic droit, touche Menu"),
    ("home", "Accueil (début de la bibliothèque)", "Touche Accueil"),
    ("page_up", "Page précédente", "Page précédente"),
    ("page_down", "Page suivante", "Page suivante"),
    ("zoom_in", "Zoom +", "Ctrl +, Zoom +"),
    ("zoom_out", "Zoom −", "Ctrl −, Zoom −"),
    ("fullscreen", "Plein écran", "F11"),
)
ACTION_LABELS = {action: label for action, label, _ in ACTIONS}

# Actions traduites en touche par défaut : la fenêtre la traite comme si elle avait été pressée.
ACTION_KEYS = {
    "up": Qt.Key_Up, "down": Qt.Key_Down, "left": Qt.Key_Left, "right": Qt.Key_Right,
    "validate": Qt.Key_Return, "back": Qt.Key_Escape, "page_up": Qt.Key_PageUp, "page_down": Qt.Key_PageDown,
}

MODIFIER_MASK = _int(Qt.ShiftModifier) | _int(Qt.ControlModifier) | _int(Qt.AltModifier) | _int(Qt.MetaModifier)
MODIFIER_KEYS = {_int(k) for k in (
    Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta, Qt.Key_AltGr, Qt.Key_CapsLock, Qt.Key_NumLock,
)}
UNKNOWN_KEYS = {0, _int(Qt.Key_unknown)}
LEFT_BUTTON = f"mouse:{_int(Qt.LeftButton)}"
MOUSE_NAMES = {
    _int(Qt.RightButton): "Clic droit",
    _int(Qt.MiddleButton): "Clic milieu",
    _int(Qt.BackButton): "Bouton souris Précédent",
    _int(Qt.ForwardButton): "Bouton souris Suivant",
}


def _key(code, modifiers: int = 0) -> str:
    return f"key:{_int(code)}:{modifiers}"


DEFAULT_INPUTS = {
    _key(Qt.Key_Up): "up", _key(Qt.Key_Down): "down", _key(Qt.Key_Left): "left", _key(Qt.Key_Right): "right",
    _key(Qt.Key_Return): "validate", _key(Qt.Key_Enter): "validate", _key(Qt.Key_Select): "validate",
    _key(Qt.Key_Escape): "back", _key(Qt.Key_Back): "back", _key(Qt.Key_Backspace): "back",
    f"mouse:{_int(Qt.BackButton)}": "back",
    f"mouse:{_int(Qt.RightButton)}": "menu", _key(Qt.Key_Menu): "menu",
    _key(Qt.Key_HomePage): "home",
    _key(Qt.Key_PageUp): "page_up", _key(Qt.Key_PageDown): "page_down",
    _key(Qt.Key_ZoomIn): "zoom_in", _key(Qt.Key_ZoomOut): "zoom_out",
    _key(Qt.Key_F11): "fullscreen",
}


def key_binding(event) -> str | None:
    """Identifiant d'une touche pressée ; None pour une touche de modification seule."""
    code = _int(event.key())
    if code in MODIFIER_KEYS:
        return None
    modifiers = _int(event.modifiers()) & MODIFIER_MASK
    if code in UNKNOWN_KEYS:
        native = int(event.nativeVirtualKey())
        return f"native:{native}:{modifiers}" if native else None
    return _key(code, modifiers)


def mouse_binding(event) -> str:
    return f"mouse:{_int(event.button())}"


def describe(binding: str) -> str:
    kind, _, rest = binding.partition(":")
    if kind == "mouse":
        number = int(rest)
        return MOUSE_NAMES.get(number, f"Bouton souris {number.bit_length()}")
    code, _, modifiers = rest.partition(":")
    if kind == "native":
        return f"Touche spéciale (code {code})"
    try:
        text = QKeySequence(int(code) | int(modifiers or 0)).toString(QKeySequence.NativeText)
    except (TypeError, ValueError):
        text = ""
    return text or f"Touche {int(code):#x}"


def is_text_input(widget: QWidget | None) -> bool:
    if isinstance(widget, (QLineEdit, QAbstractSpinBox)):
        return True
    if isinstance(widget, (QTextEdit, QPlainTextEdit)):
        return not widget.isReadOnly()
    return isinstance(widget, QComboBox) and widget.isEditable()


class RemoteBindings(QObject):
    """Filtre d'application : un bouton assigné déclenche l'action comme son bouton par défaut."""

    def __init__(self, handlers: dict[str, Callable[[], None]], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.handlers = handlers
        self.bindings: dict[str, list[str]] = {}
        self.lookup: dict[str, str] = {}
        self.paused = False

    def load(self, text: str | None) -> None:
        try:
            data = json.loads(text) if text else {}
        except ValueError:
            data = {}
        self.bindings = {}
        for action, bindings in (data.items() if isinstance(data, dict) else ()):
            if action in ACTION_LABELS and isinstance(bindings, list):
                self.bindings[action] = [b for b in bindings if isinstance(b, str) and b not in DEFAULT_INPUTS]
        self._rebuild()

    def dump(self) -> str:
        return json.dumps({action: bindings for action, bindings in self.bindings.items() if bindings})

    def _rebuild(self) -> None:
        self.lookup = {binding: action for action, bindings in self.bindings.items() for binding in bindings}

    def check(self, action: str, binding: str) -> str | None:
        """Message d'erreur si le bouton ne peut pas être assigné à cette action."""
        if binding == LEFT_BUTTON:
            return "Le clic gauche est réservé à la souris."
        name = describe(binding)
        owner = DEFAULT_INPUTS.get(binding)
        if owner == action:
            return f"« {name} » est déjà un bouton par défaut de cette action."
        if owner is not None:
            return f"« {name} » est déjà utilisé par défaut pour « {ACTION_LABELS[owner]} »."
        owner = self.lookup.get(binding)
        if owner == action:
            return f"« {name} » est déjà assigné à cette action."
        if owner is not None:
            return f"« {name} » est déjà assigné à « {ACTION_LABELS[owner]} »."
        return None

    def add(self, action: str, binding: str) -> str | None:
        error = self.check(action, binding)
        if error is None:
            self.bindings.setdefault(action, []).append(binding)
            self._rebuild()
        return error

    def clear(self, action: str | None = None) -> None:
        if action is None:
            self.bindings = {}
        else:
            self.bindings.pop(action, None)
        self._rebuild()

    def eventFilter(self, watched, event) -> bool:
        if self.paused or not self.lookup:
            return False
        kind = event.type()
        if kind in (QEvent.KeyPress, QEvent.KeyRelease, QEvent.ShortcutOverride):
            action = self.lookup.get(key_binding(event) or "")
            if action is None or is_text_input(QApplication.focusWidget()):
                return False
            if kind == QEvent.ShortcutOverride:
                event.accept()  # Le bouton assigné l'emporte sur un éventuel raccourci.
            elif kind == QEvent.KeyPress:
                self.trigger(action, watched if isinstance(watched, QWidget) else None, event.isAutoRepeat())
            return True
        if kind in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick, QEvent.MouseButtonRelease):
            action = self.lookup.get(mouse_binding(event))
            if action is None:
                return False
            if kind == QEvent.MouseButtonRelease:
                self.trigger(action, None, False)
            return True
        return False

    def trigger(self, action: str, receiver: QWidget | None, repeat: bool) -> None:
        key = ACTION_KEYS.get(action)
        if key is not None:
            target = receiver or QApplication.focusWidget() or QApplication.activeWindow()
            if target is not None:
                for kind in (QEvent.KeyPress, QEvent.KeyRelease):
                    QApplication.sendEvent(target, QKeyEvent(kind, key, Qt.NoModifier, "", repeat))
            return
        if QApplication.activeModalWidget() is not None:
            return  # Menu, accueil, zoom et plein écran ne concernent que la fenêtre principale.
        handler = self.handlers.get(action)
        if handler is not None:
            handler()


class RemoteCaptureDialog(QDialog):
    """Attend l'appui sur un bouton de télécommande et retient son identifiant."""

    def __init__(self, action_label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.binding: str | None = None
        self.setWindowTitle("Assigner un bouton")
        layout = QVBoxLayout(self)
        message = QLabel(
            f"Appuyez sur le bouton de la télécommande à assigner à « {action_label} ».\n\n"
            "Le bouton choisi s’ajoute aux boutons par défaut."
        )
        message.setWordWrap(True)
        message.setMinimumWidth(380)
        layout.addWidget(message)
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Annuler")
        cancel.setFocusPolicy(Qt.NoFocus)  # Entrée et Espace doivent pouvoir être capturés.
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)
        QApplication.instance().installEventFilter(self)

    def done(self, result: int) -> None:
        QApplication.instance().removeEventFilter(self)
        super().done(result)

    def eventFilter(self, watched, event) -> bool:
        kind = event.type()
        if kind == QEvent.ShortcutOverride:
            event.accept()
            return True
        if kind == QEvent.KeyPress:
            binding = key_binding(event)
            if binding is not None and not event.isAutoRepeat():
                self.binding = binding
                self.accept()
            return True
        if kind in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick, QEvent.MouseButtonRelease):
            if event.button() == Qt.LeftButton:
                return False
            if kind == QEvent.MouseButtonRelease:  # Le relâchement ne doit pas atteindre la grille.
                self.binding = mouse_binding(event)
                self.accept()
            return True
        if kind == QEvent.ContextMenu:
            return True
        return False

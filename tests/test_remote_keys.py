import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt
from PySide6.QtCore import QPointF
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QApplication

from app.ui.main_window import FullscreenEntryDialog, MainWindow


def key(code, repeat=False):
    return QKeyEvent(QEvent.KeyPress, code, Qt.NoModifier, "", repeat)


class RemoteKeysTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_enter_on_grid_activates_current_item(self):
        # Sous macOS, Qt n'émet pas itemActivated : la grille doit gérer Entrée elle-même.
        for code in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
            window = Mock()
            item = object()
            window.grid.currentItem.return_value = item
            self.assertTrue(MainWindow.eventFilter(window, window.grid, key(code)))
            window.activate_item.assert_called_once_with(item)

    def test_enter_auto_repeat_ignored(self):
        window = Mock()
        self.assertTrue(MainWindow.eventFilter(window, window.grid, key(Qt.Key_Return, repeat=True)))
        window.activate_item.assert_not_called()

    def test_back_keys_on_grid_leave_folder(self):
        for code in (Qt.Key_Back, Qt.Key_Escape, Qt.Key_Backspace):
            window = Mock()
            self.assertTrue(MainWindow.eventFilter(window, window.grid, key(code)))
            window.navigate_library_back.assert_called_once_with()
        window = Mock()
        MainWindow.eventFilter(window, window.grid, key(Qt.Key_Escape, repeat=True))
        window.navigate_library_back.assert_not_called()

    def test_back_mouse_button_on_grid_leaves_folder(self):
        window = Mock()
        point = QPointF(5, 5)
        for event_type in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
            event = QMouseEvent(event_type, point, point, Qt.BackButton, Qt.BackButton, Qt.NoModifier)
            self.assertTrue(MainWindow.eventFilter(window, window.grid.viewport(), event))
        window.navigate_library_back.assert_called_once_with()

    def test_enter_in_sheet_clicks_selected_button(self):
        dialog = Mock()
        dialog.return_button.isDefault.return_value = False
        self.assertTrue(FullscreenEntryDialog.eventFilter(dialog, Mock(), key(Qt.Key_Enter)))
        dialog.watch_button.click.assert_called_once_with()
        dialog.return_button.click.assert_not_called()

        dialog = Mock()
        dialog.return_button.isDefault.return_value = True
        FullscreenEntryDialog.eventFilter(dialog, Mock(), key(Qt.Key_Return))
        dialog.return_button.click.assert_called_once_with()

    def test_arrows_switch_button_without_focus(self):
        dialog = Mock()
        dialog.return_button.isDefault.return_value = False
        self.assertTrue(FullscreenEntryDialog.eventFilter(dialog, Mock(), key(Qt.Key_Left)))
        dialog.return_button.setDefault.assert_called_once_with(True)


if __name__ == "__main__":
    unittest.main()

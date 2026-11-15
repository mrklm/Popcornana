import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget

from app.ui.remote_bindings import RemoteBindings, RemoteCaptureDialog, _int, describe

F5 = f"key:{_int(Qt.Key_F5)}:0"
BACK_MOUSE = f"mouse:{_int(Qt.BackButton)}"
FORWARD_MOUSE = f"mouse:{_int(Qt.ForwardButton)}"


def key(code, kind=QEvent.KeyPress):
    return QKeyEvent(kind, code, Qt.NoModifier, "")


def mouse(kind, button):
    point = QPointF(3, 3)
    return QMouseEvent(kind, point, point, button, button, Qt.NoModifier)


class Recorder(QWidget):
    def __init__(self):
        super().__init__()
        self.keys = []

    def keyPressEvent(self, event):
        self.keys.append(event.key())


class RemoteBindingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_add_checks_conflicts_and_round_trips(self):
        remote = RemoteBindings({})
        self.assertIsNone(remote.add("up", F5))
        self.assertIn("déjà assigné à « Flèche haut »", remote.add("down", F5))
        self.assertIn("déjà assigné à cette action", remote.add("up", F5))
        self.assertIn("par défaut pour « Retour »", remote.add("menu", BACK_MOUSE))
        self.assertIn("déjà un bouton par défaut", remote.add("back", BACK_MOUSE))
        self.assertIn("clic gauche", remote.add("back", f"mouse:{_int(Qt.LeftButton)}"))
        other = RemoteBindings({})
        other.load(remote.dump())
        self.assertEqual(other.lookup, {F5: "up"})
        other.load("pas du json")
        self.assertEqual(other.bindings, {})
        remote.clear("up")
        self.assertEqual(remote.dump(), "{}")

    def test_assigned_key_sends_default_key(self):
        remote = RemoteBindings({})
        remote.add("down", F5)
        target = Recorder()
        self.assertTrue(remote.eventFilter(target, key(Qt.Key_F5)))
        self.assertTrue(remote.eventFilter(target, key(Qt.Key_F5, QEvent.KeyRelease)))
        self.assertEqual(target.keys, [Qt.Key_Down])
        self.assertFalse(remote.eventFilter(target, key(Qt.Key_F6)))

    def test_assigned_mouse_button_calls_handler_on_release(self):
        handler = Mock()
        remote = RemoteBindings({"home": handler})
        remote.add("home", FORWARD_MOUSE)
        self.assertTrue(remote.eventFilter(QWidget(), mouse(QEvent.MouseButtonPress, Qt.ForwardButton)))
        handler.assert_not_called()
        self.assertTrue(remote.eventFilter(QWidget(), mouse(QEvent.MouseButtonRelease, Qt.ForwardButton)))
        handler.assert_called_once_with()

    def test_text_fields_keep_their_keys(self):
        remote = RemoteBindings({})
        remote.add("up", F5)
        field = QLineEdit()
        field.show()
        field.activateWindow()
        field.setFocus()
        QApplication.processEvents()
        if QApplication.focusWidget() is not field:
            self.skipTest("focus indisponible sur cette plateforme")
        self.assertFalse(remote.eventFilter(field, key(Qt.Key_F5)))
        field.close()

    def test_paused_ignores_everything(self):
        remote = RemoteBindings({})
        remote.add("up", F5)
        remote.paused = True
        self.assertFalse(remote.eventFilter(Recorder(), key(Qt.Key_F5)))

    def test_capture_dialog(self):
        dialog = RemoteCaptureDialog("Retour")
        self.assertTrue(dialog.eventFilter(dialog, key(Qt.Key_Shift)))
        self.assertIsNone(dialog.binding)
        dialog.eventFilter(dialog, key(Qt.Key_F5))
        self.assertEqual(dialog.binding, F5)

        dialog = RemoteCaptureDialog("Retour")
        self.assertFalse(dialog.eventFilter(dialog, mouse(QEvent.MouseButtonPress, Qt.LeftButton)))
        self.assertTrue(dialog.eventFilter(dialog, mouse(QEvent.MouseButtonPress, Qt.ForwardButton)))
        self.assertIsNone(dialog.binding)
        dialog.eventFilter(dialog, mouse(QEvent.MouseButtonRelease, Qt.ForwardButton))
        self.assertEqual(dialog.binding, FORWARD_MOUSE)

    def test_describe(self):
        self.assertEqual(describe(FORWARD_MOUSE), "Bouton souris Suivant")
        self.assertEqual(describe("mouse:32"), "Bouton souris 6")
        self.assertEqual(describe(F5), "F5")
        self.assertIn("code 12", describe("native:12:0"))


if __name__ == "__main__":
    unittest.main()

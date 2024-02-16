from PyQt6.QtWidgets import QDialog, QApplication, QStyle
from .ui_compiled.ViewXMLWindow import Ui_ViewXMLWindow
from .XMLHighlighter import XMLHighlighter
from PyQt6.QtGui import QShowEvent
from typing import TYPE_CHECKING
from PyQt6.QtGui import QIcon


if TYPE_CHECKING:
    from .Environment import Environment
    from .MainWindow import MainWindow


class ViewXMLWindow(QDialog, Ui_ViewXMLWindow):
    def __init__(self, env: "Environment", main_window: "MainWindow") -> None:
        super().__init__(main_window)

        self.setupUi(self)

        self._main_window = main_window

        self._xml_highlighter = XMLHighlighter(self.preview_edit.document())

        self.close_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)))

        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(self.preview_edit.toPlainText()))
        self.close_button.clicked.connect(self.close)

    def showEvent(self, event: QShowEvent) -> None:
        self.preview_edit.setPlainText(self._main_window.get_xml_text())

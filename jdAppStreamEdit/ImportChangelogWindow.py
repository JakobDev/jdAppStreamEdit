from .ui_compiled.ImportChangelogWindow import Ui_ImportChangelogWindow
from PyQt6.QtWidgets import QDialog, QWidget, QMessageBox, QStyle
from typing import Optional, TYPE_CHECKING
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QIcon
from lxml import etree
import traceback
import sys


if TYPE_CHECKING:
    from .Environment import Environment


class ImportChangelogWindow(QDialog, Ui_ImportChangelogWindow):
    def __init__(self, env: "Environment", parent_window: Optional[QWidget]) -> None:
        super().__init__(parent_window)

        self.setupUi(self)

        self._env = env
        self._current_changelog: Optional[etree.Element] = None

        self.ok_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogOkButton)))
        self.cancel_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)))

        self.ok_button.clicked.connect(self._ok_button_clicked)
        self.cancel_button.clicked.connect(self.close)

    def _ok_button_clicked(self) -> None:
        changelog_importer = self._env.changelog_importer[self.changelog_type_box.currentIndex()]
        text = self.changelog_text_edit.toPlainText()

        try:
            changelog, error_message = changelog_importer.do_import(text)
        except Exception:
            print(traceback.format_exc(), end="", file=sys.stderr)

            msg_box = QMessageBox()
            msg_box.setWindowTitle(QCoreApplication.translate("ImportChangelogWindow", "Error"))
            msg_box.setText(QCoreApplication.translate("ImportChangelogWindow", "An Error happened during Import"))
            msg_box.setDetailedText(traceback.format_exc())
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.exec()

            return

        if error_message is not None:
            QMessageBox.critical(self, QCoreApplication.translate("ImportChangelogWindow", "Import failed"), error_message)
            return

        self._current_changelog = changelog
        self.close()

    def get_changelog(self) -> Optional[etree.Element]:
        self.changelog_text_edit.setPlainText("")
        self._current_changelog = None

        self.changelog_type_box.clear()
        for changelog_importer in self._env.changelog_importer:
            self.changelog_type_box.addItem(changelog_importer.get_name())

        self.exec()

        return self._current_changelog

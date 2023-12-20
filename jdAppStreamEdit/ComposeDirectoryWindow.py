from .ui_compiled.ComposeDirectoryWindow import Ui_ComposeDirectoryWindow
from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox
from .Functions import is_flatpak, check_appstreamcli
from PyQt6.QtCore import QCoreApplication
from typing import TYPE_CHECKING
import subprocess
import os


if TYPE_CHECKING:
    from .MainWindow import MainWindow


class ComposeDirectoryWindow(QDialog, Ui_ComposeDirectoryWindow):
    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__(main_window)

        self.setupUi(self)

        self._main_window = main_window

        if is_flatpak():
            self.path_edit.setEnabled(False)

        self.browse_button.clicked.connect(self._browse_button_clicked)
        self.button_box.accepted.connect(self._ok_button_clicked)
        self.button_box.rejected.connect(self.close)

    def _browse_button_clicked(self) -> None:
        if self.path_edit.text().strip() == "":
            start_dir = os.path.expanduser("~")
        else:
            start_dir = self.path_edit.text().strip()

        path = QFileDialog.getExistingDirectory(self, directory=start_dir)

        if path == "":
            return

        self.path_edit.setText(path)

    def _ok_button_clicked(self) -> None:
        path = os.path.abspath(self.path_edit.text().strip())

        if path == "":
            QMessageBox.critical(self, QCoreApplication.translate("ComposeDirectoryWindow", "No path"), QCoreApplication.translate("ComposeDirectoryWindow", "You need to specify a path"))
            return

        if not os.path.isdir(path):
            QMessageBox.critical(self, QCoreApplication.translate("ComposeDirectoryWindow", "Not a directory"), QCoreApplication.translate("ComposeDirectoryWindow", "{{path}} is not a directory").replace("{{path}}", path))
            return

        result = subprocess.run(["appstreamcli", "compose", "--prefix", "/", "--result-root", path, "--origin", "jdAppStreamEdit", path], capture_output=True)

        if result.returncode == 0:
            QMessageBox.information(self, QCoreApplication.translate("ComposeDirectoryWindow", "Success"), QCoreApplication.translate("ComposeDirectoryWindow", "The data were successfully composed"))
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(QCoreApplication.translate("ComposeDirectoryWindow", "Error"))
            msg_box.setText(QCoreApplication.translate("ComposeDirectoryWindow", "Failed to compose the data"))
            msg_box.setDetailedText(result.stdout.decode("utf-8"))
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.exec()

        self.close()

    def open_window(self) -> None:
        if not check_appstreamcli(self._main_window):
            return

        self.path_edit.setText("")
        self.open()

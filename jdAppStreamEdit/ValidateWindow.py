from .ui_compiled.ValidateWindow import Ui_ValidateWindow
from PyQt6.QtWidgets import QDialog, QMessageBox, QStyle
from PyQt6.QtCore import QCoreApplication
from typing import TYPE_CHECKING
from PyQt6.QtGui import QIcon
import subprocess
import tempfile
import os


if TYPE_CHECKING:
    from .Environment import Environment
    from .MainWindow import MainWindow


class ValidateWindow(QDialog, Ui_ValidateWindow):
    def __init__(self, env: "Environment", main_window: "MainWindow") -> None:
        super().__init__(main_window)

        self.setupUi(self)

        self._env = env
        self._main_window = main_window

        self.ok_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogOkButton)))

        self.mode_box.currentIndexChanged.connect(self._execute_command)
        self.ok_button.clicked.connect(self.close)

    def _execute_command(self) -> None:
        temp_path = os.path.join(tempfile.gettempdir(), self._main_window.get_id() + ".metainfo.xml")
        self._main_window.save_file(temp_path)
        if self.mode_box.currentIndex() == 0:
            try:
                result = subprocess.run(["appstreamcli", "validate", "--explain", temp_path], capture_output=True, text=True)
            except FileNotFoundError:
                self.output_field.setPlainText(QCoreApplication.translate("ValidateWindow", "appstreamcli was not found"))
                os.remove(temp_path)
                return
        else:
            if self.mode_box.currentIndex() == 1:
                mode = "validate"
            elif self.mode_box.currentIndex() == 2:
                mode = "validate-relax"
            elif self.mode_box.currentIndex() == 3:
                mode = "validate-strict"
            try:
                result = subprocess.run(["appstream-util", mode, temp_path], capture_output=True, text=True)
            except FileNotFoundError:
                self.output_field.setPlainText(QCoreApplication.translate("ValidateWindow", "appstream-util was not found"))
                os.remove(temp_path)
                return
        self.output_field.setPlainText(result.stdout)
        os.remove(temp_path)

    def open_window(self) -> None:
        if self._main_window.get_id() == "":
            QMessageBox.critical(self.parent(), QCoreApplication.translate("ValidateWindow", "No ID"), QCoreApplication.translate("ValidateWindow", "You need to set a ID to use this feature"))
            return

        self.mode_box.setCurrentIndex(0)
        self._execute_command()
        self.open()

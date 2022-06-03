from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtCore import QCoreApplication
from PyQt6 import uic
import subprocess
import tempfile
import os


class ValidateWindow(QDialog):
    def __init__(self, env, main_window):
        super().__init__()
        uic.loadUi(os.path.join(env.program_dir, "ValidateWindow.ui"), self)

        self._env = env
        self._main_window = main_window

        self.mode_box.currentIndexChanged.connect(self._execute_command)
        self.ok_button.clicked.connect(self.close)


    def _execute_command(self):
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


    def open_window(self):
        if self._main_window.get_id() == "":
            QMessageBox.critical(self, QCoreApplication.translate("ValidateWindow", "No ID"), QCoreApplication.translate("ValidateWindow", "You need to set a ID to use this feature"))
            return

        self.mode_box.setCurrentIndex(0)
        self._execute_command()
        self.exec()

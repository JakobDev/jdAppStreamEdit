from PyQt6.QtWidgets import QDialog, QStyle, QApplication
from .ui_compiled.SysinfoWindow import Ui_SysinfoWindow
from .Functions import check_appstreamcli
from typing import TYPE_CHECKING
from PyQt6.QtGui import QIcon
import subprocess


if TYPE_CHECKING:
    from .Environment import Environment
    from .MainWindow import MainWindow


class SysinfoWindow(QDialog, Ui_SysinfoWindow):
    def __init__(self, env: "Environment", main_window: "MainWindow") -> None:
        super().__init__(main_window)

        self.setupUi(self)

        self._main_window = main_window

        self.close_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)))

        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(self.sysinfo_edit.toPlainText()))
        self.close_button.clicked.connect(self.close)

    def open_window(self) -> None:
        if not check_appstreamcli(self._main_window):
            return

        result = subprocess.run(["appstreamcli", "sysinfo"], capture_output=True)
        self.sysinfo_edit.setPlainText(result.stdout.decode("utf-8"))

        self.open()

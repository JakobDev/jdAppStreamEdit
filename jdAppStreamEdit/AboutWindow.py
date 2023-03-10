from .ui_compiled.AboutWindow import Ui_AboutWindow
from PyQt6.QtWidgets import QDialog
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .Environment import Environment


class AboutWindow(QDialog, Ui_AboutWindow):
    def __init__(self, env: "Environment"):
        super().__init__()

        self.setupUi(self)

        self.icon_label.setPixmap(env.icon.pixmap(64, 64))
        self.version_label.setText(self.version_label.text().replace("{{version}}", env.version))

        self.close_button.clicked.connect(self.close)

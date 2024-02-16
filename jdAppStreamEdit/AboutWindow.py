from .ui_compiled.AboutWindow import Ui_AboutWindow
from PyQt6.QtWidgets import QDialog, QStyle
from .Languages import get_language_names
from typing import TYPE_CHECKING
from PyQt6.QtGui import QIcon
import json
import os


if TYPE_CHECKING:
    from .Environment import Environment
    from .MainWindow import MainWindow


class AboutWindow(QDialog, Ui_AboutWindow):
    def __init__(self, env: "Environment", main_window: "MainWindow") -> None:
        super().__init__(main_window)

        self.setupUi(self)

        self.icon_label.setPixmap(env.icon.pixmap(64, 64))
        self.version_label.setText(self.version_label.text().replace("{{version}}", env.version))

        with open(os.path.join(env.program_dir, "data", "translators.json"), "r", encoding="utf-8") as f:
            translators_dict: dict[str, list[str]] = json.load(f)

        translators_text = ""
        language_names = get_language_names()
        for language, translators in translators_dict.items():
            translators_text += f"<b>{language_names.get(language, language)}</b><br>\n"
            for translator_name in translators:
                translators_text += f"{translator_name}<br>\n"
            translators_text += "<br>\n"
        translators_text = translators_text.removesuffix("<br>\n")
        self.translators_edit.setHtml(translators_text)

        with open(os.path.join(env.program_dir, "data", "changelog.html"), "r", encoding="utf-8") as f:
            self.changelog_edit.setHtml(f.read())

        self.tab_widget.tabBar().setDocumentMode(True)
        self.tab_widget.tabBar().setExpanding(True)

        self.tab_widget.setCurrentIndex(0)

        self.close_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)))

        self.close_button.clicked.connect(self.close)

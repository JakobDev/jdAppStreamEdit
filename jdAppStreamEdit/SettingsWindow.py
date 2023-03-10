from .ui_compiled.SettingsWindow import Ui_SettingsWindow
from PyQt6.QtCore import QCoreApplication, QLocale
from .Functions import select_combo_box_data
from PyQt6.QtWidgets import QDialog
from typing import TYPE_CHECKING
import os


if TYPE_CHECKING:
    from .Environment import Environment
    from .MainWindow import MainWindow


def get_language_names() -> dict[str, str]:
    return {
        "en": QCoreApplication.translate("Language", "Englisch"),
        "de": QCoreApplication.translate("Language", "German"),
        "nl": QCoreApplication.translate("Language", "Dutch"),
    }


class SettingsWindow(QDialog, Ui_SettingsWindow):
    def __init__(self, env: "Environment", main_window: "MainWindow"):
        super().__init__()

        self.setupUi(self)

        self._env = env
        self._main_window = main_window

        self.language_box.addItem(QCoreApplication.translate("SettingsWindow", "System language"), "default")
        lannguage_names = get_language_names()
        translations_found = False
        if os.path.isdir(os.path.join(env.program_dir, "translations")):
            for i in os.listdir(os.path.join(env.program_dir, "translations")):
                if i.endswith(".qm"):
                    lang = i.removeprefix("jdAppStreamEdit_").removesuffix(".qm")
                    self.language_box.addItem(lannguage_names.get(lang, lang), lang)
                    translations_found = True

        if not translations_found:
            print("No translations where found. make sure you run the BuildTranslations script")

        self.window_title_box.addItem(QCoreApplication.translate("SettingsWindow", "Nothing"), "none")
        self.window_title_box.addItem(QCoreApplication.translate("SettingsWindow", "Filename"), "filename")
        self.window_title_box.addItem(QCoreApplication.translate("SettingsWindow", "Path"), "path")

        self.use_tabs_check_box.stateChanged.connect(self._update_whitespace_section_enabled)
        self.reset_button.clicked.connect(self._reset_button_clicked)
        self.ok_button.clicked.connect(self._ok_button_clicked)
        self.cancel_button.clicked.connect(self.close)

    def _update_widgets(self):
        index = self.language_box.findData(self._env.settings.get("language"))
        if index == -1:
            self.language_box.setCurrentIndex(0)
        else:
            self.language_box.setCurrentIndex(index)

        self.recent_files_spin_box.setValue(self._env.settings.get("recentFilesLength"))
        select_combo_box_data(self.window_title_box, self._env.settings.get("windowTitleType"))
        self.check_save_check_box.setChecked(self._env.settings.get("checkSaveBeforeClosing"))
        self.title_edited_check_box.setChecked(self._env.settings.get("showEditedTitle"))
        self.use_editorconfig_check_box.setChecked(self._env.settings.get("useEditorconfig"))
        self.whitespace_spin_box.setValue(self._env.settings.get("whitespaceCount"))
        self.use_tabs_check_box.setChecked(self._env.settings.get("useTabsInsteadOfSpaces"))
        self.add_comment_check_box.setChecked(self._env.settings.get("addCommentSave"))

    def _update_whitespace_section_enabled(self) -> None:
        enabled = not self.use_tabs_check_box.isChecked()
        self.whitespace_label.setEnabled(enabled)
        self.whitespace_spin_box.setEnabled(enabled)

    def _reset_button_clicked(self):
        self._env.settings.reset()
        self._update_widgets()

    def _ok_button_clicked(self):
        self._env.settings.set("language", self.language_box.currentData())
        self._env.settings.set("recentFilesLength",  self.recent_files_spin_box.value())
        self._env.settings.set("windowTitleType",  self.window_title_box.currentData())
        self._env.settings.set("checkSaveBeforeClosing", self.check_save_check_box.isChecked())
        self._env.settings.set("showEditedTitle", self.title_edited_check_box.isChecked())
        self._env.settings.set("useEditorconfig", self.use_editorconfig_check_box.isChecked())
        self._env.settings.set("whitespaceCount", self.whitespace_spin_box.value())
        self._env.settings.set("useTabsInsteadOfSpaces", self.use_tabs_check_box.isChecked())
        self._env.settings.set("addCommentSave", self.add_comment_check_box.isChecked())

        self._env.recent_files = self._env.recent_files[:self._env.settings.get("recentFilesLength")]
        self._env.save_recent_files()

        self._main_window.update_window_title()

        self._env.settings.save(os.path.join(self._env.data_dir, "settings.json"))
        self.close()

    def open_window(self):
        self._update_widgets()
        self.exec()

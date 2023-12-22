from .Functions import clear_table_widget, select_combo_box_data, get_logical_table_row_list, stretch_table_widget_colums_size
from PyQt6.QtWidgets import QDialog, QComboBox, QPushButton, QTableWidgetItem, QMessageBox, QStyle
from .ui_compiled.TranslateWindow import Ui_TranslateWindow
from .Constants import TRANSLATE_LANGUAGE_SORT_SETTING
from typing import Dict, Optional, TYPE_CHECKING
from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtGui import QIcon


if TYPE_CHECKING:
    from .Environment import Environment


class TranslateWindow(QDialog, Ui_TranslateWindow):
    def __init__(self, env: "Environment") -> None:
        super().__init__()
        self._env = env

        self.setupUi(self)

        stretch_table_widget_colums_size(self.table_widget)

        self.table_widget.verticalHeader().setSectionsMovable(True)

        self.ok_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogOkButton)))
        self.cancel_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)))

        self.add_button.clicked.connect(self._add_row)
        self.ok_button.clicked.connect(self._ok_button_clicked)
        self.cancel_button.clicked.connect(self.close)

    def _add_row(self, lang_code_of_paragraph: Optional[str] = None, translated_paragraph: Optional[str] = None) -> None:
        row = self.table_widget.rowCount()
        self.table_widget.insertRow(row)

        language_box = QComboBox()
        language_box.setPlaceholderText(QCoreApplication.translate("TranslateWindow", "Select Language"))

        for lang_code, lang_name in self._env.language_codes.items():
            if self._env.settings.get("translateLanguageSort") == TRANSLATE_LANGUAGE_SORT_SETTING.NAME:
                entry = f"{lang_name} ({lang_code})"
            else:
                entry = f"{lang_code}: {lang_name}"

            language_box.addItem(entry, lang_code)

        language_box.model().sort(0, Qt.SortOrder.AscendingOrder)

        select_combo_box_data(language_box, lang_code_of_paragraph, default_index=-1)

        self.table_widget.setCellWidget(row, 0, language_box)

        if translated_paragraph is None:
            self.table_widget.setItem(row, 1, QTableWidgetItem())
        else:
            self.table_widget.setItem(row, 1, QTableWidgetItem(translated_paragraph))

        remove_button = QPushButton(QCoreApplication.translate("TranslateWindow", "Remove"))
        remove_button.clicked.connect(self._remove_button_clicked)
        self.table_widget.setCellWidget(row, 2, remove_button)

    def _remove_button_clicked(self) -> None:
        for i in range(self.table_widget.rowCount()):
            if self.table_widget.cellWidget(i, 2) == self.sender():
                self.table_widget.removeRow(i)
                return

    def _check_valid(self) -> bool:
        known_languages = []
        for i in range(self.table_widget.rowCount()):
            if self.table_widget.cellWidget(i, 0).currentIndex() == -1:
                QMessageBox.critical(self, QCoreApplication.translate("TranslateWindow", "No Language selected"), QCoreApplication.translate("TranslateWindow", "You had no Language selected for at least one Item"))
                return False

            name = self.table_widget.cellWidget(i, 0).currentText()
            language = self.table_widget.cellWidget(i, 0).currentData()
            if language in known_languages:
                QMessageBox.critical(self, QCoreApplication.translate("TranslateWindow", "Language double"), QCoreApplication.translate("TranslateWindow", "{name} appears twice or more times in the table").format(name=name))
                return False
            known_languages.append(language)
            if self.table_widget.item(i, 1).text() == "":
                QMessageBox.critical(self, QCoreApplication.translate("TranslateWindow", "No Text"), QCoreApplication.translate("TranslateWindow", "The Translation for {name} has no Text").format(name=name))
                return False
        return True

    def _ok_button_clicked(self) -> None:
        if not self._check_valid():
            return

        self._current_dict.clear()
        for i in get_logical_table_row_list(self.table_widget):
            language = self.table_widget.cellWidget(i, 0).currentData()
            text = self.table_widget.item(i, 1).text()
            self._current_dict[language] = text.strip()

        if self._main_window:
            self._main_window.set_file_edited()

        self._saved = True

        self.close()

    def open_window(self, translations_of_paragraph: Dict[str, str], main_window=None) -> bool:
        self._current_dict = translations_of_paragraph
        self._saved = False

        if main_window:
            self._main_window = main_window
        else:
            self._main_window = None

        clear_table_widget(self.table_widget)

        if self._env.settings.get("translateLanguageSort") == TRANSLATE_LANGUAGE_SORT_SETTING.NAME:
            key = lambda key: self._env.language_codes[key]  # noqa: E731
        else:
            key = lambda key: key  # noqa: E731

        for lang_code_of_paragraph in sorted(translations_of_paragraph.keys(), key=key):
            translated_paragraph = translations_of_paragraph[lang_code_of_paragraph]
            self._add_row(lang_code_of_paragraph=lang_code_of_paragraph, translated_paragraph=translated_paragraph)

        self.exec()

        return self._saved

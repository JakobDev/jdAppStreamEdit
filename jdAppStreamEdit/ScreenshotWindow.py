from .Functions import is_url_valid, set_layout_enabled, list_widget_contains_item
from PyQt6.QtWidgets import QDialog, QMessageBox, QInputDialog, QListWidgetItem
from .ui_compiled.ScreenshotWindow import Ui_ScreenshotWindow
from .Types import ScreenshotDict, ScreenshotDictImage
from .ThumbnailWindow import ThumbnailWindow
from typing import Optional, TYPE_CHECKING
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QPixmap
import requests
import copy


if TYPE_CHECKING:
    from .Environment import Environment
    from .MainWindow import MainWindow


class ScreenshotWindow(QDialog, Ui_ScreenshotWindow):
    def __init__(self, env: "Environment", main_window: "MainWindow"):
        super().__init__(main_window)

        self.setupUi(self)

        self._env = env
        self._main_window = main_window
        self._thumbnail_window = ThumbnailWindow(env)
        self._caption_translations: dict[str, str] = {}
        self._source_image_translations: dict[str, ScreenshotDictImage] = {}

        self.tab_widget.tabBar().setDocumentMode(True)
        self.tab_widget.tabBar().setExpanding(True)

        self.source_width_height_check_box.stateChanged.connect(lambda: self.source_width_height_group_box.setEnabled(self.source_width_height_check_box.isChecked()))
        self.translate_caption_button.clicked.connect(lambda: env.translate_window.open_window(self._caption_translations))

        self.source_image_language_list.currentItemChanged.connect(self._source_image_language_list_item_changed)
        self.source_image_language_add_button.clicked.connect(self._source_image_language_add_button_clicked)
        self.source_image_language_remove_button.clicked.connect(self._source_image_language_remove_button_clicked)
        self.source_translation_width_height_check_box.stateChanged.connect(lambda: self.source_translation_width_height_group_box.setEnabled(self.source_translation_width_height_check_box.isChecked()))

        self.add_thumbnail_button.clicked.connect(self._add_thumbnail_button_clicked)

        self.preview_button.clicked.connect(self._preview_button_clicked)
        self.ok_button.clicked.connect(self._ok_button_clicked)
        self.cancel_button.clicked.connect(self.close)

    def _check_url(self) -> bool:
        url = self.source_url_edit.text()
        if len(url) == 0:
            QMessageBox.critical(self, QCoreApplication.translate("ScreenshotWindow", "No URL"), QCoreApplication.translate("ScreenshotWindow", "Please enter a URL"))
            return False
        if not is_url_valid(self.source_url_edit.text()):
            QMessageBox.critical(self, QCoreApplication.translate("ScreenshotWindow", "Invalid URL"), QCoreApplication.translate("ScreenshotWindow", "Please enter a valid URL"))
            return False
        return True

    def _preview_button_clicked(self):
        if not self._check_url():
            return

        try:
            r = requests.get(self.source_url_edit.text(), stream=True)
        except Exception:
            QMessageBox.critical(self, QCoreApplication.translate("ScreenshotWindow", "Can't get Image"), QCoreApplication.translate("ScreenshotWindow", "It looks like the given URL does not work"))
            return

        pixmap = QPixmap()
        if pixmap.loadFromData(r.raw.read()):
            self.source_image_label.setPixmap(pixmap.scaled(256, 256))
        else:
            QMessageBox.critical(self, QCoreApplication.translate("ScreenshotWindow", "Can't decode Image"), QCoreApplication.translate("ScreenshotWindow", "The given Image can't be decoded"))

    def _update_source_image_language_list_buttons_enabled(self) -> None:
        enabled = self.source_image_language_list.currentRow() != -1
        self.source_image_language_remove_button.setEnabled(enabled)

    def _get_translated_source_image(self, lang: str) -> ScreenshotDictImage:
        image: ScreenshotDictImage = {}
        image["type"] = "source"
        image["language"] = lang
        image["url"] = self.source_translation_url_edit.text().strip()

        if self.source_translation_width_height_check_box.isChecked():
            image["width"] = self.source_translation_width_spin_box.value()
            image["height"] = self.source_translation_height_spin_box.value()
        else:
            image["width"] = None
            image["height"] = None

        return image

    def _update_source_image_translation_widgets(self) -> None:
        if self.source_image_language_list.currentItem() is None:
            set_layout_enabled(self.source_image_translation_widgets_layout, False)
            self.source_translation_url_edit.setText("")
            self.source_translation_width_height_check_box.setChecked(False)
            self.source_translation_width_spin_box.setValue(0)
            self.source_translation_height_spin_box.setValue(0)
            return

        set_layout_enabled(self.source_image_translation_widgets_layout, True)

        image: ScreenshotDictImage = self._source_image_translations[self.source_image_language_list.currentItem().text()]

        self.source_translation_url_edit.setText(image["url"])
        self.source_translation_width_height_check_box.setChecked(image["width"] is not None and image["height"] is not None)
        self.source_translation_width_height_group_box.setEnabled(image["width"] is not None and image["height"] is not None)
        self.source_translation_width_spin_box.setValue(image["width"] or 0)
        self.source_translation_height_spin_box.setValue(image["height"] or 0)

    def _source_image_language_list_item_changed(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        if previous is not None:
            previous_lang = previous.text()
            self._source_image_translations[previous_lang] = self._get_translated_source_image(previous_lang)

        self._update_source_image_translation_widgets()
        self._update_source_image_language_list_buttons_enabled()

    def _source_image_language_add_button_clicked(self) -> None:
        lang = QInputDialog.getItem(self, QCoreApplication.translate("ScreenshotWindow", "Add Language"), QCoreApplication.translate("ScreenshotWindow", "Please enter a Language Code"), self._env.language_codes)[0].strip()

        if lang == "":
            return

        if list_widget_contains_item(self.source_image_language_list, lang):
            QMessageBox.critical(self, QCoreApplication.translate("ScreenshotWindow", "Language exists"), QCoreApplication.translate("ScreenshotWindow", "There is already a translated Image for {{language}}").replace("{{language}}", lang))
            return

        self._source_image_translations[lang] = {
            "url": "",
            "type": "source",
            "language": lang,
            "width": None,
            "height": None
        }

        item = QListWidgetItem(lang)
        self.source_image_language_list.addItem(item)
        self.source_image_language_list.setCurrentItem(item)
        self._update_source_image_language_list_buttons_enabled()

    def _source_image_language_remove_button_clicked(self) -> None:
        del self._source_image_translations[self.source_image_language_list.currentItem().text()]
        self.source_image_language_list.takeItem(self.source_image_language_list.currentRow())
        self._update_source_image_language_list_buttons_enabled()

    def _add_thumbnail_button_clicked(self) -> None:
        untranslated_image, image_list = self._thumbnail_window.open_window(None)

        if untranslated_image is None:
            return

        item = QListWidgetItem(untranslated_image["url"])
        untranslated_image["url"]
        item.setData(42, (untranslated_image, image_list))
        self.thumbnail_list.addItem(item)
        self.thumbnail_list.setCurrentItem(item)

    def _get_untranslated_source_image(self) -> ScreenshotDictImage:
        source_image: ScreenshotDictImage = {}
        source_image["type"] = "source"
        source_image["language"] = None
        source_image["url"] = self.source_url_edit.text().strip()

        if self.source_width_height_check_box.isChecked():
            source_image["width"] = self.source_width_spin_box.value()
            source_image["height"] = self.source_height_spin_box.value()
        else:
            source_image["width"] = None
            source_image["height"] = None

        return source_image

    def _ok_button_clicked(self):
        if self.source_image_language_list.currentItem() is not None:
            lang = self.source_image_language_list.currentItem().text()
            self._source_image_translations[lang] = self._get_translated_source_image(lang)

        new_dict: ScreenshotDict = {
            "source_url": self.source_url_edit.text().strip(),
            "images": [self._get_untranslated_source_image()] + [self._source_image_translations[self.source_image_language_list.item(i).text()] for i in range(self.source_image_language_list.count())]
        }

        for i in range(self.thumbnail_list.count()):
            item = self.thumbnail_list.item(i)
            new_dict["images"].append(item.data(42)[0])
            new_dict["images"] += item.data(42)[1]

        if len(self._main_window.screenshot_list) == 0:
            new_dict["default"] = True
        else:
            if self._position is not None:
                new_dict["default"] =  self._main_window.screenshot_list[self._position]["default"]
            else:
                new_dict["default"] = False

        if self.caption_edit.text().strip() != "":
            new_dict["caption"] = self.caption_edit.text().strip()
            new_dict["caption_translations"] = copy.copy(self._caption_translations)
        else:
            new_dict["caption"] = None
            new_dict["caption_translations"] = None

        if self._position is None:
            self._main_window.screenshot_list.append(new_dict)
        elif self._position is None:
            new_dict["default"] = False
        else:
            self._main_window.screenshot_list[self._position] = new_dict

        self._main_window.update_screenshot_table()
        self._main_window.set_file_edited()
        self.close()

    def _load_untranslated_source_image(self, source_image: ScreenshotDictImage) -> None:
        self.source_url_edit.setText(source_image["url"])
        self.source_width_height_check_box.setChecked(source_image["width"] is not None and source_image["height"] is not None)
        self.source_width_height_group_box.setEnabled(source_image["width"] is not None and source_image["height"] is not None)
        self.source_width_spin_box.setValue(source_image["width"] or 0)
        self.source_height_spin_box.setValue(source_image["height"] or 0)

    def open_window(self, position: Optional[int]) -> None:
        self._position = position

        self.source_image_language_list.clear()

        if position is None:
            self.source_url_edit.setText("")
            self.source_width_height_check_box.setChecked(False)
            self.source_width_height_group_box.setEnabled(False)
            self.source_width_spin_box.setValue(0)
            self.source_height_spin_box.setValue(0)
            self.caption_edit.setText("")
            self._caption_translations = {}
            self.setWindowTitle(QCoreApplication.translate("ScreenshotWindow", "Add Screenshot"))
        else:
            current_entry: ScreenshotDict = self._main_window.screenshot_list[position]

            for image in current_entry["images"]:
                if image["type"] == "source" and image["language"] is None:
                    self._load_untranslated_source_image(image)
                elif image["type"] == "source" and image["language"] is not None:
                    self.source_image_language_list.addItem(image["language"])
                    self._source_image_translations[image["language"]] = image

            self.caption_edit.setText(current_entry["caption"] or "")
            self._caption_translations = copy.deepcopy(current_entry["caption_translations"]) or {}

            self.setWindowTitle(QCoreApplication.translate("ScreenshotWindow", "Edit Screenshot"))

        self.source_image_label.clear()
        self.source_image_label.setText(QCoreApplication.translate("ScreenshotWindow", "If you click Preview, your Screenshot will appear here scaled by 256x256"))

        self._update_source_image_language_list_buttons_enabled()
        self._update_source_image_translation_widgets()
        self.tab_widget.setCurrentIndex(0)

        self.open()

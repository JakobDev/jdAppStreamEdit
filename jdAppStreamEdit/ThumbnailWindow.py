from PyQt6.QtWidgets import QDialog, QMessageBox, QInputDialog, QListWidgetItem, QStyle
from .Functions import set_layout_enabled, list_widget_contains_item
from .ui_compiled.ThumbnailWindow import Ui_ThumbnailWindow
from typing import Optional, TYPE_CHECKING
from PyQt6.QtCore import QCoreApplication
from .Types import ScreenshotDictImage
from PyQt6.QtGui import QIcon
import copy


if TYPE_CHECKING:
    from .ScreenshotWindow import ScreenshotWindow
    from .Environment import Environment


class ThumbnailWindow(QDialog, Ui_ThumbnailWindow):
    def __init__(self, env: "Environment", screenshot_window: "ScreenshotWindow") -> None:
        super().__init__(screenshot_window)

        self.setupUi(self)

        self._env = env
        self._translated_images: list[ScreenshotDictImage] = []
        self._untranslated_image: Optional[ScreenshotDictImage] = None
        self._thumbnail_image_translations: dict[str, ScreenshotDictImage] = {}

        self.tab_widget.tabBar().setDocumentMode(True)
        self.tab_widget.tabBar().setExpanding(True)

        self.ok_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogOkButton)))
        self.cancel_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)))

        self.thumbnail_scale_factor_check_box.stateChanged.connect(self._update_thumbnail_scale_factor_enabled)
        self.thumbnail_translation_scale_factor_check_box.stateChanged.connect(self._update_thumbnail_translation_scale_factor_enabled)

        self.thumbnail_image_language_list.currentItemChanged.connect(self._thumbnail_image_language_list_item_changed)
        self.thumbnail_image_language_add_button.clicked.connect(self._thumbnail_image_language_add_button_clicked)
        self.thumbnail_image_language_remove_button.clicked.connect(self._thumbnail_image_language_remove_button_clicked)

        self.ok_button.clicked.connect(self._ok_button_clicked)
        self.cancel_button.clicked.connect(self.close)

    def _update_thumbnail_scale_factor_enabled(self) -> None:
        enabled = self.thumbnail_scale_factor_check_box.isChecked()
        self.thumbnail_scale_factor_label.setEnabled(enabled)
        self.thumbnail_scale_factor_spin_box.setEnabled(enabled)

    def _update_thumbnail_translation_scale_factor_enabled(self) -> None:
        enabled = self.thumbnail_translation_scale_factor_check_box.isChecked()
        self.thumbnail_translation_scale_factor_label.setEnabled(enabled)
        self.thumbnail_translation_scale_factor_spin_box.setEnabled(enabled)

    def _update_thumbnail_image_language_list_buttons_enabled(self) -> None:
        enabled = self.thumbnail_image_language_list.currentRow() != -1
        self.thumbnail_image_language_remove_button.setEnabled(enabled)

    def _get_translated_thumbnail_image(self, lang: str) -> ScreenshotDictImage:
        image: ScreenshotDictImage = {
            "type": "thumbnail",
            "language": lang,
            "url": self.thumbnail_translation_url_edit.text().strip(),
            "width": self.thumbnail_translation_width_spin_box.value(),
            "height": self.thumbnail_translation_height_spin_box.value()
        }

        if self.thumbnail_translation_scale_factor_check_box.isChecked():
            image["scale_factor"] = self.thumbnail_translation_scale_factor_spin_box.value()
        else:
            image["scale_factor"] = None

        return image

    def _update_thumbnail_image_translation_widgets(self) -> None:
        if self.thumbnail_image_language_list.currentItem() is None:
            set_layout_enabled(self.thumbnail_image_translation_widgets_layout, False)
            self.thumbnail_translation_url_edit.setText("")
            self.thumbnail_translation_width_spin_box.setValue(0)
            self.thumbnail_translation_height_spin_box.setValue(0)
            self.thumbnail_translation_scale_factor_check_box.setChecked(False)
            self.thumbnail_translation_scale_factor_spin_box.setValue(1)
            return

        set_layout_enabled(self.thumbnail_image_translation_widgets_layout, True)

        image: ScreenshotDictImage = self._thumbnail_image_translations[self.thumbnail_image_language_list.currentItem().text()]

        self.thumbnail_translation_url_edit.setText(image["url"])
        self.thumbnail_translation_width_spin_box.setValue(image["width"] or 0)
        self.thumbnail_translation_height_spin_box.setValue(image["height"] or 0)
        self.thumbnail_translation_scale_factor_check_box.setChecked(image["scale_factor"] is not None)
        self.thumbnail_translation_scale_factor_spin_box.setValue(image["scale_factor"] if image["scale_factor"] is not None else 1)
        self._update_thumbnail_translation_scale_factor_enabled()

    def _thumbnail_image_language_list_item_changed(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        if previous is not None:
            previous_lang = previous.text()
            self._thumbnail_image_translations[previous_lang] = self._get_translated_thumbnail_image(previous_lang)

        self._update_thumbnail_image_translation_widgets()
        self._update_thumbnail_image_language_list_buttons_enabled()

    def _thumbnail_image_language_add_button_clicked(self) -> None:
        lang, ok = QInputDialog.getItem(self, QCoreApplication.translate("ScreenshotWindow", "Add Language"), QCoreApplication.translate("ScreenshotWindow", "Please enter a Language Code"), self._env.language_codes.keys())
        lang = lang.strip()

        if not ok or lang == "":
            return

        if list_widget_contains_item(self.thumbnail_image_language_list, lang):
            QMessageBox.critical(self, QCoreApplication.translate("ScreenshotWindow", "Language exists"), QCoreApplication.translate("ScreenshotWindow", "There is already a translated Image for {{language}}").replace("{{language}}", lang))
            return

        self._thumbnail_image_translations[lang] = {
            "url": "",
            "type": "source",
            "language": lang,
            "width": None,
            "height": None,
            "scale_factor": None
        }

        item = QListWidgetItem(lang)
        self.thumbnail_image_language_list.addItem(item)
        self.thumbnail_image_language_list.setCurrentItem(item)
        self._update_thumbnail_image_language_list_buttons_enabled()

    def _thumbnail_image_language_remove_button_clicked(self) -> None:
        del self._thumbnail_image_translations[self.thumbnail_image_language_list.currentItem().text()]
        self.thumbnail_image_language_list.takeItem(self.thumbnail_image_language_list.currentRow())
        self._update_thumbnail_image_language_list_buttons_enabled()

    def _ok_button_clicked(self) -> None:
        if self.thumbnail_image_language_list.currentItem() is not None:
            lang = self.thumbnail_image_language_list.currentItem().text()
            self._thumbnail_image_translations[lang] = self._get_translated_thumbnail_image(lang)

        self._untranslated_image: ScreenshotDictImage = {
            "language": None,
            "type": "thumbnail",
            "url": self.thumbnail_url_edit.text(),
            "width": self.thumbnail_width_spin_box.value(),
            "height": self.thumbnail_height_spin_box.value()
        }

        if self.thumbnail_scale_factor_check_box.isChecked():
            self._untranslated_image["scale_factor"] = self.thumbnail_scale_factor_spin_box.value()
        else:
            self._untranslated_image["scale_factor"] = None

        for i in range(self.thumbnail_image_language_list.count()):
            self._translated_images.append(self._thumbnail_image_translations[self.thumbnail_image_language_list.item(i).text()])

        self.close()

    def open_window(self, untranslated_image: Optional[ScreenshotDictImage], translated_images: list[ScreenshotDictImage]) -> tuple[Optional[ScreenshotDictImage], list[ScreenshotDictImage]]:
        if untranslated_image is None:
            self.thumbnail_url_edit.setText("")
            self.thumbnail_width_spin_box.setValue(0)
            self.thumbnail_height_spin_box.setValue(0)
            self.thumbnail_scale_factor_check_box.setChecked(False)
            self.thumbnail_scale_factor_spin_box.setValue(1)
        else:
            self.thumbnail_url_edit.setText(untranslated_image["url"])
            self.thumbnail_width_spin_box.setValue(untranslated_image["width"])
            self.thumbnail_height_spin_box.setValue(untranslated_image["height"])
            self.thumbnail_scale_factor_check_box.setChecked(untranslated_image["scale_factor"] is not None)
            self.thumbnail_scale_factor_spin_box.setValue(untranslated_image["scale_factor"] if untranslated_image["scale_factor"] is not None else 1)

        self._untranslated_image = copy.deepcopy(untranslated_image)
        self._translated_images = copy.deepcopy(translated_images)

        self._thumbnail_image_translations.clear()
        self.thumbnail_image_language_list.clear()
        for image in translated_images:
            self.thumbnail_image_language_list.addItem(image["language"])
            self._thumbnail_image_translations[image["language"]] = image

        self._update_thumbnail_image_language_list_buttons_enabled()
        self._update_thumbnail_image_translation_widgets()
        self._update_thumbnail_scale_factor_enabled()
        self.tab_widget.setCurrentIndex(0)

        self.exec()

        return copy.deepcopy(self._untranslated_image), copy.deepcopy(self._translated_images)

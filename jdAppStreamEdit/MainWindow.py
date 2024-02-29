from .Functions import clear_table_widget, stretch_table_widget_colums_size, list_widget_contains_item, is_url_reachable, get_logical_table_row_list, is_flatpak, get_shared_temp_dir, is_url_valid, get_save_settings, assert_func, get_sender_table_row
from PyQt6.QtWidgets import QApplication, QCheckBox, QComboBox, QLineEdit, QListWidget, QMainWindow, QMessageBox, QDateEdit, QInputDialog, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QRadioButton, QFileDialog
from PyQt6.QtGui import QAction, QDragEnterEvent, QDropEvent, QCloseEvent
from .ComposeDirectoryWindow import ComposeDirectoryWindow
from .ManageTemplatesWindow import ManageTemplatesWindow
from .Types import ScreenshotDict, ScreenshotDictImage
from PyQt6.QtCore import Qt, QCoreApplication, QDate
from .ui_compiled.MainWindow import Ui_MainWindow
from .DescriptionWidget import DescriptionWidget
from typing import List, Optional, TYPE_CHECKING
from .ViewCatalogWindow import ViewCatalogWindow
from .ScreenshotWindow import ScreenshotWindow
from .RelationsWidget import RelationsWidget
from .ReleasesWidget import ReleasesWidget
from .SettingsWindow import SettingsWindow
from .ValidateWindow import ValidateWindow
from .AdvancedWidget import AdvancedWidget
from .SysinfoWindow import SysinfoWindow
from .ViewXMLWindow import ViewXMLWindow
from .PluginWindow import PluginWindow
from .AboutWindow import AboutWindow
from .OarsWidget import OarsWidget
from .Constants import XML_LANG
from lxml import etree
import webbrowser
import subprocess
import requests
import shutil
import sys
import os
import io


if TYPE_CHECKING:
    from .Environment import Environment


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, env: "Environment") -> None:
        super().__init__()
        self._env = env

        self.setupUi(self)

        self._current_path = None

        self._settings_window = SettingsWindow(env, self)
        self._manage_templates_window = ManageTemplatesWindow(env, self)
        self._plugin_window = PluginWindow(env, self)
        self._validate_window = ValidateWindow(env, self)
        self._xml_window = ViewXMLWindow(env, self)
        self._view_catalog_window = ViewCatalogWindow(env, self)
        self._screenshot_window = ScreenshotWindow(env, self)
        self._releases_widget = ReleasesWidget(env, self)
        self._compose_directory_window = ComposeDirectoryWindow(self)
        self._sysinfo_window = SysinfoWindow(env, self)
        self._about_window = AboutWindow(env, self)

        self._description_widget = DescriptionWidget(env, self)
        self.description_layout.addWidget(self._description_widget)

        self.releases_layout.replaceWidget(self.releases_widget_placeholder, self._releases_widget)
        self.releases_widget_placeholder.setParent(None)

        self._relations_widget = RelationsWidget(self)
        self.relations_layout.addWidget(self._relations_widget)

        self._oars_widget = OarsWidget(self)
        self.oras_layout.addWidget(self._oars_widget)

        self._advanced_widget = AdvancedWidget(self)
        self.advanced_layout.addWidget(self._advanced_widget)

        self.screenshot_list: list[ScreenshotDict] = []

        self._url_list = []
        self._control_type_list = []
        for key, value in vars(self).items():
            if key.endswith("_url_edit"):
                self._url_list.append(key[:-9])
            elif key.startswith("control_box_"):
                self._control_type_list.append(key[12:])
                value.addItem(QCoreApplication.translate("MainWindow", "Not specified"), "none")
                value.addItem(QCoreApplication.translate("MainWindow", "Required"), "requires")
                value.addItem(QCoreApplication.translate("MainWindow", "Recommend"), "recommends")
                value.addItem(QCoreApplication.translate("MainWindow", "Supported"), "supports")
            if isinstance(value, QLineEdit):
                value.textEdited.connect(self.set_file_edited)
            elif isinstance(value, QComboBox):
                value.currentIndexChanged.connect(self.set_file_edited)
            elif isinstance(value, QPlainTextEdit):
                value.modificationChanged.connect(self.set_file_edited)
            elif isinstance(value, QTableWidget):
                value.verticalHeader().sectionMoved.connect(self.set_file_edited)
            elif isinstance(value, QListWidget):
                value.model().rowsMoved.connect(self.set_file_edited)
            elif isinstance(value, QRadioButton):
                value.toggled.connect(self.set_file_edited)
            elif isinstance(value, QCheckBox):
                value.stateChanged.connect(self.set_file_edited)
            elif isinstance(value, QDateEdit):
                value.dateChanged.connect(self.set_file_edited)
                value.setDate(QDate.currentDate())

        self._update_new_template_file_menu()
        self._update_recent_files_menu()

        self.component_type_box.addItem(QCoreApplication.translate("MainWindow", "Desktop"), ["desktop-application", "desktop"])
        self.component_type_box.addItem(QCoreApplication.translate("MainWindow", "Console"), ["console-application"])
        self.component_type_box.addItem(QCoreApplication.translate("MainWindow", "Web Application"), ["web-application"])
        self.component_type_box.addItem(QCoreApplication.translate("MainWindow", "Service"), ["service"])
        self.component_type_box.addItem(QCoreApplication.translate("MainWindow", "Addon"), ["addon"])
        self.component_type_box.addItem(QCoreApplication.translate("MainWindow", "Font"), ["font"])
        self.component_type_box.addItem(QCoreApplication.translate("MainWindow", "Icon Theme"), ["icon-theme"])
        self.component_type_box.addItem(QCoreApplication.translate("MainWindow", "Codecs"), ["codec"])
        self.component_type_box.addItem(QCoreApplication.translate("MainWindow", "Input Method"), ["inputmethod"])
        self.component_type_box.addItem(QCoreApplication.translate("MainWindow", "Firmware"), ["firmware"])

        for key, value in env.metadata_license_list.items():
            self.metadata_license_box.addItem(f"{value} ({key})", key)

        for license in env.project_license_list["licenses"]:
            if not license["isDeprecatedLicenseId"]:
                self.project_license_box.addItem(f'{license["name"]} ({license["licenseId"]})', license["licenseId"])

        self.metadata_license_box.model().sort(0, Qt.SortOrder.AscendingOrder)
        self.project_license_box.model().sort(0, Qt.SortOrder.AscendingOrder)

        unknown_text = QCoreApplication.translate("MainWindow", "Unknown")
        self.metadata_license_box.insertItem(0, unknown_text, "unknown")
        self.project_license_box.insertItem(0, unknown_text, "unknown")

        self.metadata_license_box.setCurrentIndex(0)
        self.project_license_box.setCurrentIndex(0)

        self.internal_releases_radio_button.setChecked(True)

        stretch_table_widget_colums_size(self.screenshot_table)
        stretch_table_widget_colums_size(self.launchable_table)
        stretch_table_widget_colums_size(self.provides_table)

        self.screenshot_table.verticalHeader().setSectionsMovable(True)
        self.launchable_table.verticalHeader().setSectionsMovable(True)
        self.provides_table.verticalHeader().setSectionsMovable(True)

        self._update_end_of_life_enabled()
        self._update_releases_enabled()
        self._update_categorie_remove_button_enabled()
        self._update_keyword_edit_remove_button()

        self._edited = False

        self._name_translations = {}
        self._summary_translations = {}
        self._developer_name_translations = {}

        self.translate_name_button.clicked.connect(lambda: env.translate_window.open_window(self._name_translations))
        self.translate_summary_button.clicked.connect(lambda: env.translate_window.open_window(self._summary_translations))
        self.translate_developer_name_button.clicked.connect(lambda: env.translate_window.open_window(self._developer_name_translations))
        self.end_of_life_check_box.stateChanged.connect(self._update_end_of_life_enabled)

        self.screenshot_table.verticalHeader().sectionMoved.connect(self._screenshot_table_row_moved)
        self.screenshot_add_button.clicked.connect(lambda: self._screenshot_window.open_window(None))
        self.check_screenshot_url_button.clicked.connect(self._check_screenshot_urls)

        self.internal_releases_radio_button.toggled.connect(self._update_releases_enabled)

        self.check_links_url_button.clicked.connect(self._check_links_url_button_clicked)

        self.categorie_list.itemSelectionChanged.connect(self._update_categorie_remove_button_enabled)
        self.categorie_add_button.clicked.connect(self._add_categorie_button_clicked)

        self.categorie_remove_button.clicked.connect(self._remove_categorie_button_clicked)

        self.launchable_add_button.clicked.connect(self._add_launchable_row)

        self.provides_add_button.clicked.connect(self._add_provides_row)

        self.keyword_list.itemDoubleClicked.connect(self._edit_keyword)
        self.keyword_list.itemSelectionChanged.connect(self._update_keyword_edit_remove_button)
        self.keyword_add_button.clicked.connect(self._add_keyword)
        self.keyword_edit_button.clicked.connect(self._edit_keyword)
        self.keyword_remove_button.clicked.connect(self._remove_keyword)

        self.new_action.triggered.connect(self._new_menu_action_clicked)
        self.new_desktop_file_action.triggered.connect(self._new_from_desktop_action_clicked)
        self.open_action.triggered.connect(self._open_menu_action_clicked)
        self.open_url_action.triggered.connect(self._open_url_clicked)
        self.save_action.triggered.connect(self._save_file_clicked)
        self.save_as_action.triggered.connect(self._save_as_clicked)
        self.exit_action.triggered.connect(self._exit_menu_action_clicked)

        self.settings_action.triggered.connect(self._settings_window.open_window)
        self.manage_templates_action.triggered.connect(self._manage_templates_window.exec)
        self.plugins_action.triggered.connect(self._open_plugin_settings)

        self.validate_action.triggered.connect(self._validate_window.open_window)
        self.view_xml_action.triggered.connect(self._xml_window.exec)
        self.preview_gnome_software.triggered.connect(lambda: self._previev_appstream_file(["gnome-software", "--show-metainfo"]))
        self.view_catalog_action.triggered.connect(self._view_catalog_window.open_window)
        self.compose_directory_action.triggered.connect(self._compose_directory_window.open_window)
        self.sysinfo_action.triggered.connect(self._sysinfo_window.open_window)

        self.welcome_dialog_action.triggered.connect(self.show_welcome_dialog)
        self.documentation_action.triggered.connect(lambda: webbrowser.open("https://www.freedesktop.org/software/appstream/docs"))
        self.view_source_action.triggered.connect(lambda: webbrowser.open("https://codeberg.org/JakobDev/jdAppStreamEdit"))
        self.report_bug_action.triggered.connect(lambda: webbrowser.open("https://codeberg.org/JakobDev/jdAppStreamEdit/issues"))
        self.translate_action.triggered.connect(lambda: webbrowser.open("https://translate.codeberg.org/projects/jdAppStreamEdit"))
        self.donate_action.triggered.connect(lambda: webbrowser.open("https://ko-fi.com/jakobdev"))
        self.about_action.triggered.connect(self._about_window.exec)
        self.about_qt_action.triggered.connect(QApplication.instance().aboutQt)

        self.setAcceptDrops(True)

        self.main_tab_widget.setCurrentIndex(0)
        self.update_window_title()

    def set_file_edited(self) -> None:
        self._edited = True
        self.update_window_title()

    def update_window_title(self) -> None:
        if self._env.settings.get("windowTitleType") == "none":
            title = "jdAppStreamEdit"
        elif self._current_path is None:
            title = QCoreApplication.translate("MainWindow", "Untitled") + " - jdAppStreamEdit"
        elif self._env.settings.get("windowTitleType") == "filename":
            title = os.path.basename(self._current_path) + " - jdAppStreamEdit"
        elif self._env.settings.get("windowTitleType") == "path":
            title = self._current_path + " - jdAppStreamEdit"
        else:
            title = QCoreApplication.translate("MainWindow", "Error")

        if self._edited and self._env.settings.get("showEditedTitle"):
            self.setWindowTitle("*" + title)
        else:
            self.setWindowTitle(title)

    def _update_new_template_file_menu(self) -> None:
        self.new_template_file_menu.clear()

        if len(self._env.template_list) == 0:
            empty_action = QAction(QCoreApplication.translate("MainWindow", "No templates found"), self)
            empty_action.setEnabled(False)
            self.new_template_file_menu.addAction(empty_action)
        else:
            for i in self._env.template_list:
                template_action = QAction(i, self)
                template_action.setData(i)
                template_action.triggered.connect(self._new_template_file_clicked)
                self.new_template_file_menu.addAction(template_action)

    def _update_recent_files_menu(self) -> None:
        self.recent_files_menu.clear()

        if len(self._env.recent_files) == 0:
            empty_action = QAction(QCoreApplication.translate("MainWindow", "No recent files"), self)
            empty_action.setEnabled(False)
            self.recent_files_menu.addAction(empty_action)
            return

        for i in self._env.recent_files:
            file_action = QAction(i, self)
            file_action.setData(i)
            file_action.triggered.connect(self._open_recent_file)
            self.recent_files_menu.addAction(file_action)

        self.recent_files_menu.addSeparator()

        clear_action = QAction(QCoreApplication.translate("MainWindow", "Clear"), self)
        clear_action.triggered.connect(self._clear_recent_files)
        self.recent_files_menu.addAction(clear_action)

    def add_to_recent_files(self, path: str) -> None:
        while path in self._env.recent_files:
            self._env.recent_files.remove(path)
        self._env.recent_files.insert(0, path)
        self._env.recent_files = self._env.recent_files[:self._env.settings.get("recentFilesLength")]
        self._update_recent_files_menu()
        self._env.save_recent_files()

    def _ask_for_save(self) -> bool:
        if not self._edited:
            return True
        if not self._env.settings.get("checkSaveBeforeClosing"):
            return True
        answer = QMessageBox.warning(self, QCoreApplication.translate("MainWindow", "Unsaved changes"), QCoreApplication.translate("MainWindow", "You have unsaved changes. Do you want to save now?"), QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Save:
            self._save_file_clicked()
            return True
        elif answer == QMessageBox.StandardButton.Discard:
            return True
        elif answer == QMessageBox.StandardButton.Cancel:
            return False

    def show_welcome_dialog(self) -> None:
        text = "<center>"
        text += QCoreApplication.translate("MainWindow", "Welcome to jdAppStreamEdit!") + "<br><br>"
        text += QCoreApplication.translate("MainWindow", "With jdAppStreamEdit you can create and edit AppStream files (*.metainfo.xml or .appdata.xml). This files are to provide data for your Application (Description, Screenshots etc.) to Software Centers.") + "<br><br>"
        text += QCoreApplication.translate("MainWindow", "It is highly recommend to read the the AppStream Documentation before using this Program. You can open it under ?>AppStream documentation.") + "<br><br>"
        text += QCoreApplication.translate("MainWindow", "You can check if your AppStream is valid under Tools>Validate.")
        text += "</center>"

        check_box = QCheckBox(QCoreApplication.translate("MainWindow", "Show this dialog at startup"))
        check_box.setChecked(self._env.settings.get("showWelcomeDialog"))

        message_box = QMessageBox(self)
        message_box.setWindowTitle(QCoreApplication.translate("MainWindow", "Welcome"))
        message_box.setText(text)
        message_box.setCheckBox(check_box)

        message_box.exec()

        self._env.settings.set("showWelcomeDialog", check_box.isChecked())
        self._env.settings.save(os.path.join(self._env.data_dir, "settings.json"))

    def _new_menu_action_clicked(self) -> None:
        if not self._ask_for_save():
            return
        self.reset_data()
        self._edited = False
        self._current_path = None
        self.update_window_title()

    def _new_from_desktop_action_clicked(self) -> None:
        try:
            import desktop_entry_lib
        except ModuleNotFoundError:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "desktop-entry-lib not found"), QCoreApplication.translate("MainWindow", "This function needs the desktop-entry-lib python module to work"))
            return

        if not self._ask_for_save():
            return

        self.reset_data()

        filter = QCoreApplication.translate("MainWindow", "Desktop Entry Files") + " (*.desktop);;" + QCoreApplication.translate("MainWindow", "All Files") + " (*)"
        path = QFileDialog.getOpenFileName(self, filter=filter)[0]
        if path == "":
            return

        try:
            entry = desktop_entry_lib.DesktopEntry.from_file(path)
        except Exception:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Could not read file"), QCoreApplication.translate("MainWindow", "Could not read {{path}}. Make sure it is a valid desktop entry and you have the Permission to read it.").replace("{{path}}", path))
            return

        self.id_edit.setText(entry.desktop_id)

        self.name_edit.setText(entry.Name.default_text)
        for key, value in entry.Name.translations.items():
            self._name_translations[key] = value

        self.summary_edit.setText(entry.Comment.default_text)
        for key, value in entry.Comment.translations.items():
            self._summary_translations[key] = value

        self._add_launchable_row(value_type="deskop-id", value=os.path.basename(path))

        for i in entry.Categories:
            self.categorie_list.addItem(i)

        try:
            prog = entry.Exec.split(" ")[0]
            assert_func(prog == os.path.basename(prog))
            self._add_provides_row("binary", prog)
        except Exception:
            pass

        for i in entry.MimeType:
            self._add_provides_row("mediatype", i)

        for i in entry.Keywords.default_list:
            self.keyword_list.addItem(i)

        self._edited = False
        self._current_path = None
        self.update_window_title()

    def _new_template_file_clicked(self) -> None:
        if not self._ask_for_save():
            return

        action = self.sender()

        if not action:
            return

        self.open_file(os.path.join(self._env.data_dir, "templates", action.data() + ".metainfo.xml"), template=True)

    def _open_menu_action_clicked(self) -> None:
        if not self._ask_for_save():
            return

        filter = QCoreApplication.translate("MainWindow", "AppStream Files") + " (*.metainfo.xml *.metainfo.xml.in *.appdata.xml *.appdata.xml.in);;" + QCoreApplication.translate("MainWindow", "All Files") + " (*)"
        path = QFileDialog.getOpenFileName(self, filter=filter)

        if path[0] == "":
            return

        self.open_file(path[0])
        self.add_to_recent_files(path[0])

    def _open_recent_file(self) -> None:
        if not self._ask_for_save():
            return
        action = self.sender()
        if not action:
            return
        self.open_file(action.data())
        self.add_to_recent_files(action.data())

    def _open_url_clicked(self) -> None:
        if not self._ask_for_save():
            return

        url = QInputDialog.getText(self, QCoreApplication.translate("MainWindow", "Enter URL"), QCoreApplication.translate("MainWindow", "Please enter a URL"))[0]

        if url != "":
            self.open_url(url)

    def _save_file_clicked(self) -> None:
        if self._current_path is None:
            self._save_as_clicked()
            return

        self.save_file(self._current_path)
        self.add_to_recent_files(self._current_path)
        self._edited = False
        self.update_window_title()

    def _save_as_clicked(self) -> None:
        filter = QCoreApplication.translate("MainWindow", "AppStream Files") + " (*.metainfo.xml *.appdata.xml);;" + QCoreApplication.translate("MainWindow", "All Files") + " (*)"
        path = QFileDialog.getSaveFileName(self, filter=filter)[0]

        if path == "":
            return

        self._current_path = path
        self.save_file(path)
        self.add_to_recent_files(path)
        self._edited = False
        self.update_window_title()

    def _exit_menu_action_clicked(self) -> None:
        if self._ask_for_save():
            sys.exit(0)

    def _clear_recent_files(self) -> None:
        self._env.recent_files.clear()
        self._update_recent_files_menu()
        self._env.save_recent_files()

    def _open_plugin_settings(self) -> None:
        if len(self._env.plugin_list) == 0:
            QMessageBox.information(self, QCoreApplication.translate("MainWindow", "No Plugins installed"), QCoreApplication.translate("MainWindow", "You have no Plugins installed"))
            return

        self._plugin_window.exec()

    # General

    def _update_end_of_life_enabled(self) -> None:
        enabled = self.end_of_life_check_box.isChecked()
        self.end_of_life_label.setEnabled(enabled)
        self.end_of_life_date_edit.setEnabled(enabled)

    # Screenshots

    def update_screenshot_table(self) -> None:
        clear_table_widget(self.screenshot_table)
        for row, i in enumerate(self.screenshot_list):
            self.screenshot_table.insertRow(row)

            url_item = QTableWidgetItem(i["source_url"])
            url_item.setFlags(url_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.screenshot_table.setItem(row, 0, url_item)

            default_button = QRadioButton()
            if i["default"]:
                default_button.setChecked(True)
            default_button.clicked.connect(self._default_button_clicked)
            self.screenshot_table.setCellWidget(row, 1, default_button)

            edit_button = QPushButton(QCoreApplication.translate("MainWindow", "Edit"))
            edit_button.clicked.connect(self._edit_screenshot_button_clicked)
            self.screenshot_table.setCellWidget(row, 2, edit_button)

            remove_button = QPushButton(QCoreApplication.translate("MainWindow", "Remove"))
            remove_button.clicked.connect(self._remove_screenshot_clicked)
            self.screenshot_table.setCellWidget(row, 3, remove_button)

    def _check_screenshot_urls(self) -> None:
        for screenshot in self.screenshot_list:
            for image in screenshot["images"]:
                if not is_url_reachable(image["url"]):
                    QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Invalid URL"), QCoreApplication.translate("MainWindow", "The URL {{url}} does not work").replace("{{url}}", image["url"]))
                    return
        QMessageBox.information(self, QCoreApplication.translate("MainWindow", "Everything OK"), QCoreApplication.translate("MainWindow", "All URLs are working"))

    def _default_button_clicked(self) -> None:
        for count, i in enumerate(self.screenshot_list):
            if self.screenshot_table.cellWidget(count, 1).isChecked():
                i["default"] = True
            else:
                i["default"] = False
        self.set_file_edited()

    def _edit_screenshot_button_clicked(self) -> None:
        for i in range(self.screenshot_table.rowCount()):
            if self.screenshot_table.cellWidget(i, 2) == self.sender():
                self._screenshot_window.open_window(i)
                return

    def _remove_screenshot_clicked(self) -> None:
        for i in range(self.screenshot_table.rowCount()):
            if self.screenshot_table.cellWidget(i, 3) == self.sender():
                default = self.screenshot_list[i]["default"]
                del self.screenshot_list[i]
                if default and len(self.screenshot_list) != 0:
                    self.screenshot_list[0]["default"] = True
                self.update_screenshot_table()
                self.set_file_edited()
                return

    def _screenshot_table_row_moved(self, logical_index: int, old_visual_index: int, new_visual_index: int) -> None:
        item = self.screenshot_list[old_visual_index]
        if new_visual_index == len(self.screenshot_list) - 1:
            self.screenshot_list.append(item)
        else:
            if new_visual_index > old_visual_index:
                self.screenshot_list.insert(new_visual_index + 1, item)
            else:
                self.screenshot_list.insert(new_visual_index, item)
        if new_visual_index > old_visual_index:
            del self.screenshot_list[old_visual_index]
        else:
            del self.screenshot_list[old_visual_index + 1]
        self.update_screenshot_table()

    # Releases

    def _update_releases_enabled(self) -> None:
        internal = self.internal_releases_radio_button.isChecked()
        self._releases_widget.setEnabled(internal)
        self.external_releases_url_label.setEnabled(not internal)
        self.external_releases_url_edit.setEnabled(not internal)

    # Links

    def _check_links_url_button_clicked(self) -> None:
        for i in self._url_list:
            url = getattr(self, f"{i}_url_edit").text()
            if url == "":
                continue
            if not is_url_reachable(url):
                QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Invalid URL"), QCoreApplication.translate("MainWindow", "The URL {url} does not work").format(url=url))
                return
        QMessageBox.information(self, QCoreApplication.translate("MainWindow", "Everything OK"), QCoreApplication.translate("MainWindow", "All URLs are working"))

    # Categories

    def _update_categorie_remove_button_enabled(self) -> None:
        if self.categorie_list.currentRow() == -1:
            self.categorie_remove_button.setEnabled(False)
        else:
            self.categorie_remove_button.setEnabled(True)

    def _add_categorie_button_clicked(self) -> None:
        categorie, ok = QInputDialog.getItem(self, QCoreApplication.translate("MainWindow", "Add a Categorie"), QCoreApplication.translate("MainWindow", "Please select a Categorie from the list below"), self._env.categories, 0, False)
        if not ok:
            return
        if list_widget_contains_item(self.categorie_list, categorie):
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Categorie already added"), QCoreApplication.translate("MainWindow", "You can't add the same Categorie twice"))
        else:
            self.categorie_list.addItem(categorie)
            self._update_categorie_remove_button_enabled()
            self.set_file_edited()

    def _remove_categorie_button_clicked(self) -> None:
        row = self.categorie_list.currentRow()
        if row == -1:
            return
        self.categorie_list.takeItem(row)
        self._update_categorie_remove_button_enabled()
        self.set_file_edited()

    # Launchable

    def _add_launchable_row(self, value_type: Optional[str] = None, value: str = "") -> None:
        row = self.launchable_table.rowCount()
        self.launchable_table.insertRow(row)

        type_box = QComboBox()
        type_box.addItem("desktop-id", "desktop-id")
        type_box.addItem("service", "service")
        type_box.addItem("cockpit-manifest", "cockpit-manifest")
        type_box.addItem("url", "url")
        if value_type:
            index = type_box.findData(value_type)
            if index != -1:
                type_box.setCurrentIndex(index)
            else:
                print(f"Unkown provides type {value_type}", file=sys.stderr)
        self.launchable_table.setCellWidget(row, 0, type_box)

        self.launchable_table.setItem(row, 1, QTableWidgetItem(value))

        remove_button = QPushButton(QCoreApplication.translate("MainWindow", "Remove"))
        remove_button.clicked.connect(self._remove_launchable_button_clicked)
        self.launchable_table.setCellWidget(row, 2, remove_button)

        self.set_file_edited()

    def _remove_launchable_button_clicked(self) -> None:
        row = get_sender_table_row(self.launchable_table, 2, self.sender())
        self.launchable_table.removeRow(row)

    # Provides

    def _add_provides_row(self, value_type: Optional[str] = None, value: str = "") -> None:
        row = self.provides_table.rowCount()
        self.provides_table.insertRow(row)

        type_box = QComboBox()
        type_box.addItem("mediatype", "mediatype")
        type_box.addItem("library", "library")
        type_box.addItem("binary", "binary")
        type_box.addItem("font", "font")
        type_box.addItem("modalias", "modalias")
        type_box.addItem("firmware", "firmware")
        type_box.addItem("python3", "python3")
        type_box.addItem("dbus-user", "dbus-user")
        type_box.addItem("dbus-system", "dbus-system")
        type_box.addItem("id", "id")
        if value_type:
            index = type_box.findData(value_type)
            if index != -1:
                type_box.setCurrentIndex(index)
            else:
                print(f"Unkown provides type {value_type}", file=sys.stderr)
        self.provides_table.setCellWidget(row, 0, type_box)

        self.provides_table.setItem(row, 1, QTableWidgetItem(value))

        remove_button = QPushButton(QCoreApplication.translate("MainWindow", "Remove"))
        remove_button.clicked.connect(self._remove_provides_button_clicked)
        self.provides_table.setCellWidget(row, 2, remove_button)

        self.set_file_edited()

    def _remove_provides_button_clicked(self) -> None:
        for i in range(self.provides_table.rowCount()):
            if self.provides_table.cellWidget(i, 2) == self.sender():
                self.provides_table.removeRow(i)
                self.set_file_edited()
                return

    # Keywords

    def _add_keyword(self) -> None:
        text, ok = QInputDialog.getText(self, QCoreApplication.translate("MainWindow", "New Keyword"), QCoreApplication.translate("MainWindow", "Please enter a new Keyword"))
        if not ok:
            return
        if list_widget_contains_item(self.keyword_list, text):
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Keyword in List"), QCoreApplication.translate("MainWindow", "This Keyword is already in the List"))
            return
        self.keyword_list.addItem(text)
        self._update_keyword_edit_remove_button()
        self.set_file_edited()

    def _edit_keyword(self) -> None:
        if self.keyword_list.currentRow() == -1:
            return
        old_text = self.keyword_list.currentItem().text()
        new_text, ok = QInputDialog.getText(self, QCoreApplication.translate("MainWindow", "Edit Keyword"), QCoreApplication.translate("MainWindow", "Please edit the Keyword"), text=old_text)

        if not ok or old_text == new_text:
            return

        if list_widget_contains_item(self.keyword_list, new_text):
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Keyword in List"), QCoreApplication.translate("MainWindow", "This Keyword is already in the List"))
            return

        self.keyword_list.currentItem().setText(new_text)
        self.set_file_edited()

    def _remove_keyword(self) -> None:
        index = self.keyword_list.currentRow()
        if index != -1:
            self.keyword_list.takeItem(index)
            self._update_keyword_edit_remove_button()
            self.set_file_edited()

    def _update_keyword_edit_remove_button(self) -> None:
        if self.keyword_list.currentRow() == -1:
            self.keyword_edit_button.setEnabled(False)
            self.keyword_remove_button.setEnabled(False)
        else:
            self.keyword_edit_button.setEnabled(True)
            self.keyword_remove_button.setEnabled(True)

    # Other Functions

    def get_id(self) -> str:
        return self.id_edit.text()

    def reset_data(self) -> None:
        for value in vars(self).values():
            if isinstance(value, QLineEdit):
                value.setText("")
            elif isinstance(value, QComboBox):
                value.setCurrentIndex(0)
            elif isinstance(value, QPlainTextEdit):
                value.setPlainText("")
            elif isinstance(value, QTableWidget):
                clear_table_widget(value)
            elif isinstance(value, QCheckBox):
                value.setChecked(False)
            elif isinstance(value, QListWidget):
                value.clear()
            elif isinstance(value, QDateEdit):
                value.setDate(QDate.currentDate())
        self.end_of_life_check_box.setChecked(False)
        self._description_widget.reset_data()
        self.screenshot_list.clear()
        self.internal_releases_radio_button.setChecked(True)
        self._releases_widget.reset_data()
        self._relations_widget.reset_data()
        self._oars_widget.reset_data()
        self._name_translations.clear()
        self._summary_translations.clear()
        self._advanced_widget.reset_data()
        self._update_categorie_remove_button_enabled()
        self._update_keyword_edit_remove_button()
        self._update_end_of_life_enabled()

    # Read

    def open_file(self, path: str, template: bool = False) -> bool:
        try:
            with open(path, "rb") as f:
                text = f.read()
        except FileNotFoundError:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "File not found"), QCoreApplication.translate("MainWindow", "{{path}} does not exists").replace("{{path}}", path))
            return
        except Exception:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Error"), QCoreApplication.translate("MainWindow", "An error occurred while trying to open {{path}}").replace("{{path}}", path))
            return

        if self.load_xml(text):
            if template:
                self._current_path = None
            else:
                self._current_path = path
            self.update_window_title()
            return True
        else:
            return False

    def open_url(self, url: str) -> None:
        if not is_url_valid(url):
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Invalid URL"), QCoreApplication.translate("MainWindow", "{{url}} is not a valid http/https URL").replace("{{url}}", url))
            return

        try:
            r = requests.get(url, timeout=10)
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Could not connect"), QCoreApplication.translate("MainWindow", "Could not connect to {{url}}").replace("{{url}}", url))
            return
        except Exception:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Error"), QCoreApplication.translate("MainWindow", "An error occurred while trying to connect to {{url}}").replace("{{url}}", url))
            return

        if self.load_xml(r.content):
            self._current_path = None
            self.update_window_title()

    def _parse_screenshots_tag(self, screenshots_tag: etree._Element) -> None:
        for i in screenshots_tag.getchildren():
            if i.tag != "screenshot":
                continue

            new_dict: ScreenshotDict = {
                "default": i.get("type") == "default",
                "caption": None,
                "caption_translations": {},
                "images": []
            }

            for image_tag in i.findall("image"):
                image: ScreenshotDictImage = {
                    "url": image_tag.text,
                    "type": image_tag.get("type", "source"),
                    "language": image_tag.get(XML_LANG),
                    "width": image_tag.get("width"),
                    "height": image_tag.get("height")
                }

                if (scale := image_tag.get("scale")) is not None:
                    try:
                        image["scale_factor"] = int(scale)
                    except ValueError:
                        image["scale_factor"] = None
                        print(f"{scale} is not an integer", file=sys.stderr)
                else:
                    image["scale_factor"] = None

                if image["type"] == "source" and image["language"] is None:
                    new_dict["source_url"] = image["url"]

                new_dict["images"].append(image)

            for caption_tag in i.findall("caption"):
                if caption_tag.get(XML_LANG) is None:
                    new_dict["caption"] = caption_tag.text
                else:
                    new_dict["caption_translations"][caption_tag.get(XML_LANG)] = caption_tag.text

            self.screenshot_list.append(new_dict)

        self.update_screenshot_table()

    def load_xml(self, xml_data: bytes) -> bool:
        xml_data = xml_data.replace(b"<code>", b"&lt;code&gt;")
        xml_data = xml_data.replace(b"</code>", b"&lt;/code&gt;")
        xml_data = xml_data.replace(b"<em>", b"&lt;em&gt;")
        xml_data = xml_data.replace(b"</em>", b"&lt;/em&gt;")

        try:
            root = etree.parse(io.BytesIO(xml_data))
        except etree.XMLSyntaxError as ex:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "XML parsing failed"), ex.msg)
            return False

        if len(root.xpath("/component")) == 0:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "No component tag"), QCoreApplication.translate("MainWindow", "This XML file has no component tag"))
            return False
        elif len(root.xpath("/component")) > 2:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Too many component tags"), QCoreApplication.translate("MainWindow", "Only files with one component tag are supported"))
            return False

        self.reset_data()

        component_type = root.xpath("/component")[0].get("type")
        for i in range(self.component_type_box.count()):
            if component_type in self.component_type_box.itemData(i):
                self.component_type_box.setCurrentIndex(i)
                break

        if (date_eol := root.getroot().get("date_eol")) is not None:
            self.end_of_life_date_edit.setDate(QDate.fromString(date_eol, Qt.DateFormat.ISODate))
            self.end_of_life_check_box.setChecked(True)

        id_tag = root.find("id")
        if id_tag is not None:
            self.id_edit.setText(id_tag.text)

        for i in root.findall("name"):
            if i.get("{http://www.w3.org/XML/1998/namespace}lang") is None:
                self.name_edit.setText(i.text)
            else:
                self._name_translations[i.get("{http://www.w3.org/XML/1998/namespace}lang")] = i.text

        for i in root.findall("summary"):
            if i.get("{http://www.w3.org/XML/1998/namespace}lang") is None:
                self.summary_edit.setText(i.text)
            else:
                self._summary_translations[i.get("{http://www.w3.org/XML/1998/namespace}lang")] = i.text

        for i in root.findall("developer_name"):
            if i.get("{http://www.w3.org/XML/1998/namespace}lang") is None:
                self.developer_name_edit.setText(i.text)
            else:
                self._developer_name_translations[i.get("{http://www.w3.org/XML/1998/namespace}lang")] = i.text

        if (developer_tag := root.find("developer")) is not None:
            self.developer_id_edit.setText(developer_tag.get("id", ""))
            self.developer_name_edit.setText("")
            self._developer_name_translations.clear()
            for i in developer_tag.findall("name"):
                if i.get("{http://www.w3.org/XML/1998/namespace}lang") is None:
                    self.developer_name_edit.setText(i.text)
                else:
                    self._developer_name_translations[i.get("{http://www.w3.org/XML/1998/namespace}lang")] = i.text

        metadata_license_tag = root.find("metadata_license")
        if metadata_license_tag is not None:
            index = self.metadata_license_box.findData(metadata_license_tag.text)
            if index != -1:
                self.metadata_license_box.setCurrentIndex(index)

        project_license_tag = root.find("project_license")
        if project_license_tag is not None:
            # update deprecated license tag
            if project_license_tag.text.endswith("+"):
                project_license_tag.text = project_license_tag.text[:-1] + "-or-later"
            index = self.project_license_box.findData(project_license_tag.text)
            if index != -1:
                self.project_license_box.setCurrentIndex(index)
            else:
                index = self.project_license_box.findData(project_license_tag.text + "-only")
                if index != -1:
                    self.project_license_box.setCurrentIndex(index)

        update_contact_tag = root.find("update_contact")
        if update_contact_tag is not None:
            self.update_contact_edit.setText(update_contact_tag.text)

        project_group_tag = root.find("project_group")
        if project_group_tag is not None:
            self.project_group_edit.setText(project_group_tag.text)

        description_tag = root.find("description")
        if description_tag is not None:
            self._description_widget.load_tags(description_tag)

        screenshots_tag = root.find("screenshots")
        if screenshots_tag is not None:
            self._parse_screenshots_tag(screenshots_tag)

        if (releases_tag := root.find("releases")) is not None:
            if releases_tag.get("type") == "external":
                self.external_releases_radio_button.setChecked(True)
                if releases_tag.get("url") is not None:
                    self.external_releases_url_edit.setText(releases_tag.get("url"))
                else:
                    self.external_releases_url_edit.setText("")
            else:
                self._releases_widget.load_tag(releases_tag)

        categories_tag = root.find("categories")
        if categories_tag is not None:
            for i in categories_tag.getchildren():
                self.categorie_list.addItem(i.text)

        for i in root.findall("url"):
            try:
                getattr(self, i.get("type").replace("-", "_") + "_url_edit").setText(i.text)
            except AttributeError:
                print(f"Unknown URL type {i.get('type')}", file=sys.stderr)

        for a in ["requires", "recommends", "supports"]:
            current_tag = root.find(a)
            if current_tag is None:
                continue
            for i in current_tag.findall("control"):
                try:
                    box = getattr(self, "control_box_" + i.text.replace("-", "_"))
                    index = box.findData(a)
                    box.setCurrentIndex(index)
                except AttributeError:
                    print(f"Unknown value {i.text} for control tag")
            self._relations_widget.load_data(current_tag)

        content_rating_tag = root.find("content_rating")
        if content_rating_tag is not None:
            self._oars_widget.open_file(content_rating_tag)

        for launchable_tag in root.findall("launchable"):
            self._add_launchable_row(value_type=launchable_tag.get("type"), value=launchable_tag.text)

        provides_tag = root.find("provides")
        if provides_tag is not None:
            for i in provides_tag.getchildren():
                if i.tag == "dbus":
                    if i.get("type") == "user":
                        self._add_provides_row(value_type="dbus-user", value=i.text)
                    elif i.get("type") == "system":
                        self._add_provides_row(value_type="dbus-system", value=i.text)
                    else:
                        print("Invalid dbus type " + i.get("type"), file=sys.stderr)
                else:
                    self._add_provides_row(value_type=i.tag, value=i.text)

        keywords_tag = root.find("keywords")
        if keywords_tag is not None:
            for i in keywords_tag.findall("keyword"):
                self.keyword_list.addItem(i.text)

        self._advanced_widget.load_data(root)

        self._edited = False

        return True

    # Write

    def _get_screenshot_tag(self, screenshot: ScreenshotDict) -> etree.Element:
        screenshot_tag = etree.Element("screenshot")

        if screenshot["default"]:
            screenshot_tag.set("type", "default")

        if screenshot["caption"] is not None:
            caption_tag = etree.SubElement(screenshot_tag, "caption")
            caption_tag.text = screenshot["caption"]

        if screenshot["caption_translations"] is not None:
            for key, value in screenshot["caption_translations"].items():
                caption_trans_tag = etree.SubElement(screenshot_tag, "caption")
                caption_trans_tag.set("{http://www.w3.org/XML/1998/namespace}lang", key)
                caption_trans_tag.text = value

        for image in screenshot["images"]:
            image_tag = etree.SubElement(screenshot_tag, "image")
            image_tag.set("type", image["type"])

            if image["language"] is not None:
                image_tag.set("{http://www.w3.org/XML/1998/namespace}lang", image["language"])

            if image["width"] is not None:
                image_tag.set("width", str(image["width"]))

            if image["height"] is not None:
                image_tag.set("height", str(image["height"]))

            if image["scale_factor"] is not None:
                image_tag.set("scale", str(image["scale_factor"]))

            image_tag.text = image["url"]

        return screenshot_tag

    def _write_releases(self, root_tag: etree.Element) -> None:
        releases_tag = etree.SubElement(root_tag, "releases")
        if self.internal_releases_radio_button.isChecked():
            self._releases_widget.write_tag(releases_tag)
            if len(releases_tag.getchildren()) == 0:
                root_tag.remove(releases_tag)
        else:
            releases_tag.set("type", "external")
            if (url := self.external_releases_url_edit.text().strip()) != "":
                releases_tag.set("url", url)

    def _write_requires_recommends_supports_tags(self, root_tag: etree._Element, current_type: str) -> None:
        current_tag = etree.SubElement(root_tag, current_type)
        for i in self._control_type_list:
            if getattr(self, "control_box_" + i).currentData() == current_type:
                control_tag = etree.SubElement(current_tag, "control")
                control_tag.text = i.replace("_", "-")  # For tv-remote - is in a object name not supportet
        self._relations_widget.get_save_data(current_tag, current_type)
        if len(current_tag.getchildren()) == 0:
            root_tag.remove(current_tag)

    def get_xml_text(self) -> str:
        root = etree.Element("component")
        root.set("type", self.component_type_box.currentData()[0])

        if self.end_of_life_check_box.isChecked():
            root.set("date_eol", self.end_of_life_date_edit.date().toString(Qt.DateFormat.ISODate))

        if self._env.settings.get("addCommentSave"):
            root.append(etree.Comment("Created with jdAppStreamEdit " + self._env.version))

        id_tag = etree.SubElement(root, "id")
        id_tag.text = self.id_edit.text().strip()

        name_tag = etree.SubElement(root, "name")
        name_tag.text = self.name_edit.text().strip()
        for key, value in self._name_translations.items():
            name_translation_tag = etree.SubElement(root, "name")
            name_translation_tag.set("{http://www.w3.org/XML/1998/namespace}lang", key)
            name_translation_tag.text = value

        summary_tag = etree.SubElement(root, "summary")
        summary_tag.text = self.summary_edit.text().strip()
        for key, value in self._summary_translations.items():
            summary_translation_tag = etree.SubElement(root, "summary")
            summary_translation_tag.set("{http://www.w3.org/XML/1998/namespace}lang", key)
            summary_translation_tag.text = value

        developer_tag = etree.SubElement(root, "developer")
        if (developer_id := self.developer_id_edit.text()) != "":
            developer_tag.set("id", developer_id)
        developer_name_tag = etree.SubElement(developer_tag, "name")
        developer_name_tag.text = self.developer_name_edit.text().strip()
        for key, value in self._developer_name_translations.items():
            developer_name_tag = etree.SubElement(developer_tag, "name")
            developer_name_tag.set("{http://www.w3.org/XML/1998/namespace}lang", key)
            developer_name_tag.text = value

        if self.metadata_license_box.currentData() != "unknown":
            metadata_license_tag = etree.SubElement(root, "metadata_license")
            metadata_license_tag.text = self.metadata_license_box.currentData()

        if self.project_license_box.currentData() != "unknown":
            project_license_tag = etree.SubElement(root, "project_license")
            project_license_tag.text = self.project_license_box.currentData()

        if self.update_contact_edit.text() != "":
            update_contact_tag = etree.SubElement(root, "update_contact")
            update_contact_tag.text = self.update_contact_edit.text().strip()

        if self.project_group_edit.text() != "":
            project_group_tag = etree.SubElement(root, "project_group")
            project_group_tag.text = self.project_group_edit.text().strip()

        description_tag = etree.SubElement(root, "description")
        self._description_widget.get_tags(description_tag)

        if len(self.screenshot_list) > 0:
            screenshots_tag = etree.SubElement(root, "screenshots")
            for i in self.screenshot_list:
                screenshots_tag.append(self._get_screenshot_tag(i))

        self._write_releases(root)

        for i in self._url_list:
            url = getattr(self, f"{i}_url_edit").text()
            if url == "":
                continue
            url_tag = etree.SubElement(root, "url")
            url_tag.set("type", i.replace("_", "-"))
            url_tag.text = url

        if self.categorie_list.count() > 0:
            categories_tag = etree.SubElement(root, "categories")
            for i in range(self.categorie_list.count()):
                single_categorie_tag = etree.SubElement(categories_tag, "category")
                single_categorie_tag.text = self.categorie_list.item(i).text()

        self._write_requires_recommends_supports_tags(root, "requires")
        self._write_requires_recommends_supports_tags(root, "recommends")
        self._write_requires_recommends_supports_tags(root, "supports")

        content_rating_tag = etree.SubElement(root, "content_rating")
        content_rating_tag.set("type", "oars-1.1")
        self._oars_widget.save_file(content_rating_tag)

        for i in get_logical_table_row_list(self.launchable_table):
            launchable_tag = etree.SubElement(root, "launchable")
            launchable_tag.set("type", self.launchable_table.cellWidget(i, 0).currentData())
            launchable_tag.text = self.launchable_table.item(i, 1).text()

        if self.provides_table.rowCount() > 0:
            provides_tag = etree.SubElement(root, "provides")
            for i in get_logical_table_row_list(self.provides_table):
                provides_type = self.provides_table.cellWidget(i, 0).currentData()
                if provides_type == "dbus-user":
                    single_provides_tag = etree.SubElement(provides_tag, "dbus")
                    single_provides_tag.set("type", "user")
                elif provides_type == "dbus-system":
                    single_provides_tag = etree.SubElement(provides_tag, "dbus")
                    single_provides_tag.set("type", "system")
                else:
                    single_provides_tag = etree.SubElement(provides_tag, provides_type)
                single_provides_tag.text = self.provides_table.item(i, 1).text()

        if self.keyword_list.count() > 0:
            keywords_tag = etree.SubElement(root, "keywords")
            for i in range(self.keyword_list.count()):
                single_keyword_tag = etree.SubElement(keywords_tag, "keyword")
                single_keyword_tag.text = self.keyword_list.item(i).text().strip()

        self._advanced_widget.save_data(root)

        save_settings = get_save_settings(self._current_path, self._env.settings)
        etree.indent(root, space=save_settings["ident"])

        xml = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8").decode("utf-8")

        # lxml filters the tags from the description text, so we need to convert them back
        xml = xml.replace("&lt;code&gt;", "<code>")
        xml = xml.replace("&lt;/code&gt;", "</code>")
        xml = xml.replace("&lt;em&gt;", "<em>")
        xml = xml.replace("&lt;/em&gt;", "</em>")

        return xml

    def save_file(self, path: str) -> None:
        try:
            os.makedirs(os.path.dirname(path))
        except Exception:
            pass

        with open(path, "w", encoding="utf-8", newline='\n') as f:
            f.write(self.get_xml_text())

    def _previev_appstream_file(self, command: List[str]) -> None:
        if self.get_id() == "":
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "No ID"), QCoreApplication.translate("MainWindow", "You need to set a ID to use this feature"))
            return

        preview_dir = os.path.join(get_shared_temp_dir(), "preview")
        try:
            os.makedirs(preview_dir)
        except Exception:
            pass

        file_path = os.path.join(preview_dir, self.get_id() + ".metainfo.xml")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.get_xml_text())

        try:
            if is_flatpak():
                subprocess.check_call(["flatpak-spawn", "--host"] + command + [file_path])
            else:
                subprocess.Popen(command + [file_path])
        except Exception:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "{{binary}} not found").replace("{{binary}}", command[0]), QCoreApplication.translate("MainWindow", "{{binary}} was not found. Make sure it is installed and in PATH.").replace("{{binary}}", command[0]))

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        try:
            url = event.mimeData().urls()[0]
        except IndexError:
            return

        if not self._ask_for_save():
            return

        if url.isLocalFile():
            path = url.toLocalFile()
            if self.open_file(path):
                self.add_to_recent_files(path)
        else:
            self.open_url(url.toString())

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._ask_for_save():
            try:
                shutil.rmtree(get_shared_temp_dir())
            except Exception:
                pass
            event.accept()
        else:
            event.ignore()

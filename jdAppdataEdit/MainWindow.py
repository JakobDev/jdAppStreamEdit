from PyQt6.QtWidgets import QApplication, QCheckBox, QComboBox, QLineEdit, QListWidget, QMainWindow, QMessageBox, QDateEdit, QInputDialog, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QRadioButton, QFileDialog
from .Functions import clear_table_widget, stretch_table_widget_colums_size, list_widget_contains_item, is_url_reachable
from PyQt6.QtCore import Qt, QCoreApplication, QDate
from .ScreenshotWindow import ScreenshotWindow
from .SettingsWindow import SettingsWindow
from .ValidateWindow import ValidateWindow
from .AboutWindow import AboutWindow
from PyQt6.QtGui import QAction
from typing import Optional
from lxml import etree
from PyQt6 import uic
import urllib.parse
import webbrowser
import requests
import sys
import os


class MainWindow(QMainWindow):
    def __init__(self, env):
        super().__init__()
        uic.loadUi(os.path.join(env.program_dir, "MainWindow.ui"), self)

        self._env = env

        self._settings_window = SettingsWindow(env, self)
        self._validate_window = ValidateWindow(env, self)
        self._screenshot_window = ScreenshotWindow(env, self)
        self._about_window = AboutWindow(env)

        self.screenshot_list = []

        self._current_path = None

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

        self._update_recent_files_menu()

        for i in env.license_list["licenses"]:
            self.metadata_license_box.addItem(i["name"], i["licenseId"])
            self.project_license_box.addItem(i["name"], i["licenseId"])

        self.metadata_license_box.model().sort(0, Qt.SortOrder.AscendingOrder)
        self.project_license_box.model().sort(0, Qt.SortOrder.AscendingOrder)

        unknown_text = QCoreApplication.translate("MainWindow", "Unknown")
        self.metadata_license_box.insertItem(0, unknown_text, "unknown")
        self.project_license_box.insertItem(0, unknown_text, "unknown")

        self.metadata_license_box.setCurrentIndex(0)
        self.project_license_box.setCurrentIndex(0)

        stretch_table_widget_colums_size(self.screenshot_table)
        stretch_table_widget_colums_size(self.releases_table)
        stretch_table_widget_colums_size(self.provides_table)

        self._update_categorie_remove_button_enabled()

        self._edited = False

        self.description_edit.textChanged.connect(self._update_description_preview)

        self.screenshot_add_button.clicked.connect(lambda: self._screenshot_window.open_window(None))
        self.check_screenshot_url_button.clicked.connect(self._check_screenshot_urls)

        self.release_add_button.clicked.connect(self._release_add_button_clicked)
        self.release_import_github_button.clicked.connect(self._release_import_github)
        self.release_import_gitlab_button.clicked.connect(self._release_import_gitlab)

        self.check_links_url_button.clicked.connect(self._check_links_url_button_clicked)

        self.categorie_list.itemSelectionChanged.connect(self._update_categorie_remove_button_enabled)
        self.categorie_add_button.clicked.connect(self._add_categorie_button_clicked)

        self.categorie_remove_button.clicked.connect(self._remove_categorie_button_clicked)

        self.provides_add_button.clicked.connect(self._add_provides_row)

        self.new_action.triggered.connect(self._new_menu_action_clicked)
        self.open_action.triggered.connect(self._open_menu_action_clicked)
        self.save_action.triggered.connect(self._save_file_clicked)
        self.save_as_action.triggered.connect(self._save_as_clicked)
        self.exit_action.triggered.connect(self._exit_menu_action_clicked)

        self.settings_action.triggered.connect(self._settings_window.open_window)
        self.validate_action.triggered.connect(self._validate_window.open_window)

        self.documentation_action.triggered.connect(lambda: webbrowser.open("https://www.freedesktop.org/software/appstream/docs"))
        self.about_action.triggered.connect(self._about_window.exec)
        self.about_qt_action.triggered.connect(QApplication.instance().aboutQt)

        self.main_tab_widget.setCurrentIndex(0)
        self.update_window_title()

    def set_file_edited(self):
        self._edited = True
        self.update_window_title()

    def update_window_title(self):
        if self._current_path is None or self._env.settings.get("windowTitleType") == "none":
            self.setWindowTitle("jdAppdataEdit")
            return
        elif self._env.settings.get("windowTitleType") == "filename":
            if self._edited and self._env.settings.get("showEditedTitle"):
                self.setWindowTitle(os.path.basename(self._current_path) + "* -jdAppdataEdit")
            else:
                self.setWindowTitle(os.path.basename(self._current_path) + " -jdAppdataEdit")
        elif self._env.settings.get("windowTitleType") == "filename":
            if self._edited and self._env.settings.get("showEditedTitle"):
                self.setWindowTitle(self._current_path + "* -jdAppdataEdit")
            else:
                self.setWindowTitle(self._current_path + " -jdAppdataEdit")

    def _update_recent_files_menu(self):
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

    def _add_to_recent_files(self, path: str):
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
            return
        answer = QMessageBox.warning(self, QCoreApplication.translate("MainWindow", "Unsaved changes"), QCoreApplication.translate("MainWindow", "You have unsaved changes. Do you want to save now?"), QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Save:
            self._save_file_clicked()
            return True
        elif answer == QMessageBox.StandardButton.Discard:
            return True
        elif answer == QMessageBox.StandardButton.Cancel:
            return False

    def _new_menu_action_clicked(self):
        if not self._ask_for_save():
            return
        self.reset_data()
        self._edited = False
        self.update_window_title()

    def _open_menu_action_clicked(self):
        if not self._ask_for_save():
            return
        path = QFileDialog.getOpenFileName(self)
        if path[0] == "":
            return
        self.open_file(path[0])
        self._add_to_recent_files(path[0])
        self._current_path = path[0]
        self.update_window_title()

    def _open_recent_file(self):
        if not self._ask_for_save():
            return
        action = self.sender()
        if not action:
            return
        self.open_file(action.data())
        self._add_to_recent_files(action.data())
        self._current_path = action.data()
        self.update_window_title()

    def _save_file_clicked(self):
        if self._current_path is None:
            self._save_as_clicked()
            return
        self.save_file(self._current_path)
        self._add_to_recent_files(self._current_path)
        self._edited = False
        self.update_window_title()

    def _save_as_clicked(self):
        path = QFileDialog.getSaveFileName(self)
        if path[0] == "":
            return
        self.save_file(path[0])
        self._current_path = path[0]
        self._add_to_recent_files(path[0])
        self._edited = False
        self.update_window_title()

    def _exit_menu_action_clicked(self):
        if self._ask_for_save():
            sys.exit(0)

    def _clear_recent_files(self):
        self._env.recent_files.clear()
        self._update_recent_files_menu()
        self._env.save_recent_files()

    def _update_description_preview(self):
        text = self.description_edit.toPlainText()
        self.description_preview.setHtml(text)

    def update_sceenshot_table(self):
        clear_table_widget(self.screenshot_table)
        for row, i in enumerate(self.screenshot_list):
            self.screenshot_table.insertRow(row)

            url_item = QTableWidgetItem(i["url"])
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

    def _check_screenshot_urls(self):
        for i in self.screenshot_list:
            if not is_url_reachable(i["url"]):
                QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Invalid URL"), QCoreApplication.translate("MainWindow", "The URL {url} does not work").format(url=i["url"]))
                return
        QMessageBox.information(self, QCoreApplication.translate("MainWindow", "Everything OK"), QCoreApplication.translate("MainWindow", "All URLs are working"))

    def _default_button_clicked(self):
        for count, i in enumerate(self.screenshot_list):
            if self.screenshot_table.cellWidget(count, 1).isChecked():
                i["default"] = True
            else:
                i["default"] = False
        self.set_file_edited()

    def _edit_screenshot_button_clicked(self):
        for i in range(self.screenshot_table.rowCount()):
            if self.screenshot_table.cellWidget(i, 2) == self.sender():
                self._screenshot_window.open_window(i)
                return

    def _remove_screenshot_clicked(self):
        for i in range(self.screenshot_table.rowCount()):
            if self.screenshot_table.cellWidget(i, 3) == self.sender():
                default = self.screenshot_list[i]["default"]
                del self.screenshot_list[i]
                if default and len(self.screenshot_list) != 0:
                    self.screenshot_list[0]["default"] = True
                self.update_sceenshot_table()
                self.set_file_edited()
                return

    def _set_release_row(self, row: int, version: Optional[str] = "", date: Optional[QDate] = None, development: bool = False):
        self.releases_table.setItem(row, 0, QTableWidgetItem(version))

        if date is None:
            self.releases_table.setCellWidget(row, 1, QDateEdit())
        else:
            self.releases_table.setCellWidget(row, 1, QDateEdit(date))

        type_box = QComboBox()
        type_box.addItem(QCoreApplication.translate("MainWindow", "Stable"), "stable")
        type_box.addItem(QCoreApplication.translate("MainWindow", "Development"), "development")
        if development:
            type_box.setCurrentIndex(1)
        self.releases_table.setCellWidget(row, 2, type_box)

        remove_button = QPushButton(QCoreApplication.translate("MainWindow", "Remove"))
        remove_button.clicked.connect(self._release_remove_button_clicked)
        self.releases_table.setCellWidget(row, 3, remove_button)

    def _release_remove_button_clicked(self):
        for i in range(self.releases_table.rowCount()):
            if self.releases_table.cellWidget(i, 3) == self.sender():
                self.releases_table.removeRow(i)
                self.set_file_edited()
                return

    def _release_add_button_clicked(self):
        current_row = self.releases_table.rowCount()
        self.releases_table.insertRow(current_row)
        self._set_release_row(current_row)
        self.set_file_edited()

    def _release_import_github(self):
        repo_url, ok = QInputDialog.getText(self, QCoreApplication.translate("MainWindow", "Enter Repo URL"), QCoreApplication.translate("MainWindow", "Please Enter the URL to the GitHub Repo"))
        if not ok:
            return
        try:
            parsed = urllib.parse.urlparse(repo_url)
            if parsed.netloc != "github.com":
                raise Exception()
            _, owner, repo = parsed.path.split("/")
        except Exception:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Invalid URL"), QCoreApplication.translate("MainWindow", "Could not get the Repo and Owner from the URL"))
            return
        api_data = requests.get(f"https://api.github.com/repos/{owner}/{repo}/releases").json()
        if len(api_data) == 0:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Nothing found"), QCoreApplication.translate("MainWindow", "It looks like this Repo doesn't  have any releases"))
            return
        if self.releases_table.rowCount() > 0:
            ans = QMessageBox.question(self, QCoreApplication.translate("MainWindow", "Overwrite evrything"), QCoreApplication.translate("MainWindow", "If you proceed, all your chnages in the release tab will be overwritten. Continue?"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ans != QMessageBox.StandardButton.Yes:
                return
            clear_table_widget(self.releases_table)
        for count, i in enumerate(api_data):
            self.releases_table.insertRow(count)
            self._set_release_row(count, version = i["tag_name"], date=QDate.fromString(i["published_at"], Qt.DateFormat.ISODate), development=i["prerelease"])
        self.set_file_edited()

    def _release_import_gitlab(self):
        repo_url, ok = QInputDialog.getText(self, QCoreApplication.translate("MainWindow", "Enter Repo URL"), QCoreApplication.translate("MainWindow", "Please Enter the URL to the GitLab Repo"))
        if not ok:
            return
        parsed = urllib.parse.urlparse(repo_url)
        host = parsed.scheme + "://" + parsed.netloc
        try:
            r = requests.get(f"{host}/api/v4/projects/{urllib.parse.quote_plus(parsed.path[1:])}/releases")
            assert r.status_code == 200
        except Exception:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Could not get Data"), QCoreApplication.translate("MainWindow", "Could not get release Data for that Repo. Make sure you have the right URL."))
            return
        if self.releases_table.rowCount() > 0:
            ans = QMessageBox.question(self, QCoreApplication.translate("MainWindow", "Overwrite evrything"), QCoreApplication.translate("MainWindow", "If you proceed, all your chnages in the release tab will be overwritten. Continue?"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ans != QMessageBox.StandardButton.Yes:
                return
            clear_table_widget(self.releases_table)
        for count, i in enumerate(r.json()):
            self.releases_table.insertRow(count)
            self._set_release_row(count, version = i["name"], date=QDate.fromString(i["released_at"], Qt.DateFormat.ISODate))
        self.set_file_edited()

    def _check_links_url_button_clicked(self):
        for i in self._url_list:
            url = getattr(self, f"{i}_url_edit").text()
            if url == "":
                continue
            if not is_url_reachable(url):
                QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Invalid URL"), QCoreApplication.translate("MainWindow", "The URL {url} does not work").format(url=url))
                return
        QMessageBox.information(self, QCoreApplication.translate("MainWindow", "Everything OK"), QCoreApplication.translate("MainWindow", "All URLs are working"))

    def _update_categorie_remove_button_enabled(self):
        if self.categorie_list.currentRow() == -1:
            self.categorie_remove_button.setEnabled(False)
        else:
            self.categorie_remove_button.setEnabled(True)

    def _add_categorie_button_clicked(self):
        categorie, ok = QInputDialog.getItem(self, QCoreApplication.translate("MainWindow", "Add a Categorie"), QCoreApplication.translate("MainWindow", "Please select a Categorie from the list below"), self._env.categories, 0, False)
        if not ok:
            return
        if list_widget_contains_item(self.categorie_list, categorie):
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "Categorie already added"), QCoreApplication.translate("MainWindow", "You can't add the same Categorie twice"))
        else:
            self.categorie_list.addItem(categorie)
            self._update_categorie_remove_button_enabled()
            self.set_file_edited()

    def _remove_categorie_button_clicked(self):
        row = self.categorie_list.currentRow()
        if row == -1:
            return
        self.categorie_list.takeItem(row)
        self._update_categorie_remove_button_enabled()
        self.set_file_edited()

    def _add_provides_row(self, value_type: Optional[str] = None, value: str = ""):
        row = self.provides_table.rowCount()
        self.provides_table.insertRow(row)

        type_box = QComboBox()
        type_box.addItem("mediatype", "mediatype")
        type_box.addItem("library", "library")
        type_box.addItem("binary", "binary")
        type_box.addItem("font", "font")
        type_box.addItem("modalias", "modalias")
        type_box.addItem("firmware", "firmware")
        type_box.addItem("python2", "python2")
        type_box.addItem("python3", "python3")
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

    def _remove_provides_button_clicked(self):
        for i in range(self.provides_table.rowCount()):
            if self.provides_table.cellWidget(i, 2) == self.sender():
                self.provides_table.removeRow(i)
                return

    def get_id(self) -> str:
        return self.id_edit.text()

    def reset_data(self):
        for key, value in vars(self).items():
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
        self.screenshot_list.clear()
        self._update_categorie_remove_button_enabled()

    def _parse_screenshots_tag(self, screenshots_tag: etree._Element):
        for i in screenshots_tag.getchildren():
            new_dict = {}

            if i.get("type") == "default":
                new_dict["default"] = True
            else:
                new_dict["default"] = False

            if len(i.getchildren()) == 0:
                new_dict["type"] = "source"
                new_dict["url"] = i.text
                self.screenshot_list.append(new_dict)
                continue

            image_tag = i.find("image")
            new_dict["type"] = image_tag.get("type")
            new_dict["url"] = image_tag.text

            width = image_tag.get("width")
            if width is not None:
                new_dict["width"] = int(width)
            height = image_tag.get("height")
            if height is not None:
                new_dict["height"] = int(height)

            caption_tag = i.find("caption")
            if caption_tag is not None:
                new_dict["caption"] = caption_tag.text

            self.screenshot_list.append(new_dict)

        self.update_sceenshot_table()

    def open_file(self, path: str):
        if not os.path.isfile(path):
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "File not found"), QCoreApplication.translate("MainWindow", "The file you are trying to open does not exists"))
            return

        try:
            root = etree.parse(path)
        except etree.XMLSyntaxError as ex:
            QMessageBox.critical(self, QCoreApplication.translate("MainWindow", "XML parsing failed"), ex.msg)
            return

        self.reset_data()

        id_tag = root.find("id")
        if id_tag is not None:
            self.id_edit.setText(id_tag.text)

        name_tag = root.find("name")
        if name_tag is not None:
            self.name_edit.setText(name_tag.text)

        summary_tag = root.find("summary")
        if summary_tag is not None:
            self.summary_edit.setText(summary_tag.text)

        developer_name_tag = root.find("developer_name")
        if developer_name_tag is not None:
            self.developer_name_edit.setText(developer_name_tag.text)

        launchable_tag = root.find("launchable")
        if launchable_tag is not None:
            self.desktop_file_edit.setText(launchable_tag.text)

        metadata_license_tag = root.find("metadata_license")
        if metadata_license_tag is not None:
            index = self.metadata_license_box.findData(metadata_license_tag.text)
            if index != -1:
                self.metadata_license_box.setCurrentIndex(index)

        project_license_tag = root.find("project_license")
        if project_license_tag is not None:
            index = self.project_license_box.findData(project_license_tag.text)
            if index != -1:
                self.project_license_box.setCurrentIndex(index)

        description_tag = root.find("description")
        if description_tag is not None:
            description = ""
            for i in description_tag.getchildren():
                description += etree.tostring(i).decode("utf-8")
            self.description_edit.setPlainText(description)

        screenshots_tag = root.find("screenshots")
        if screenshots_tag is not None:
            self._parse_screenshots_tag(screenshots_tag)

        releases_tag = root.find("releases")
        if releases_tag is not None:
            for i in releases_tag.getchildren():
                current_row = self.releases_table.rowCount()
                self.releases_table.insertRow(current_row)
                self._set_release_row(current_row, version=i.get("version"), date=QDate.fromString(i.get("date"), Qt.DateFormat.ISODate), development=(i.get("type") == "development"))

        categories_tag = root.find("categories")
        if categories_tag is not None:
            for i in categories_tag.getchildren():
                self.categorie_list.addItem(i.text)

        for i in root.findall("url"):
            try:
                getattr(self, i.get("type") + "_url_edit").setText(i.text)
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

        provides_tag = root.find("provides")
        if provides_tag is not None:
            for i in provides_tag.getchildren():
                self._add_provides_row(value_type=i.tag, value=i.text)

        self._edited = False

    def _write_requires_recommends_supports_tags(self, root_tag: etree._Element, current_type: str):
        current_tag = etree.SubElement(root_tag, current_type)
        for i in self._control_type_list:
            if getattr(self, "control_box_" + i).currentData() == current_type:
                control_tag = etree.SubElement(current_tag, "control")
                control_tag.text = i.replace("_", "-") # For tv-remote - is in a object name not supportet
        if len(current_tag.getchildren()) == 0:
            root_tag.remove(current_tag)

    def save_file(self, path: str):
        root = etree.Element("component")
        root.set("type", "desktop")

        if self._env.settings.get("addCommentSave"):
            root.append(etree.Comment("Created with jdAppdataEdit " + self._env.version))

        id_tag = etree.SubElement(root, "id")
        id_tag.text = self.id_edit.text()

        name_tag = etree.SubElement(root, "name")
        name_tag.text = self.name_edit.text()

        summary_tag = etree.SubElement(root, "summary")
        summary_tag.text = self.summary_edit.text()

        developer_name_tag = etree.SubElement(root, "developer_name")
        developer_name_tag.text = self.developer_name_edit.text()

        if self.desktop_file_edit.text() != "":
            launchable_tag = etree.SubElement(root, "launchable")
            launchable_tag.set("type", "desktop-id")
            launchable_tag.text = self.desktop_file_edit.text()

        if self.metadata_license_box.currentData() != "unknown":
            metadata_license_tag = etree.SubElement(root, "metadata_license")
            metadata_license_tag.text = self.metadata_license_box.currentData()

        if self.project_license_box.currentData() != "unknown":
            project_license_tag = etree.SubElement(root, "project_license")
            project_license_tag.text = self.project_license_box.currentData()

        description_tag = etree.SubElement(root, "description")
        description = self.description_edit.toPlainText()
        if description.find("<p>") == -1:
            description_tag.text = "<p>" + description + "</p>"
        else:
            description_tag.text = description

        content_rating_tag =  etree.SubElement(root, "content_rating")
        content_rating_tag.set("type", "oars-1.1" )

        if len(self.screenshot_list) > 0:
            screenshots_tag = etree.SubElement(root, "screenshots")
            for i in self.screenshot_list:
                single_screenshot_tag = etree.SubElement(screenshots_tag, "screenshot")
                if i["default"]:
                    single_screenshot_tag.set("type", "default")
                if "caption" in i:
                    caption_tag = etree.SubElement(single_screenshot_tag, "caption")
                    caption_tag.text = i["caption"]
                image_tag = etree.SubElement(single_screenshot_tag, "image")
                image_tag.text = i["url"]
                image_tag.set("type", i["type"])
                if "width" in i:
                    image_tag.set("width", str(i["width"]))
                if "height" in i:
                    image_tag.set("height", str(i["height"]))

        if self.releases_table.rowCount() > 0:
            releases_tag = etree.SubElement(root, "releases")
            for i in range(self.releases_table.rowCount()):
                version = self.releases_table.item(i, 0).text()
                date = self.releases_table.cellWidget(i, 1).date().toString(Qt.DateFormat.ISODate)
                release_type = self.releases_table.cellWidget(i, 2).currentData()
                single_release_tag = etree.SubElement(releases_tag, "release")
                single_release_tag.set("version", version)
                single_release_tag.set("date", date)
                single_release_tag.set("type", release_type)

        for i in self._url_list:
            url = getattr(self, f"{i}_url_edit").text()
            if url == "":
                continue
            url_tag = etree.SubElement(root, "url")
            url_tag.set("type", i)
            url_tag.text = url

        if self.categorie_list.count() > 0:
            categories_tag = etree.SubElement(root, "categories")
            for i in range(self.categorie_list.count()):
                single_categorie_tag = etree.SubElement(categories_tag, "category")
                single_categorie_tag.text = self.categorie_list.item(i).text()

        self._write_requires_recommends_supports_tags(root, "requires")
        self._write_requires_recommends_supports_tags(root, "recommends")
        self._write_requires_recommends_supports_tags(root, "supports")

        if self.provides_table.rowCount() > 0:
            provides_tag = etree.SubElement(root, "provides")
            for i in range(self.provides_table.rowCount()):
                provides_type = self.provides_table.cellWidget(i, 0).currentData()
                single_provides_tag = etree.SubElement(provides_tag, provides_type)
                single_provides_tag.text = self.provides_table.item(i, 1).text()

        xml = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8").decode("utf-8")

        # lxml filters the tags from the description text, so we need to convert them back
        xml = xml.replace("&lt;", "<")
        xml = xml.replace("&gt;", ">")

        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)

    def closeEvent(self, event):
        if self._ask_for_save():
            event.accept()
        else:
            event.ignore()

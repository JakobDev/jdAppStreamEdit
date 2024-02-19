from PyQt6.QtWidgets import QMainWindow, QMessageBox, QCheckBox, QFileDialog, QInputDialog, QApplication
from .ui_compiled.ExternalReleasesWindow import Ui_ExternalReleasesWindow
from PyQt6.QtGui import QAction, QDragEnterEvent, QDropEvent, QCloseEvent
from .Functions import is_url_valid, get_save_settings
from .SettingsWindow import SettingsWindow
from .ReleasesWidget import ReleasesWidget
from typing import Optional, TYPE_CHECKING
from PyQt6.QtCore import QCoreApplication
from .ViewXMLWindow import ViewXMLWindow
from .PluginWindow import PluginWindow
from .AboutWindow import AboutWindow
from lxml import etree
import webbrowser
import requests
import sys
import os
import io


if TYPE_CHECKING:
    from .Environment import Environment


class ExternalReleasesWindow(QMainWindow, Ui_ExternalReleasesWindow):
    def __init__(self, env: "Environment") -> None:
        super().__init__()
        self._env = env

        self.setupUi(self)

        self._releases_widget = ReleasesWidget(env, self)
        self._settings_window = SettingsWindow(env, self)
        self._plugin_window = PluginWindow(env, self)
        self._xml_window = ViewXMLWindow(env, self)
        self._about_window = AboutWindow(env, self)

        self._current_path: Optional[str] = None
        self._edited = False

        self.setCentralWidget(self._releases_widget)

        self._update_recent_files_menu()

        self.new_action.triggered.connect(self._new_menu_action_clicked)
        self.open_action.triggered.connect(self._open_menu_action_clicked)
        self.open_url_action.triggered.connect(self._open_url_clicked)
        self.save_action.triggered.connect(self._save_file_clicked)
        self.save_as_action.triggered.connect(self._save_as_clicked)
        self.exit_action.triggered.connect(self._exit_menu_action_clicked)

        self.settings_action.triggered.connect(self._settings_window.open_window)
        self.plugins_action.triggered.connect(self._open_plugin_settings)

        self.view_xml_action.triggered.connect(self._xml_window.exec)

        self.welcome_dialog_action.triggered.connect(self.show_welcome_dialog)
        self.documentation_action.triggered.connect(lambda: webbrowser.open("https://www.freedesktop.org/software/appstream/docs"))
        self.view_source_action.triggered.connect(lambda: webbrowser.open("https://codeberg.org/JakobDev/jdAppStreamEdit"))
        self.report_bug_action.triggered.connect(lambda: webbrowser.open("https://codeberg.org/JakobDev/jdAppStreamEdit/issues"))
        self.translate_action.triggered.connect(lambda: webbrowser.open("https://translate.codeberg.org/projects/jdAppStreamEdit"))
        self.donate_action.triggered.connect(lambda: webbrowser.open("https://ko-fi.com/jakobdev"))
        self.about_action.triggered.connect(self._about_window.exec)
        self.about_qt_action.triggered.connect(QApplication.instance().aboutQt)

        self.setAcceptDrops(True)

        self.update_window_title()

    def set_file_edited(self) -> None:
        self._edited = True
        self.update_window_title()

    def update_window_title(self) -> None:
        if self._env.settings.get("windowTitleType") == "none":
            title = "jdAppStreamEdit External Releases Editor"
        elif self._current_path is None:
            title = QCoreApplication.translate("ExternalReleasesWindow", "Untitled") + " - jdAppStreamEdit External Releases Editor"
        elif self._env.settings.get("windowTitleType") == "filename":
            title = os.path.basename(self._current_path) + " - jdAppStreamEdit External Releases Editor"
        elif self._env.settings.get("windowTitleType") == "path":
            title = self._current_path + " - jdAppStreamEdit External Releases Editor"
        else:
            title = QCoreApplication.translate("ExternalReleasesWindow", "Error")

        if self._edited and self._env.settings.get("showEditedTitle"):
            self.setWindowTitle("*" + title)
        else:
            self.setWindowTitle(title)

    def _update_recent_files_menu(self) -> None:
        self.recent_files_menu.clear()

        if len(self._env.recent_files_external_releases) == 0:
            empty_action = QAction(QCoreApplication.translate("ExternalReleasesWindow", "No recent files"), self)
            empty_action.setEnabled(False)
            self.recent_files_menu.addAction(empty_action)
            return

        for i in self._env.recent_files_external_releases:
            file_action = QAction(i, self)
            file_action.setData(i)
            file_action.triggered.connect(self._open_recent_file)
            self.recent_files_menu.addAction(file_action)

        self.recent_files_menu.addSeparator()

        clear_action = QAction(QCoreApplication.translate("ExternalReleasesWindow", "Clear"), self)
        clear_action.triggered.connect(self._clear_recent_files)
        self.recent_files_menu.addAction(clear_action)

    def add_to_recent_files(self, path: str) -> None:
        while path in self._env.recent_files_external_releases:
            self._env.recent_files_external_releases.remove(path)
        self._env.recent_files_external_releases.insert(0, path)
        self._env.recent_files_external_releases = self._env.recent_files_external_releases[:self._env.settings.get("recentFilesLength")]
        self._update_recent_files_menu()
        self._env.save_recent_files_external_releases()

    def _clear_recent_files(self) -> None:
        self._env.recent_files_external_releases.clear()
        self._env.save_recent_files_external_releases()
        self._update_recent_files_menu()

    def _ask_for_save(self) -> bool:
        if not self._edited:
            return True
        if not self._env.settings.get("checkSaveBeforeClosing"):
            return True
        answer = QMessageBox.warning(self, QCoreApplication.translate("ExternalReleasesWindow", "Unsaved changes"), QCoreApplication.translate("ExternalReleasesWindow", "You have unsaved changes. Do you want to save now?"), QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Save:
            self._save_file_clicked()
            return True
        elif answer == QMessageBox.StandardButton.Discard:
            return True
        elif answer == QMessageBox.StandardButton.Cancel:
            return False

    def show_welcome_dialog(self) -> None:
        text = "<center>"
        text += QCoreApplication.translate("ExternalReleasesWindow", "Welcome to the jdAppStreamEdit External Releases Editor!") + "<br><br>"
        text += QCoreApplication.translate("ExternalReleasesWindow", "This Editor allows you to create and edit AppStream External Relases file (*.releases.xml)") + "<br><br>"
        text += QCoreApplication.translate("ExternalReleasesWindow", "It is part of jdAppStreamEdit") + "<br><br>"
        text += QCoreApplication.translate("ExternalReleasesWindow", "It is highly recommend to read the the AppStream Documentation before using this Program. You can open it under ?>AppStream documentation.") + "<br><br>"
        text += "</center>"

        check_box = QCheckBox(QCoreApplication.translate("ExternalReleasesWindow", "Show this dialog at startup"))
        check_box.setChecked(self._env.settings.get("showWelcomeDialogExternalReleases"))

        message_box = QMessageBox(self)
        message_box.setWindowTitle(QCoreApplication.translate("ExternalReleasesWindow", "Welcome"))
        message_box.setText(text)
        message_box.setCheckBox(check_box)

        message_box.exec()

        self._env.settings.set("showWelcomeDialogExternalReleases", check_box.isChecked())
        self._env.settings.save(os.path.join(self._env.data_dir, "settings.json"))

    def _new_menu_action_clicked(self) -> None:
        if not self._ask_for_save():
            return
        self._releases_widget.reset_data()
        self._edited = False
        self._current_path = None
        self.update_window_title()

    def _open_menu_action_clicked(self) -> None:
        if not self._ask_for_save():
            return
        filter = QCoreApplication.translate("ExternalReleasesWindow", "AppStream Releases") + " (*.releases.xml);;" + QCoreApplication.translate("ExternalReleasesWindow", "All Files") + " (*)"
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

        url = QInputDialog.getText(self, QCoreApplication.translate("ExternalReleasesWindow", "Enter URL"), QCoreApplication.translate("ExternalReleasesWindow", "Please enter a URL"))[0]

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
        filter = QCoreApplication.translate("ExternalReleasesWindow", "AppStream Releases") + " (*.releases.xml *.releases.xml.in);;" + QCoreApplication.translate("ExternalReleasesWindow", "All Files") + " (*)"
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

    def _open_plugin_settings(self) -> None:
        if len(self._env.plugin_list) == 0:
            QMessageBox.information(self, QCoreApplication.translate("MainWindow", "No Plugins installed"), QCoreApplication.translate("MainWindow", "You have no Plugins installed"))
            return

        self._plugin_window.exec()

    def open_file(self, path: str) -> bool:
        try:
            with open(path, "rb") as f:
                text = f.read()
        except FileNotFoundError:
            QMessageBox.critical(self, QCoreApplication.translate("ExternalReleasesWindow", "File not found"), QCoreApplication.translate("ExternalReleasesWindow", "{{path}} does not exists").replace("{{path}}", path))
            return
        except Exception:
            QMessageBox.critical(self, QCoreApplication.translate("ExternalReleasesWindow", "Error"), QCoreApplication.translate("ExternalReleasesWindow", "An error occurred while trying to open {{path}}").replace("{{path}}", path))
            return

        if self.load_xml(text):
            self._current_path = path
            self.update_window_title()
            return True
        else:
            return False

    def open_url(self, url: str) -> None:
        if not is_url_valid(url):
            QMessageBox.critical(self, QCoreApplication.translate("ExternalReleasesWindow", "Invalid URL"), QCoreApplication.translate("ExternalReleasesWindow", "{{url}} is not a valid http/https URL").replace("{{url}}", url))
            return

        try:
            r = requests.get(url, timeout=10)
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
            QMessageBox.critical(self, QCoreApplication.translate("ExternalReleasesWindow", "Could not connect"), QCoreApplication.translate("ExternalReleasesWindow", "Could not connect to {{url}}").replace("{{url}}", url))
            return
        except Exception:
            QMessageBox.critical(self, QCoreApplication.translate("ExternalReleasesWindow", "Error"), QCoreApplication.translate("ExternalReleasesWindow", "An error occurred while trying to connect to {{url}}").replace("{{url}}", url))
            return

        if self.load_xml(r.content):
            self._current_path = None
            self.update_window_title()

    def load_xml(self, xml_data: bytes) -> bool:
        try:
            root = etree.parse(io.BytesIO(xml_data))
        except etree.XMLSyntaxError as ex:
            QMessageBox.critical(self, QCoreApplication.translate("ExternalReleasesWindow", "XML parsing failed"), ex.msg)
            return False

        releases_tag = root.getroot()

        if releases_tag.tag != "releases":
            QMessageBox.critical(self, QCoreApplication.translate("ExternalReleasesWindow", "No releases tag"), QCoreApplication.translate("ExternalReleasesWindow", "This XML file has no releases tag"))
            return False

        self._releases_widget.reset_data()

        self._releases_widget.load_tag(releases_tag)

        return True

    def get_xml_text(self) -> str:
        root = etree.Element("releases")

        if self._env.settings.get("addCommentSave"):
            root.append(etree.Comment("Created with jdAppStreamEdit " + self._env.version))

        self._releases_widget.write_tag(root)

        save_settings = get_save_settings(self._current_path, self._env.settings)
        etree.indent(root, space=save_settings["ident"])

        xml = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8").decode("utf-8")

        return xml

    def save_file(self, path: str) -> None:
        try:
            os.makedirs(os.path.dirname(path))
        except Exception:
            pass

        with open(path, "w", encoding="utf-8", newline='\n') as f:
            f.write(self.get_xml_text())

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
            event.accept()
        else:
            event.ignore()

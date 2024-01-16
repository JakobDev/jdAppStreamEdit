from .Functions import stretch_table_widget_colums_size, get_sender_table_row, clear_table_widget, get_logical_table_row_list, select_combo_box_data
from PyQt6.QtWidgets import QWidget, QPushButton, QComboBox, QDateEdit, QTableWidgetItem, QMessageBox, QMenu, QInputDialog
from .ui_compiled.ReleasesWidget import Ui_ReleasesWidget
from PyQt6.QtCore import Qt, QCoreApplication, QDate
from typing import Optional, Literal, TYPE_CHECKING
from .ReleasesWindow import ReleasesWindow
from .Interfaces import ChangelogImporter
from PyQt6.QtGui import QAction
from lxml import etree
import traceback
import sys


if TYPE_CHECKING:
    from .Environment import Environment


class _COLUMNS:
    VERSION = 0
    DATE = 1
    TYPE = 2
    EDIT_BUTTON = 3
    REMOVE_BUTTON = 4


class ReleasesWidget(QWidget, Ui_ReleasesWidget):
    def __init__(self, env: "Environment", parent: QWidget) -> None:
        super().__init__()

        self.setupUi(self)

        self._parent = parent
        self._env = env

        self._releases_window = ReleasesWindow(env, self, parent)

        release_importer_menu = QMenu()
        for i in env.release_importer:
            importer_action = QAction(i.get_menu_text(), self)
            importer_action.setData(i.do_import)
            importer_action.triggered.connect(self._release_import_function)
            release_importer_menu.addAction(importer_action)
        release_importer_menu.setFixedWidth(self.import_button.width())
        self.import_button.setMenu(release_importer_menu)
        self.import_button.resizeEvent = lambda event: release_importer_menu.setFixedWidth(self.import_button.width())

        stretch_table_widget_colums_size(self.releases_table)

        self.releases_table.verticalHeader().setSectionsMovable(True)

        self.releases_table.verticalHeader().sectionMoved.connect(self._parent.set_file_edited)
        self.add_button.clicked.connect(self._add_button_clicked)
        self.sort_button.clicked.connect(self._sort_button_clicked)

    def _set_release_row(self, row: int, version: Optional[str] = "", date: Optional[QDate] = None, release_type: Literal["stable", "development", "snapshot"] = "stable", data: Optional[dict] = None) -> None:
        version_item = QTableWidgetItem(version)
        if data:
            version_item.setData(42, data)
        else:
            version_item.setData(42, {})
        self.releases_table.setItem(row, _COLUMNS.VERSION, version_item)

        date_edit = QDateEdit()

        if date is None:
            date_edit.setDate(QDate.currentDate())
        else:
            date_edit.setDate(date)

        date_edit.dateChanged.connect(self._parent.set_file_edited)
        self.releases_table.setCellWidget(row, _COLUMNS.DATE, date_edit)

        type_box = QComboBox()
        type_box.addItem(QCoreApplication.translate("ReleasesWidget", "Stable"), "stable")
        type_box.addItem(QCoreApplication.translate("ReleasesWidget", "Development"), "development")
        type_box.addItem(QCoreApplication.translate("ReleasesWidget", "Snapshot"), "snapshot")
        select_combo_box_data(type_box, release_type)
        type_box.currentIndexChanged.connect(self._parent.set_file_edited)
        self.releases_table.setCellWidget(row, _COLUMNS.TYPE, type_box)

        edit_button = QPushButton(QCoreApplication.translate("ReleasesWidget", "Edit"))
        edit_button.clicked.connect(self._edit_button_clicked)
        self.releases_table.setCellWidget(row, _COLUMNS.EDIT_BUTTON, edit_button)

        remove_button = QPushButton(QCoreApplication.translate("ReleasesWidget", "Remove"))
        remove_button.clicked.connect(self._remove_button_clicked)
        self.releases_table.setCellWidget(row, _COLUMNS.REMOVE_BUTTON, remove_button)

    def _edit_button_clicked(self) -> None:
        row = get_sender_table_row(self.releases_table, _COLUMNS.EDIT_BUTTON, self.sender())
        self._releases_window.open_window(row)

    def _remove_button_clicked(self) -> None:
        row = get_sender_table_row(self.releases_table, _COLUMNS.REMOVE_BUTTON, self.sender())
        self.releases_table.removeRow(row)
        self._parent.set_file_edited()

    def _add_button_clicked(self) -> None:
        self.releases_table.insertRow(0)
        self._set_release_row(0)
        self._parent.set_file_edited()

    def _sort_button_clicked(self) -> None:
        try:
            import packaging.version
        except ModuleNotFoundError:
            QMessageBox.critical(self, QCoreApplication.translate("ReleasesWidget", "packaging not found"), QCoreApplication.translate("ReleasesWidget", "This function needs the packaging python module to work"))
            return

        version_list = []
        row_dict = {}

        for row in range(self.releases_table.rowCount()):
            version_string = self.releases_table.item(row, 0).text().strip()

            if version_string == "":
                continue

            try:
                version = packaging.version.Version(version_string)
            except packaging.version.InvalidVersion:
                QMessageBox.critical(self, QCoreApplication.translate("ReleasesWidget", "Could not parse version"), QCoreApplication.translate("ReleasesWidget", "Could not parse version {{version}}").replace("{{version}}", version_string))
                return

            row_dict[version] = {"date": self.releases_table.cellWidget(row, 1).date(), "type": self.releases_table.cellWidget(row, 2).currentData() == "development", "data": self.releases_table.item(row, 0).data(42)}
            version_list.append(version)

        clear_table_widget(self.releases_table)

        version_list.sort(reverse=True)

        for row, version in enumerate(version_list):
            self.releases_table.insertRow(row)
            self._set_release_row(row, version=str(version), date=row_dict[version]["date"], release_type=row_dict[version]["type"], data=row_dict[version]["data"])

        self._parent.set_file_edited()

    def _release_import_function(self) -> None:
        action = self.sender()

        if not action:
            return

        try:
            release_data = action.data()(self)
        except Exception:
            print(traceback.format_exc(), end="", file=sys.stderr)

            msg_box = QMessageBox()
            msg_box.setWindowTitle(QCoreApplication.translate("ReleasesWidget", "Error"))
            msg_box.setText(QCoreApplication.translate("ReleasesWidget", "An Error happened during Import"))
            msg_box.setDetailedText(traceback.format_exc())
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.exec()

            return

        if release_data is None or len(release_data["releases"]) == 0:
            return

        changelog_importer: Optional[ChangelogImporter] = None
        if release_data.get("changelog_importer") is True:
            changelog_importer_list: list[str] = []
            changelog_importer_dict: dict[str, ChangelogImporter] = {}

            changelog_importer_list.append(QCoreApplication.translate("ReleasesWidget", "None"))
            for current_importer in self._env.changelog_importer:
                changelog_importer_list.append(current_importer.get_name())
                changelog_importer_dict[current_importer.get_name()] = current_importer

            changelog_importer_name, ok = QInputDialog.getItem(self, QCoreApplication.translate("ReleasesWidget", "Import Changelog"), QCoreApplication.translate("ReleasesWidget", "jdAppStreamEdit can import the changelog if it adheres to a specific format. If this is the case, please choose the appropriate format."), changelog_importer_list, editable=False)
            if ok and changelog_importer_name in changelog_importer_dict:
                changelog_importer = changelog_importer_dict[changelog_importer_name]

        if self.releases_table.rowCount() > 0:
            ans = QMessageBox.question(self, QCoreApplication.translate("ReleasesWidget", "Overwrite everything"), QCoreApplication.translate("ReleasesWidget", "If you proceed, all your chnages in the release tab will be overwritten. Continue?"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ans != QMessageBox.StandardButton.Yes:
                return

        clear_table_widget(self.releases_table)

        for count, i in enumerate(release_data["releases"]):
            changelog_text = i.get("changelog_text", "")
            if changelog_importer is not None and changelog_text is not None and changelog_text != "":
                try:
                    changelog, _ = changelog_importer.do_import(changelog_text)

                    if changelog is not None:
                        if "data" not in i:
                            i["data"] = {}
                        i["data"]["description"] = changelog
                except Exception:
                    print(traceback.format_exc(), end="", file=sys.stderr)

            self.releases_table.insertRow(count)
            try:
                self._set_release_row(count, version=i["version"], date=i["date"], release_type=i.get("type", "stable"), data=i.get("data", {}))
            except Exception:
                print(traceback.format_exc(), end="", file=sys.stderr)

                msg_box = QMessageBox()
                msg_box.setWindowTitle(QCoreApplication.translate("ReleasesWidget", "Error"))
                msg_box.setText(QCoreApplication.translate("ReleasesWidget", "An Error happened during Import"))
                msg_box.setDetailedText(traceback.format_exc())
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.exec()

                return

        self._parent.set_file_edited()

    def reset_data(self) -> None:
        clear_table_widget(self.releases_table)

    def load_tag(self, releases_tag: etree._Element) -> None:
        for i in releases_tag.getchildren():
            current_row = self.releases_table.rowCount()
            data = {}

            if i.get("urgency") is not None:
                data["urgency"] = i.get("urgency")

            url_tag = i.find("url")
            if url_tag is not None:
                data["url"] = url_tag.text

            description_tag = i.find("description")
            if description_tag is not None:
                data["description"] = description_tag

            artifacts_tag = i.find("artifacts")
            if artifacts_tag is not None:
                data["artifacts"] = artifacts_tag

            self.releases_table.insertRow(current_row)
            self._set_release_row(current_row, version=i.get("version"), date=QDate.fromString(i.get("date"), Qt.DateFormat.ISODate), release_type=(i.get("type", "stable")), data=data)

    def write_tag(self, releases_tag: etree.Element) -> None:
        for i in get_logical_table_row_list(self.releases_table):
            version = self.releases_table.item(i, _COLUMNS.VERSION).text().strip()
            date = self.releases_table.cellWidget(i, _COLUMNS.DATE).date().toString(Qt.DateFormat.ISODate)
            release_type = self.releases_table.cellWidget(i, _COLUMNS.TYPE).currentData()
            single_release_tag = etree.SubElement(releases_tag, "release")
            single_release_tag.set("version", version)
            single_release_tag.set("date", date)
            single_release_tag.set("type", release_type)

            data = self.releases_table.item(i, _COLUMNS.VERSION).data(42)

            if "urgency" in data:
                single_release_tag.set("urgency", data["urgency"])

            if "url" in data:
                url_tag = etree.SubElement(single_release_tag, "url")
                url_tag.text = data["url"]

            if "description" in data:
                single_release_tag.append(data["description"])

            if "artifacts" in data:
                single_release_tag.append(data["artifacts"])

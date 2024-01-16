from .Functions import get_logical_table_row_list, clear_table_widget, stretch_table_widget_colums_size, select_combo_box_data, get_sender_table_row
from PyQt6.QtWidgets import QDialog, QWidget, QPushButton, QTableWidgetItem, QStyle
from .ui_compiled.ReleasesWindow import Ui_ReleasesWindow
from .ImportChangelogWindow import ImportChangelogWindow
from .DescriptionWidget import DescriptionWidget
from PyQt6.QtCore import QCoreApplication, Qt
from .ArtifactWindow import ArtifactWindow
from .Types import ReleaseInfoDict
from typing import TYPE_CHECKING
from PyQt6.QtGui import QIcon
from lxml import etree
import sys


if TYPE_CHECKING:
    from .ReleasesWidget import ReleasesWidget
    from .Environment import Environment


class ReleasesWindow(QDialog, Ui_ReleasesWindow):
    def __init__(self, env: "Environment", releases_widget: "ReleasesWidget", parent_window: QWidget) -> None:
        super().__init__(parent_window)

        self.setupUi(self)

        self._import_changelog_window = ImportChangelogWindow(env, self)
        self._releases_widget = releases_widget
        self._parent_window = parent_window

        self._description_widget = DescriptionWidget(env)
        self.description_layout.insertWidget(0, self._description_widget)

        self._artifacts_window = ArtifactWindow(env, self)

        self.urgency_box.addItem(QCoreApplication.translate("ReleasesWindow", "Not specified"), "none")
        self.urgency_box.addItem(QCoreApplication.translate("ReleasesWindow", "Low"), "low")
        self.urgency_box.addItem(QCoreApplication.translate("ReleasesWindow", "Medium"), "medium")
        self.urgency_box.addItem(QCoreApplication.translate("ReleasesWindow", "High"), "high")
        self.urgency_box.addItem(QCoreApplication.translate("ReleasesWindow", "Critical"), "critical")

        stretch_table_widget_colums_size(self.artifacts_table)
        self.artifacts_table.verticalHeader().setSectionsMovable(True)

        self.ok_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogOkButton)))
        self.cancel_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)))

        self.import_changelog_button.clicked.connect(self._import_changelog_button_clicked)
        self.add_artifact_button.clicked.connect(lambda: self._artifacts_window.open_window(None))
        self.ok_button.clicked.connect(self._ok_button_clicked)
        self.cancel_button.clicked.connect(self.close)

    def _import_changelog_button_clicked(self) -> None:
        changelog_tag = self._import_changelog_window.get_changelog()

        if changelog_tag is not None:
            self._description_widget.load_tags(changelog_tag)

    def _edit_artifact_clicked(self) -> None:
        row = get_sender_table_row(self.artifacts_table, 1, self.sender())
        self._artifacts_window.open_window(row)

    def _remove_artifact_clicked(self) -> None:
        row = get_sender_table_row(self.artifacts_table, 2, self.sender())
        self.artifacts_table.removeRow(row)

    def _ok_button_clicked(self) -> None:
        new_dict: ReleaseInfoDict = {}

        if self.url_edit.text() != "":
            new_dict["url"] = self.url_edit.text()

        if self.urgency_box.currentData() != "none":
            new_dict["urgency"] = self.urgency_box.currentData()

        description_tag = etree.Element("description")
        self._description_widget.get_tags(description_tag)
        if len(description_tag.getchildren()) > 0:
            new_dict["description"] = description_tag

        if self.artifacts_table.rowCount() > 0:
            artifacts_tag = etree.Element("artifacts")
            for i in get_logical_table_row_list(self.artifacts_table):
                artifacts_tag.append(self.artifacts_table.item(i, 0).data(42))
            new_dict["artifacts"] = artifacts_tag

        self._releases_widget.releases_table.item(self._position, 0).setData(42, new_dict)

        self._parent_window.set_file_edited()

        self.close()

    def add_artifacts_row(self, row: int) -> None:
        self.artifacts_table.insertRow(row)

        edit_button = QPushButton(QCoreApplication.translate("ReleasesWindow", "Edit"))
        edit_button.clicked.connect(self._edit_artifact_clicked)
        self.artifacts_table.setCellWidget(row, 1, edit_button)

        remove_button = QPushButton(QCoreApplication.translate("ReleasesWindow", "Remove"))
        remove_button.clicked.connect(self._remove_artifact_clicked)
        self.artifacts_table.setCellWidget(row, 2, remove_button)

    def open_window(self, position: int) -> None:
        self._position = position

        data = self._releases_widget.releases_table.item(self._position, 0).data(42)

        if "url" in data:
            self.url_edit.setText(data["url"])
        else:
            self.url_edit.setText("")

        if "urgency" in data:
            select_combo_box_data(self.urgency_box, data["urgency"])
        else:
            self.urgency_box.setCurrentIndex(0)

        self._description_widget.reset_data()
        if "description" in data:
            self._description_widget.load_tags(data["description"])

        clear_table_widget(self.artifacts_table)
        if "artifacts" in data:
            for i in data["artifacts"].findall("artifact"):
                location_tag = i.find("location")
                if location_tag is None:
                    print("artifact has no location tag", file=sys.stderr)
                    continue

                row = self.artifacts_table.rowCount()
                self.add_artifacts_row(row)

                location_item = QTableWidgetItem(location_tag.text)
                location_item.setFlags(location_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                location_item.setData(42, i)
                self.artifacts_table.setItem(row, 0, location_item)

        self.main_tab_widget.setCurrentIndex(0)

        self.setWindowTitle(QCoreApplication.translate("ReleasesWindow", "Edit release {{release}}").replace("{{release}}", self._releases_widget.releases_table.item(self._position, 0).text()))

        self.open()

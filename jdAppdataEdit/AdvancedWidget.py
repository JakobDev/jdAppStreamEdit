from .Functions import stretch_table_widget_colums_size, select_combo_box_data, get_logical_table_row_list, clear_table_widget, list_widget_contains_item, get_sender_table_row
from PyQt6.QtWidgets import QWidget, QComboBox, QTableWidgetItem, QInputDialog, QMessageBox, QPushButton
from PyQt6.QtCore import QCoreApplication
from typing import Optional
from lxml import etree
from PyQt6 import uic
import os


class AdvancedWidget(QWidget):
    def __init__(self, env, main_window):
        super().__init__()
        uic.loadUi(os.path.join(env.program_dir, "AdvancedWidget.ui"), self)

        self._main_window = main_window

        stretch_table_widget_colums_size(self.translation_table)
        stretch_table_widget_colums_size(self.tags_table)
        stretch_table_widget_colums_size(self.custom_table)

        self.translation_table.verticalHeader().setSectionsMovable(True)
        self.tags_table.verticalHeader().setSectionsMovable(True)
        self.custom_table.verticalHeader().setSectionsMovable(True)

        self._update_suggests_edit_remove_button()

        self.translation_table.verticalHeader().sectionMoved.connect(main_window.set_file_edited)
        self.translation_add_button.clicked.connect(lambda: self._add_translation_row())

        self.suggests_add_button.clicked.connect(self._add_suggests_clicked)
        self.suggests_edit_button.clicked.connect(self._edit_suggests_clicked)
        self.suggests_remove_button.clicked.connect(self._remove_suggests_clicked)
        self.suggests_list.itemSelectionChanged.connect(self._update_suggests_edit_remove_button)

        self.tags_table.verticalHeader().sectionMoved.connect(main_window.set_file_edited)
        self.tags_add_button.clicked.connect(lambda: self._add_tags_row())

        self.custom_table.verticalHeader().sectionMoved.connect(main_window.set_file_edited)
        self.custom_add_button.clicked.connect(lambda: self._add_custom_row())

        self.tab_widget.setCurrentIndex(0)

    # Translation

    def _add_translation_row(self, translation_type: Optional[str] = None, domain: Optional[str] = None):
        row = self.translation_table.rowCount()
        self.translation_table.insertRow(row)

        type_box = QComboBox()
        type_box.addItem("gettext", "gettext")
        type_box.addItem("qt", "qt")
        type_box.currentIndexChanged.connect(self._main_window.set_file_edited)
        if  translation_type is not None:
            select_combo_box_data(type_box, translation_type)
        self.translation_table.setCellWidget(row, 0, type_box)

        domain_item = QTableWidgetItem()
        if domain is not None:
            domain_item.setText(domain)
        self.translation_table.setItem(row, 1, domain_item)

        remove_button = QPushButton(QCoreApplication.translate("AdvancedWidget", "Remove"))
        remove_button.clicked.connect(self._remove_translation_clicked)
        self.translation_table.setCellWidget(row, 2, remove_button)

        self._main_window.set_file_edited()

    def _remove_translation_clicked(self):
        row = get_sender_table_row(self.translation_table, 2, self.sender())
        self.translation_table.removeRow(row)
        self._main_window.set_file_edited()

    # Suggests

    def _add_suggests_clicked(self):
        text = QInputDialog.getText(self, QCoreApplication.translate("AdvancedWidget", "New Suggestion"), QCoreApplication.translate("AdvancedWidget", "Please enter a new ID"))[0]
        if text == "":
            return
        if list_widget_contains_item(self.suggests_list, text):
            QMessageBox.critical(self, QCoreApplication.translate("AdvancedWidget", "ID in List"), QCoreApplication.translate("AdvancedWidget", "This ID is already in the List"))
            return
        self.suggests_list.addItem(text)
        self._update_suggests_edit_remove_button()
        self._main_window.set_file_edited()

    def _edit_suggests_clicked(self):
        if self.suggests_list.currentRow() == -1:
            return
        old_text = self.suggests_list.currentItem().text()
        new_text, ok = QInputDialog.getText(self, QCoreApplication.translate("AdvancedWidget", "Edit Suggestion"), QCoreApplication.translate("AdvancedWidget", "Please edit the ID"), text=old_text)
        if not ok or old_text == new_text:
            return
        if list_widget_contains_item(self.suggests_list, new_text):
            QMessageBox.critical(self, QCoreApplication.translate("AdvancedWidget", "ID in List"), QCoreApplication.translate("AdvancedWidget", "This ID is already in the List"))
            return
        self.suggests_list.currentItem().setText(new_text)
        self._main_window.set_file_edited()

    def _remove_suggests_clicked(self):
        index = self.suggests_list.currentRow()
        if index != -1:
            self.suggests_list.takeItem(index)
            self._update_suggests_edit_remove_button()
            self._main_window.set_file_edited()

    def _update_suggests_edit_remove_button(self):
        if self.suggests_list.currentRow() == -1:
            self.suggests_edit_button.setEnabled(False)
            self.suggests_remove_button.setEnabled(False)
        else:
            self.suggests_edit_button.setEnabled(True)
            self.suggests_remove_button.setEnabled(True)

    # Tags

    def _add_tags_row(self, namespace: Optional[str] = None, value: Optional[str] = None):
        row = self.tags_table.rowCount()
        self.tags_table.insertRow(row)

        namespace_item = QTableWidgetItem()
        if namespace is not None:
            namespace_item.setText(namespace)
        self.tags_table.setItem(row, 0, namespace_item)

        value_item = QTableWidgetItem()
        if value is not None:
            value_item.setText(value)
        self.tags_table.setItem(row, 1, value_item)

        remove_button = QPushButton(QCoreApplication.translate("AdvancedWidget", "Remove"))
        remove_button.clicked.connect(self._remove_tags_clicked)
        self.tags_table.setCellWidget(row, 2, remove_button)

        self._main_window.set_file_edited()

    def _remove_tags_clicked(self):
        row = get_sender_table_row(self.tags_table, 2, self.sender())
        self.tags_table.removeRow(row)
        self._main_window.set_file_edited()

    # Tags

    def _add_custom_row(self, key: Optional[str] = None, value: Optional[str] = None):
        row = self.custom_table.rowCount()
        self.custom_table.insertRow(row)

        key_item = QTableWidgetItem()
        if key is not None:
            key_item.setText(key)
        self.custom_table.setItem(row, 0, key_item)

        value_item = QTableWidgetItem()
        if value is not None:
            value_item.setText(value)
        self.custom_table.setItem(row, 1, value_item)

        remove_button = QPushButton(QCoreApplication.translate("AdvancedWidget", "Remove"))
        remove_button.clicked.connect(self._remove_custom_clicked)
        self.custom_table.setCellWidget(row, 2, remove_button)

        self._main_window.set_file_edited()

    def _remove_custom_clicked(self):
        row = get_sender_table_row(self.custom_table, 2, self.sender())
        self.custom_table.removeRow(row)
        self._main_window.set_file_edited()

    # Other

    def reset_data(self):
        clear_table_widget(self.translation_table)
        self.suggests_list.clear()
        clear_table_widget(self.tags_table)
        clear_table_widget(self.custom_table)

        self._update_suggests_edit_remove_button

    def load_data(self, root_tag: etree._Element):
        for i in root_tag.findall("translation"):
            self._add_translation_row(translation_type=i.get("type"), domain=i.text)

        suggests_tag = root_tag.find("suggests")
        if suggests_tag is not None:
            for i in suggests_tag.findall("id"):
                self.suggests_list.addItem(i.text)

        tags_tag = root_tag.find("tags")
        if tags_tag is not None:
            for i in tags_tag.findall("tag"):
                self._add_tags_row(namespace=i.get("namespace"), value=i.text)

        custom_tag = root_tag.find("custom")
        if custom_tag is not None:
            for i in custom_tag.findall("value"):
                self._add_custom_row(key=i.get("key"), value=i.text)

    def save_data(self, root_tag: etree.Element) -> None:
        for i in get_logical_table_row_list(self.translation_table):
            translation_tag = etree.SubElement(root_tag, "translation")
            translation_tag.set("type", self.translation_table.cellWidget(i, 0).currentData())
            translation_tag.text = self.translation_table.item(i, 1).text()

        if self.suggests_list.count() > 0:
            suggests_tag = etree.SubElement(root_tag, "suggests")
            for i in range(self.suggests_list.count()):
                id_tag = etree.SubElement(suggests_tag, "id")
                id_tag.text = self.suggests_list.item(i).text()

        if self.tags_table.rowCount() > 0:
            tags_tag = etree.SubElement(root_tag, "tags")
            for i in get_logical_table_row_list(self.tags_table):
                tag_tag = etree.SubElement(tags_tag, "tag")
                tag_tag.set("namespace", self.tags_table.item(i, 0).text())
                tag_tag.text = self.tags_table.item(i, 1).text()

        if self.custom_table.rowCount() > 0:
            custom_tag = etree.SubElement(root_tag, "custom")
            for i in get_logical_table_row_list(self.custom_table):
                value_tag = etree.SubElement(custom_tag, "value")
                value_tag.set("key", self.custom_table.item(i, 0).text())
                value_tag.text = self.custom_table.item(i, 1).text()

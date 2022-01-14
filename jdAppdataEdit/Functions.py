from PyQt6.QtWidgets import QTableWidget, QHeaderView, QListWidget, QComboBox
from typing import List, Any
import urllib.parse
import requests


def clear_table_widget(table: QTableWidget):
    """Removes all Rows from a QTableWidget"""
    while table.rowCount() > 0:
        table.removeRow(0)


def stretch_table_widget_colums_size(table: QTableWidget):
    """Stretch all Colums of a QTableWidget"""
    for i in range(table.columnCount()):
        table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)


def list_widget_contains_item(list_widget: QListWidget, text: str) -> bool:
    """Checks if a QListWidget contains a item with the given text"""
    for i in range(list_widget.count()):
        if list_widget.item(i).text() == text:
            return True
    return False


def is_url_valid(url: str) -> bool:
    """Checks if the given URL with http/https protocol is valid"""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "http" and parsed.scheme != "https":
        return False
    if parsed.netloc == "":
        return False
    return True


def is_url_reachable(url: str) -> bool:
    """Checks if a URL exists"""
    try:
        r = requests.get(url, stream=True)
        return r.status_code == 200
    except Exception:
        return False


def select_combo_box_data(box: QComboBox, data: Any, default_index: int = 0):
    """Set the index to the item with the given data"""
    index = box.findData(data)
    if index == -1:
        box.setCurrentIndex(default_index)
    else:
        box.setCurrentIndex(index)


def get_logical_table_row_list(table: QTableWidget) -> List[int]:
    """Returns a List of the row indexes in the order they appear in the table"""
    index_list = []
    header = table.verticalHeader()
    for i in range(table.rowCount()):
        index_list.append(header.logicalIndex(i))
    return index_list

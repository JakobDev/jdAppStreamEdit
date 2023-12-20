from PyQt6.QtWidgets import QWidget, QTableWidget, QHeaderView, QListWidget, QComboBox, QLayout, QMessageBox
from typing import Optional, List, Any, TYPE_CHECKING
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtCore import QObject
from lxml import etree
import urllib.parse
import collections
import requests
import tempfile
import hashlib
import shutil
import sys
import os


try:
    import editorconfig
except ModuleNotFoundError:
    print("Optional module editorconfig not found", file=sys.stderr)
    editorconfig = None


if TYPE_CHECKING:
    from .Settings import Settings


def clear_table_widget(table: QTableWidget) -> None:
    """Removes all Rows from a QTableWidget"""
    while table.rowCount() > 0:
        table.removeRow(0)


def stretch_table_widget_colums_size(table: QTableWidget) -> None:
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
        r = requests.head(url, stream=True)
        return r.status_code == 200
    except Exception:
        return False


def select_combo_box_data(box: QComboBox, data: Any, default_index: int = 0) -> None:
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


def calculate_checksum_from_url(url: str, hashtype: str) -> Optional[str]:
    """Returns the checksum of the given hashtype of the given URL. returns None, if the status code is not 200."""
    BUF_SIZE = 65536
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        return None
    hash = getattr(hashlib, hashtype)()
    for chunk in r.iter_content(chunk_size=BUF_SIZE):
        hash.update(chunk)
    return hash.hexdigest()


def create_artifact_source_tag(url: str) -> etree.Element:
    """Creates a artifact tag for the given source URL"""
    atrtifact_tag = etree.Element("artifact")
    atrtifact_tag.set("type", "source")
    location_tag = etree.SubElement(atrtifact_tag, "location")
    location_tag.text = url
    for i in ("sha1", "sha256", "blake2b", "blake2s"):
        checksum_tag = etree.SubElement(atrtifact_tag, "checksum")
        checksum_tag.set("type", i)
        checksum_tag.text = calculate_checksum_from_url(url, i)
    return atrtifact_tag


def is_string_number(text: str) -> bool:
    """Checks if the given string is a number"""
    try:
        int(text)
        return True
    except ValueError:
        return False


def is_flatpak() -> bool:
    return os.path.isfile("/.flatpak-info")


def get_shared_temp_dir() -> str:
    if is_flatpak():
        return os.path.join(os.getenv("XDG_CACHE_HOME"), "jdAppStreamEdit")
    else:
        return os.path.join(tempfile.gettempdir(), "jdAppStreamEdit")


def get_sender_table_row(table: QTableWidget, column: int, sender: QObject) -> int:
    """Get the Row in a QTableWidget that contains the Button that was clicked"""
    for i in range(table.rowCount()):
        if table.cellWidget(i, column) == sender:
            return i


def get_save_settings(path: Optional[str], settings: "Settings") -> dict[str, str]:
    if path is not None and editorconfig is not None and settings.get("useEditorconfig"):
        try:
            config = editorconfig.get_properties(path)
        except editorconfig.EditorConfigError:
            print("Invalid .editorconfig", file=sys.stderr)
            config = collections.OrderedDict
    else:
        config = collections.OrderedDict()

    if "indent_style" not in config:
        if settings.get("useTabsInsteadOfSpaces"):
            config["indent_style"] = "tab"
        else:
            config["indent_style"] = "space"

    if "indent_size" not in config:
        config["indent_size"] = str(settings.get("whitespaceCount"))

    save_settings: dict[str, str] = {}

    if config.get("indent_style") == "tab":
        save_settings["ident"] = "\t"
    else:
        try:
            save_settings["ident"] = " " * int(config.get("indent_size"))
        except ValueError:
            return "  "

    return save_settings


def set_layout_enabled(layout: QLayout, enabled: bool) -> None:
    "Set all widgets in this layout enabled"
    for count in range(layout.count()):
        item = layout.itemAt(count)

        if (widget := item.widget()) is not None:
            widget.setEnabled(enabled)

        if (child_layout := item.layout()) is not None:
            set_layout_enabled(child_layout, enabled)


def assert_func(expression: bool) -> None:
    """
    The assert keyword is not available when running Python in Optimized Mode.
    This function is a drop-in replacement.
    See https://docs.python.org/3/using/cmdline.html?highlight=pythonoptimize#cmdoption-O
    """
    if not expression:
        raise AssertionError()


def check_appstreamcli(parent: Optional[QWidget]) -> bool:
    "Check if appstreamcli is installed"
    if shutil.which("appstreamcli") is not None:
        return True
    else:
        QMessageBox.critical(parent, QCoreApplication.translate("Functions", "appstreamcli not found"), QCoreApplication.translate("Functions", "appstreamcli was not found. Make sure it is installed and in PATH."))
        return False

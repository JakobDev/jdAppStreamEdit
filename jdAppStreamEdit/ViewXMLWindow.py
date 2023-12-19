from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QShowEvent
from PyQt6.QtWidgets import QDialog, QApplication, QStyle
from .ui_compiled.ViewXMLWindow import Ui_ViewXMLWindow
from typing import TYPE_CHECKING
from PyQt6.QtGui import QIcon
import re


if TYPE_CHECKING:
    from .Environment import Environment
    from .MainWindow import MainWindow


class XMLHighlighter(QSyntaxHighlighter):
    '''
    Class for highlighting xml text inherited from QSyntaxHighlighter
    reference:
        http://www.yasinuludag.com/blog/?p=49

    '''
    def __init__(self, parent=None) -> None:

        super(XMLHighlighter, self).__init__(parent)

        self._highlighting_rules = []

        xmlAttributeFormat = QTextCharFormat()
        xmlAttributeFormat.setFontItalic(True)
        xmlAttributeFormat.setForeground(QColor("#177317"))  # green
        self._highlighting_rules.append((re.compile(r"(<(.*?)|\"|\') (.*?)="), xmlAttributeFormat))

        xmlElementFormat = QTextCharFormat()
        xmlElementFormat.setForeground(QColor("#000070"))  # blue
        self._highlighting_rules.append((re.compile("<(.*?)[> ]"), xmlElementFormat))

        single_line_comment_format = QTextCharFormat()
        single_line_comment_format.setForeground(QColor("#a0a0a4"))  # grey
        self._highlighting_rules.append((re.compile("<!--[^\n]*-->"), single_line_comment_format))

        self._value_format = QTextCharFormat()
        self._value_format.setForeground(QColor("#e35e00"))  # orange
        self._value_regex = re.compile(r"(?<=\S=)[\"\'](.*?)[\"\']")

    def highlightBlock(self, text: str) -> None:
        for pattern, format in self._highlighting_rules:
            for i in pattern.finditer(text):
                self.setFormat(i.start(), i.end() - i.start(), format)

        for i in self._value_regex.finditer(text):
            self.setFormat(i.start(), i.end() - i.start(), self._value_format)


class ViewXMLWindow(QDialog, Ui_ViewXMLWindow):
    def __init__(self, env: "Environment", main_window: "MainWindow") -> None:
        super().__init__()

        self.setupUi(self)

        self._main_window = main_window

        self._xml_highlighter = XMLHighlighter(self.preview_edit.document())

        self.close_button.setIcon(QIcon(env.app.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)))

        self.copy_button.clicked.connect(lambda: QApplication.clipboard().setText(self.preview_edit.toPlainText()))
        self.close_button.clicked.connect(self.close)

    def showEvent(self, event: QShowEvent) -> None:
        self.preview_edit.setPlainText(self._main_window.get_xml_text())

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtWidgets import QDialog
from PyQt6 import uic
import re
import os


class XMLHighlighter(QSyntaxHighlighter):
    '''
    Class for highlighting xml text inherited from QSyntaxHighlighter
    reference:
        http://www.yasinuludag.com/blog/?p=49

    '''
    def __init__(self, parent=None):

        super(XMLHighlighter, self).__init__(parent)

        self._highlighting_rules = []

        xmlAttributeFormat = QTextCharFormat()
        xmlAttributeFormat.setFontItalic(True)
        xmlAttributeFormat.setForeground(QColor("#177317")) #green
        self._highlighting_rules.append((re.compile(r"(<(.*?)|\"|\') (.*?)="), xmlAttributeFormat))

        xmlElementFormat = QTextCharFormat()
        xmlElementFormat.setForeground(QColor("#000070")) #blue
        self._highlighting_rules.append((re.compile("<(.*?)[> ]"), xmlElementFormat))

        single_line_comment_format = QTextCharFormat()
        single_line_comment_format.setForeground(QColor("#a0a0a4")) # grey
        self._highlighting_rules.append((re.compile("<!--[^\n]*-->"), single_line_comment_format))

        self._value_format = QTextCharFormat()
        self._value_format.setForeground(QColor("#e35e00")) #orange
        self._value_regex = re.compile(r"[\"\'](.*?)[\"\']")

    def highlightBlock(self, text):
        for pattern, format in self._highlighting_rules:
            for i in pattern.finditer(text):
                self.setFormat(i.start(), i.end() - i.start(), format)

        for i in self._value_regex.finditer(text):
            self.setFormat(i.start(), i.end() - i.start(), self._value_format)


class ViewXMLWindow(QDialog):
    def __init__(self, env, main_window):
        super().__init__()
        uic.loadUi(os.path.join(env.program_dir, "ViewXMLWindow.ui"), self)

        self._main_window = main_window

        self.test = XMLHighlighter(self.preview_edit.document())

    def showEvent(self, event):
        self.preview_edit.setPlainText(self._main_window.get_xml_text())
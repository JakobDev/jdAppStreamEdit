from .Interfaces import ChangelogImporter
from PyQt6.QtCore import QCoreApplication
from typing import Optional
from lxml import etree
import re


def _replace_markdown_inline_code(text: str) -> str:
    for regex_match in re.finditer(r"(?=`)`(?!`)[^`]*(?=`)`(?!`)", text):
        text = text.replace(regex_match.group(), "<code>" + regex_match.group().removeprefix("`").removesuffix("`") + "</code>")
    return text


def _replace_markdown_links(text: str) -> str:
    for regex_match in re.finditer(r"!?\[([^\]]*)\]\(([^\)]+)\)", text):
        link_text = re.search(r"(?<=^\[)[\s|\S]+(?=\]\()", regex_match.group()).group()
        text = text.replace(regex_match.group(), link_text)
    return text


class _PlainTextImporter(ChangelogImporter):
    @staticmethod
    def do_import(text: str) -> tuple[Optional[etree.Element], Optional[str]]:
        root_tag = etree.Element("description")
        paragraph_tag = etree.SubElement(root_tag, "p")
        paragraph_tag.text = text
        return (root_tag, None)

    @staticmethod
    def get_name() -> str:
        return QCoreApplication.translate("ChangelogImporter", "Plain Text")


class _KeepAChanhelogImporter(ChangelogImporter):
    @staticmethod
    def do_import(text: str) -> tuple[Optional[etree.Element], Optional[str]]:
        current_list_tag = None
        root_tag = etree.Element("description")

        for line in text.splitlines():
            if line.startswith("### "):
                paragraph_tag = etree.SubElement(root_tag, "p")
                paragraph_tag.text = line.removeprefix("### ")
                current_list_tag = None
            elif line.startswith("- "):
                if current_list_tag is None:
                    current_list_tag = etree.SubElement(root_tag, "ul")

                entry_tag = etree.SubElement(current_list_tag, "li")
                entry_tag.text = line.removeprefix("- ")
                entry_tag.text = _replace_markdown_inline_code(entry_tag.text)
                entry_tag.text = _replace_markdown_links(entry_tag.text)

        return (root_tag, None)

    @staticmethod
    def get_name() -> str:
        return "Keep A Changelog"


def get_changelog_importer() -> list[ChangelogImporter]:
    return [
        _PlainTextImporter(),
        _KeepAChanhelogImporter()
    ]

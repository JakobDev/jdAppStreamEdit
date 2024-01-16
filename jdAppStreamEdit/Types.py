from typing import Optional, TypedDict, Literal
from PyQt6.QtCore import QDate
from lxml import etree


class ScreenshotDictImage(TypedDict):
    url: str
    type: Literal["source", "thumbnail"]
    language: Optional[str]
    width: Optional[int]
    height: Optional[int]
    scale_factor: Optional[int]


class ScreenshotDict(TypedDict):
    default: bool
    caption: Optional[str]
    caption_translations: Optional[dict[str, str]]
    images: list[ScreenshotDictImage]
    source_url: str


class ReleaseInfoDict(TypedDict, total=False):
    url: str
    urgency: str
    description: etree.Element
    artifacts: etree.Element


class SingleReleaseImportInfo(TypedDict, total=False):
    version: str
    date: QDate
    type: Literal["stable", "development", "snapshot"]
    data: ReleaseInfoDict
    changelog_text: str


class ReleaseImportInfo(TypedDict, total=False):
    releases: list[SingleReleaseImportInfo]
    changelog_importer: bool


class PluginDict(TypedDict, total=False):
    id: str
    name: str
    init: str
    description: str
    homepage: str

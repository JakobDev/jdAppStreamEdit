from typing import Optional, TypedDict, Literal
from PyQt6.QtCore import QDate


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


class ReleaseImportInfo(TypedDict):
    version: str
    date: QDate
    development: bool
    data: dict


class PluginDict(TypedDict, total=False):
    id: str
    name: str
    init: str
    description: str
    homepage: str

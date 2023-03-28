from typing import Optional, TypedDict, Literal


class ScreenshotDictImage(TypedDict):
    url: str
    type: Literal["source", "thumbnail"]
    language: Optional[str]
    width: Optional[int]
    height: Optional[int]


class ScreenshotDict(TypedDict):
    default: bool
    caption: Optional[str]
    caption_translations: Optional[dict[str, str]]
    images: list[ScreenshotDictImage]
    source_url: str

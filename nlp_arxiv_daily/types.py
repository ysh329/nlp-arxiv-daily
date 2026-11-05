from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, NotRequired, TypedDict


@dataclass(frozen=True)
class Paper:
    paper_id: str
    title: str
    first_author: str
    update_time: date
    paper_url: str
    code_link: str | None
    model_link: str | None = None
    arxiv_short_id: str = ""
    authors: tuple[str, ...] = ()
    abstract: str = ""
    categories: tuple[str, ...] = ()


class KeywordConfig(TypedDict):
    filters: list[str]


class WebRecord(TypedDict):
    date: str
    title: str
    authors: list[str]
    url: str
    code: str | None
    model: NotRequired[str | None]
    categories: list[str]


PaperValue = str | dict[str, Any]
PapersByKeyword = dict[str, dict[str, PaperValue]]
PapersByMonth = dict[str, dict[str, dict[str, PaperValue]]]

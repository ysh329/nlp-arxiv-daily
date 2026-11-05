"""Conversions between Paper, persisted web records, and legacy rows."""

from __future__ import annotations

import re

from nlp_arxiv_daily.types import Paper, PaperValue, WebRecord


_LEGACY_CODE_RE = re.compile(r"\*\*\[[^\]]*\]\((https?://[^)]+)\)\*\*")


def paper_to_web_record(p: Paper) -> WebRecord:
    """Persist public links; abstracts remain excluded to keep JSON compact."""
    authors = list(p.authors) if p.authors else [p.first_author]
    return {
        "date": p.update_time.isoformat(),
        "title": p.title,
        "authors": authors,
        "url": p.paper_url,
        "code": p.code_link,
        **({"model": p.model_link} if p.model_link else {}),
        "categories": list(p.categories),
    }


def web_line(date: str, title: str, first_author: str, url: str, code: str | None) -> str:
    line = f"- {date}, **{title}**, {first_author} et.al., Paper: [{url}]({url})"
    if code:
        line += f", Code: **[{code}]({code})**"
    return line + "\n"


def web_record_to_line(value: PaperValue) -> str:
    if isinstance(value, str):
        return value
    authors = value.get("authors") or [""]
    return web_line(value["date"], value["title"], authors[0], value["url"], value.get("code"))


def code_link_from_value(value: PaperValue) -> str | None:
    if isinstance(value, dict):
        return value.get("code") or None
    match = _LEGACY_CODE_RE.search(value)
    return match.group(1) if match else None

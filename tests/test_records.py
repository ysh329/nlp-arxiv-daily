from __future__ import annotations

import datetime
import json

from nlp_arxiv_daily.records import paper_to_web_record, web_record_to_line
from nlp_arxiv_daily.types import Paper


def _paper(**overrides) -> Paper:
    base = {
        "paper_id": "2604.21637",
        "title": "A Title",
        "first_author": "Alice",
        "update_time": datetime.date(2026, 4, 22),
        "paper_url": "http://arxiv.org/abs/2604.21637v1",
        "code_link": None,
        "arxiv_short_id": "2604.21637v1",
        "authors": ("Alice", "Bob"),
        "abstract": "We study things.",
        "categories": ("cs.CL", "cs.AI"),
    }
    return Paper(**{**base, **overrides})


def test_new_fields_default_empty():
    paper = Paper(
        paper_id="2604.21637",
        title="T",
        first_author="Alice",
        update_time=datetime.date(2026, 4, 22),
        paper_url="u",
        code_link=None,
    )
    assert paper.authors == ()
    assert paper.abstract == ""
    assert paper.categories == ()
    assert paper.model_link is None


def test_model_link_is_persisted_when_present():
    record = paper_to_web_record(_paper(model_link="https://huggingface.co/acme/model"))
    assert record["model"] == "https://huggingface.co/acme/model"


def test_empty_model_link_is_omitted():
    assert "model" not in paper_to_web_record(_paper())


def test_record_is_json_serializable():
    json.dumps(paper_to_web_record(_paper()))


def test_record_uses_first_author_when_author_list_is_empty():
    assert paper_to_web_record(_paper(authors=()))["authors"] == ["Alice"]

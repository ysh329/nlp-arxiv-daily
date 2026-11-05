"""Structured web records and legacy row compatibility."""

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


class TestPaperDefaults:
    def test_new_fields_default_empty(self):
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


class TestPaperToWebRecord:
    def test_record_shape(self):
        record = paper_to_web_record(_paper(code_link="https://github.com/x/y"))
        assert record == {
            "date": "2026-04-22",
            "title": "A Title",
            "authors": ["Alice", "Bob"],
            "url": "http://arxiv.org/abs/2604.21637v1",
            "code": "https://github.com/x/y",
            "categories": ["cs.CL", "cs.AI"],
        }

    def test_model_link_is_persisted_when_present(self):
        record = paper_to_web_record(_paper(model_link="https://huggingface.co/acme/model"))
        assert record["model"] == "https://huggingface.co/acme/model"

    def test_abstract_is_not_persisted(self):
        assert "abstract" not in paper_to_web_record(_paper(abstract="long text"))

    def test_record_is_json_serialisable(self):
        json.dumps(paper_to_web_record(_paper()))

    def test_no_authors_falls_back_to_first_author(self):
        assert paper_to_web_record(_paper(authors=()))["authors"] == ["Alice"]


class TestWebRecordToLine:
    LEGACY = (
        "- 2026-04-22, **A Title**, Alice et.al., "
        "Paper: [http://arxiv.org/abs/2604.21637v1](http://arxiv.org/abs/2604.21637v1)\n"
    )

    def test_string_passthrough(self):
        assert web_record_to_line(self.LEGACY) is self.LEGACY

    def test_record_renders_legacy_line(self):
        assert web_record_to_line(paper_to_web_record(_paper())) == self.LEGACY

    def test_record_with_code_link(self):
        line = web_record_to_line(paper_to_web_record(_paper(code_link="https://github.com/x/y")))
        assert line.endswith(", Code: **[https://github.com/x/y](https://github.com/x/y)**\n")


class TestCodeLinkFromValue:
    def test_dict_record(self):
        from nlp_arxiv_daily.records import code_link_from_value

        assert code_link_from_value({"code": "https://github.com/x/y"}) == "https://github.com/x/y"
        assert code_link_from_value({"code": None}) is None

    def test_bullet_row(self):
        from nlp_arxiv_daily.records import code_link_from_value

        row = "- 2026-04-22, **T**, A et.al., Paper: [u](u), Code: **[https://github.com/x/y](https://github.com/x/y)**\n"
        assert code_link_from_value(row) == "https://github.com/x/y"
        assert code_link_from_value("- 2026-04-22, **T**, A et.al., Paper: [u](u)\n") is None

    def test_pipe_row(self):
        from nlp_arxiv_daily.records import code_link_from_value

        assert code_link_from_value("|**2025-06-03**|**T**|A et.al.|[id](u)|**[link](https://github.com/x/y)**|\n") == (
            "https://github.com/x/y"
        )
        assert code_link_from_value("|**2025-06-03**|**T**|A et.al.|[id](u)|null|\n") is None

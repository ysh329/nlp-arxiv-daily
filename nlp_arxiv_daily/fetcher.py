from __future__ import annotations

import datetime
import logging
import re
import time
from collections.abc import Iterable, Mapping

import arxiv
import requests
from tenacity import (
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from nlp_arxiv_daily.types import Paper


HF_PAPERS_API = "https://huggingface.co/api/papers/"
REQUEST_TIMEOUT = 10
GITHUB_URL_RE = re.compile(r"https?://github\.com/[\w.-]+/[\w.-]+")
HF_MODEL_URL_RE = re.compile(r"https?://huggingface\.co/(?!datasets/)[\w.-]+/[\w.-]+")
DAILY_RATE_LIMIT_SECONDS = 15
BACKFILL_RATE_LIMIT_SECONDS = 5
DAILY_NUM_RETRIES = 10
BACKFILL_NUM_RETRIES = 10
DAILY_PAGE_SIZE = 100
DEFAULT_DAILY_LOOKBACK_DAYS = 7
BACKFILL_DEFAULT_MAX_RESULTS = 2000
HF_MIN_INTERVAL_SECONDS = 0.5
_hf_last_call_ts: float = 0.0
_DAILY_CLIENT: arxiv.Client | None = None


def _get_daily_client() -> arxiv.Client:
    global _DAILY_CLIENT
    if _DAILY_CLIENT is None:
        _DAILY_CLIENT = arxiv.Client(
            page_size=DAILY_PAGE_SIZE,
            delay_seconds=DAILY_RATE_LIMIT_SECONDS,
            num_retries=DAILY_NUM_RETRIES,
        )
    return _DAILY_CLIENT


def make_backfill_client(delay_seconds: int = BACKFILL_RATE_LIMIT_SECONDS) -> arxiv.Client:
    return arxiv.Client(delay_seconds=delay_seconds, num_retries=BACKFILL_NUM_RETRIES)


def get_authors(authors: Iterable, first_author: bool = False) -> str:
    if first_author:
        return list(authors)[0]
    return ", ".join(str(author) for author in authors)


def _is_retryable_hf_error(exc: BaseException) -> bool:
    if isinstance(exc, requests.HTTPError):
        resp = getattr(exc, "response", None)
        status = getattr(resp, "status_code", None)
        return status == 429 or (status is not None and 500 <= status < 600)
    return isinstance(exc, requests.ConnectionError | requests.Timeout)


@retry(
    retry=retry_if_exception(_is_retryable_hf_error),
    wait=wait_exponential(multiplier=2, min=2, max=30) + wait_random(0, 2),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _hf_lookup(arxiv_id: str) -> dict | None:
    global _hf_last_call_ts
    elapsed = time.monotonic() - _hf_last_call_ts
    if elapsed < HF_MIN_INTERVAL_SECONDS:
        time.sleep(HF_MIN_INTERVAL_SECONDS - elapsed)
    _hf_last_call_ts = time.monotonic()
    response = requests.get(f"{HF_PAPERS_API}{arxiv_id}", timeout=REQUEST_TIMEOUT)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def find_code_link(arxiv_id: str, summary: str | None = None) -> str | None:
    try:
        payload = _hf_lookup(arxiv_id)
        if payload:
            repo = payload.get("githubRepo")
            if repo:
                return repo
    except (requests.RequestException, requests.HTTPError) as error:
        logging.warning(f"HF Papers lookup failed for {arxiv_id}: {error}")
    if summary:
        match = GITHUB_URL_RE.search(summary)
        if match:
            return match.group(0).rstrip(".,);")
    return None


def find_model_link(summary: str | None = None) -> str | None:
    """Return a model URL explicitly present in the abstract; exclude datasets."""
    if summary:
        match = HF_MODEL_URL_RE.search(summary)
        if match:
            return match.group(0).rstrip(".,);")
    return None


def _strip_version_suffix(short_id: str) -> str:
    ver_pos = short_id.find("v")
    return short_id if ver_pos == -1 else short_id[:ver_pos]


def _result_to_paper(result, known_code_links: Mapping[str, str | None] | None = None) -> Paper:
    short_id = result.get_short_id()
    paper_id = _strip_version_suffix(short_id)
    authors = tuple(str(author) for author in result.authors)
    first_author = get_authors(result.authors, first_author=True)
    update_time = result.published.date()
    abstract = " ".join((result.summary or "").split())
    categories = tuple(getattr(result, "categories", None) or ())
    logging.info(f"Time = {update_time} title = {result.title} author = {first_author}")
    if known_code_links is not None and paper_id in known_code_links:
        code_link = known_code_links[paper_id]
    else:
        code_link = find_code_link(paper_id, summary=result.summary)
    return Paper(
        paper_id=paper_id,
        title=result.title,
        first_author=first_author,
        update_time=update_time,
        paper_url=result.entry_id,
        code_link=code_link,
        model_link=find_model_link(result.summary),
        arxiv_short_id=short_id,
        authors=authors,
        abstract=abstract,
        categories=categories,
    )


@retry(
    retry=retry_if_exception_type(arxiv.HTTPError),
    wait=wait_exponential(multiplier=10, min=10, max=120) + wait_random(0, 5),
    stop=stop_after_attempt(4),
    reraise=True,
)
def fetch_papers(query: str, max_results: int) -> list[Paper]:
    client = _get_daily_client()
    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.SubmittedDate)
    return [_result_to_paper(result) for result in client.results(search)]


def _format_arxiv_datetime(dt: datetime.date, *, end_of_day: bool) -> str:
    suffix = "2359" if end_of_day else "0000"
    return f"{dt.year:04d}{dt.month:02d}{dt.day:02d}{suffix}"


@retry(
    retry=retry_if_exception_type(arxiv.HTTPError),
    wait=wait_exponential(multiplier=10, min=10, max=120) + wait_random(0, 5),
    stop=stop_after_attempt(4),
    reraise=True,
)
def fetch_papers_in_range(
    query: str,
    start: datetime.date,
    end: datetime.date,
    max_results: int = BACKFILL_DEFAULT_MAX_RESULTS,
    delay_seconds: int = BACKFILL_RATE_LIMIT_SECONDS,
    known_code_links: Mapping[str, str | None] | None = None,
    client: arxiv.Client | None = None,
) -> list[Paper]:
    range_clause = (
        f"submittedDate:[{_format_arxiv_datetime(start, end_of_day=False)}"
        f" TO {_format_arxiv_datetime(end, end_of_day=True)}]"
    )
    composite = f"({query}) AND {range_clause}"
    if client is None:
        client = arxiv.Client(
            delay_seconds=delay_seconds,
            num_retries=BACKFILL_NUM_RETRIES,
        )
    search = arxiv.Search(query=composite, max_results=max_results, sort_by=arxiv.SortCriterion.SubmittedDate)
    return [_result_to_paper(result, known_code_links) for result in client.results(search)]


def fetch_recent_papers(
    query: str,
    *,
    lookback_days: int = DEFAULT_DAILY_LOOKBACK_DAYS,
    max_results: int,
    known_code_links: Mapping[str, str | None] | None = None,
    today: datetime.date | None = None,
) -> list[Paper]:
    if today is None:
        today = datetime.date.today()
    start = today - datetime.timedelta(days=max(lookback_days, 1) - 1)
    return fetch_papers_in_range(
        query,
        start,
        today,
        max_results=max_results,
        known_code_links=known_code_links,
        client=_get_daily_client(),
    )

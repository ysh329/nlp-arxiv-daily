from nlp_arxiv_daily.fetcher import find_model_link


def test_find_model_link_from_summary():
    summary = "Model: https://huggingface.co/acme/tiny-model. Code: https://github.com/acme/code"
    assert find_model_link(summary) == "https://huggingface.co/acme/tiny-model"


def test_find_model_link_ignores_dataset_and_missing_links():
    assert find_model_link("Data: https://huggingface.co/datasets/acme/data") is None
    assert find_model_link("No model link") is None

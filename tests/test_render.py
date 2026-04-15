from __future__ import annotations

from searxng_mcp.render import approximate_tokens, normalize_url, result_summary_line


def test_normalize_url_strips_tracking_and_trailing_slash() -> None:
    url = "https://example.com/path/?utm_source=newsletter&gclid=123&x=1#fragment"
    assert normalize_url(url) == "https://example.com/path?x=1"


def test_result_summary_line_contains_title_and_url() -> None:
    line = result_summary_line(
        {
            "title": "Example",
            "url": "https://example.com/path",
            "content": "Snippet text",
            "engine": "brave",
            "score": 4.0,
        },
        1,
    )
    assert "[Example](https://example.com/path)" in line
    assert "brave" in line
    assert "Snippet text" in line


def test_approximate_tokens_returns_positive_count() -> None:
    assert approximate_tokens("hello world") > 0


from __future__ import annotations


import httpx

import searxng_mcp.extract as extract_module
from searxng_mcp.extract import extract_from_html, extract_from_response


def make_response(
    url: str, content: str, content_type: str = "text/html; charset=utf-8"
) -> httpx.Response:
    return httpx.Response(
        200,
        content=content.encode("utf-8"),
        headers={"content-type": content_type},
        request=httpx.Request("GET", url),
    )


def test_extract_html_document() -> None:
    response = make_response(
        "https://example.org/article",
        """
        <html>
          <head>
            <title>Example Article</title>
            <meta name="description" content="Short description.">
          </head>
          <body>
            <main>
              <h1>Heading One</h1>
              <p>First paragraph.</p>
              <p>Second paragraph with a <a href="/docs">docs link</a>.</p>
            </main>
          </body>
        </html>
        """,
    )

    document = extract_from_response(response, max_excerpt_chars=400)

    assert document.title == "Example Article"
    assert document.description == "Short description."
    assert "Heading One" in document.headings
    assert document.links[0]["url"] == "https://example.org/docs"
    assert "First paragraph" in document.excerpt


def test_extract_pdf_document(monkeypatch) -> None:
    monkeypatch.setattr(
        extract_module, "extract_pdf_text", lambda *args, **kwargs: "PDF text body"
    )
    response = httpx.Response(
        200,
        content=b"%PDF-1.4 test",
        headers={"content-type": "application/pdf"},
        request=httpx.Request("GET", "https://example.org/file.pdf"),
    )

    document = extract_from_response(response, max_excerpt_chars=100)

    assert document.content_type == "application/pdf"
    assert "PDF text body" in document.text
    assert document.excerpt == "PDF text body"


def test_extract_rendered_html_document_marks_rendered() -> None:
    document = extract_from_html(
        """
        <html>
          <head><title>Rendered Article</title></head>
          <body>
            <main>
              <h1>Rendered Heading</h1>
              <p>Rendered body text.</p>
            </main>
          </body>
        </html>
        """,
        url="https://example.org/rendered",
        max_excerpt_chars=400,
        rendered=True,
    )

    assert document.rendered is True
    assert document.to_summary()["rendered"] is True
    assert document.title == "Rendered Article"
    assert "Rendered Heading" in document.headings

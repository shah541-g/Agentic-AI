"""Tests for link and metadata extractor."""
import pytest
from linkatlas.extractor import extract_links


def test_basic_link_and_title_extraction():
    html = b"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>   Example    Page Title   </title>
    </head>
    <body>
        <h1>Hello World</h1>
        <a href="/about">About Us</a>
        <a href="https://example.org/docs">Documentation</a>
    </body>
    </html>
    """
    res = extract_links(html, "https://example.com/home")
    assert res.title == "Example Page Title"
    assert res.page_nofollow is False
    assert res.ignored_links == 0
    assert len(res.links) == 2
    assert res.links[0].url == "https://example.com/about"
    assert res.links[0].text == "About Us"
    assert res.links[0].nofollow is False
    assert res.links[1].url == "https://example.org/docs"
    assert res.links[1].text == "Documentation"


def test_base_href_resolution():
    html = b"""
    <html>
    <head>
        <base href="https://cdn.example.com/assets/">
    </head>
    <body>
        <a href="page.html">Page</a>
    </body>
    </html>
    """
    res = extract_links(html, "https://example.com/")
    assert len(res.links) == 1
    assert res.links[0].url == "https://cdn.example.com/assets/page.html"


def test_nofollow_rel():
    html = b"""
    <body>
        <a href="/a" rel="nofollow">NoFollow 1</a>
        <a href="/b" rel="external nofollow noopener">NoFollow 2</a>
        <a href="/c" rel="external">Follow</a>
    </body>
    """
    res = extract_links(html, "https://example.com/")
    assert len(res.links) == 3
    assert res.links[0].nofollow is True
    assert res.links[1].nofollow is True
    assert res.links[2].nofollow is False


def test_meta_robots_nofollow():
    html_nofollow = b"""
    <html>
    <head>
        <meta name="robots" content="index, nofollow">
    </head>
    <body><a href="/link">Link</a></body>
    </html>
    """
    res = extract_links(html_nofollow, "https://example.com/")
    assert res.page_nofollow is True

    html_none = b"""
    <html>
    <head>
        <meta name="ROBOTS" content="none">
    </head>
    <body><a href="/link">Link</a></body>
    </html>
    """
    res = extract_links(html_none, "https://example.com/")
    assert res.page_nofollow is True

    html_follow = b"""
    <html>
    <head>
        <meta name="robots" content="index, follow">
    </head>
    <body><a href="/link">Link</a></body>
    </html>
    """
    res = extract_links(html_follow, "https://example.com/")
    assert res.page_nofollow is False


def test_ignored_schemes_and_fragments():
    html = b"""
    <body>
        <a href="#top">Top Anchor</a>
        <a href="">Empty</a>
        <a href="mailto:support@example.com">Email Us</a>
        <a href="tel:+123456789">Call Us</a>
        <a href="javascript:void(0)">Click</a>
        <a href="ftp://ftp.example.com/file">FTP</a>
        <a href="/valid">Valid Link</a>
    </body>
    """
    res = extract_links(html, "https://example.com/")
    assert res.ignored_links == 4  # mailto, tel, javascript, ftp
    assert len(res.links) == 1
    assert res.links[0].url == "https://example.com/valid"


def test_text_truncation_and_whitespace():
    long_text = "   Word   " * 30
    html = f'<body><a href="/path">{long_text}</a></body>'.encode("utf-8")
    res = extract_links(html, "https://example.com/")
    assert len(res.links) == 1
    assert len(res.links[0].text) <= 80
    assert not res.links[0].text.startswith(" ")
    assert not res.links[0].text.endswith(" ")
    assert "  " not in res.links[0].text


def test_title_truncation_and_missing():
    long_title = "Title " * 50
    html = f"<head><title>{long_title}</title></head>".encode("utf-8")
    res = extract_links(html, "https://example.com/")
    assert res.title is not None
    assert len(res.title) <= 120

    html_no_title = b"<body><h1>No Title</h1></body>"
    res2 = extract_links(html_no_title, "https://example.com/")
    assert res2.title is None


def test_broken_html_does_not_raise():
    broken = b"<html><head><title>Page</title></head><body><a href='/broken' rel=nofollow>Link<div><span>"
    res = extract_links(broken, "https://example.com/")
    assert res.title == "Page"
    assert len(res.links) == 1
    assert res.links[0].url == "https://example.com/broken"

    res_empty = extract_links(b"", "https://example.com/")
    assert res_empty.links == []
    assert res_empty.ignored_links == 0

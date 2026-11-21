"""Comprehensive tests for linkatlas.urls."""
import pytest
from linkatlas.urls import normalize_url, site_key, is_internal, has_skippable_extension, domain_of


# ---------------------------------------------------------------------------
# normalize_url
# ---------------------------------------------------------------------------

class TestNormalizeUrl:

    def test_relative_url_with_base(self):
        result = normalize_url("/about", base="http://example.com/page")
        assert result == "http://example.com/about"

    def test_absolute_url_no_base(self):
        result = normalize_url("https://example.com/page")
        assert result == "https://example.com/page"

    def test_fragment_stripped(self):
        result = normalize_url("http://example.com/page#section")
        assert result == "http://example.com/page"

    def test_http_default_port_80_removed(self):
        result = normalize_url("http://example.com:80/page")
        assert result == "http://example.com/page"

    def test_https_default_port_443_removed(self):
        result = normalize_url("https://example.com:443/page")
        assert result == "https://example.com/page"

    def test_non_default_port_8080_kept(self):
        result = normalize_url("http://example.com:8080/page")
        assert result == "http://example.com:8080/page"

    def test_utm_source_removed(self):
        result = normalize_url("http://example.com/?utm_source=google&q=1")
        assert "utm_source" not in result
        assert "q=1" in result

    def test_utm_campaign_removed(self):
        result = normalize_url("http://example.com/?utm_campaign=spring&q=1")
        assert "utm_campaign" not in result
        assert "q=1" in result

    def test_utm_medium_removed(self):
        result = normalize_url("http://example.com/?utm_medium=email&q=1")
        assert "utm_medium" not in result
        assert "q=1" in result

    def test_fbclid_removed(self):
        result = normalize_url("http://example.com/?fbclid=abc123&q=1")
        assert "fbclid" not in result
        assert "q=1" in result

    def test_gclid_removed(self):
        result = normalize_url("http://example.com/?gclid=xyz&q=1")
        assert "gclid" not in result
        assert "q=1" in result

    def test_msclkid_removed(self):
        result = normalize_url("http://example.com/?msclkid=xyz&q=1")
        assert "msclkid" not in result
        assert "q=1" in result

    def test_mc_cid_removed(self):
        result = normalize_url("http://example.com/?mc_cid=xyz&q=1")
        assert "mc_cid" not in result
        assert "q=1" in result

    def test_mc_eid_removed(self):
        result = normalize_url("http://example.com/?mc_eid=xyz&q=1")
        assert "mc_eid" not in result
        assert "q=1" in result

    def test_non_tracking_params_kept_in_order(self):
        result = normalize_url("http://example.com/?a=1&b=2&c=3")
        assert result == "http://example.com/?a=1&b=2&c=3"

    def test_uppercase_scheme_lowercased(self):
        result = normalize_url("HTTP://Example.COM/path")
        assert result.startswith("http://")
        assert "example.com" in result

    def test_uppercase_host_lowercased(self):
        result = normalize_url("https://EXAMPLE.COM/path")
        assert "example.com" in result
        assert "EXAMPLE" not in result

    def test_empty_path_becomes_slash(self):
        result = normalize_url("http://example.com")
        assert result == "http://example.com/"

    def test_mailto_returns_none(self):
        assert normalize_url("mailto:user@example.com") is None

    def test_javascript_returns_none(self):
        assert normalize_url("javascript:void(0)") is None

    def test_data_returns_none(self):
        assert normalize_url("data:text/html,<h1>Hi</h1>") is None

    def test_ftp_returns_none(self):
        assert normalize_url("ftp://files.example.com/pub/file.zip") is None

    def test_url_longer_than_2000_chars_returns_none(self):
        long_url = "http://example.com/" + "a" * 1990
        assert len(long_url) > 2000
        assert normalize_url(long_url) is None


# ---------------------------------------------------------------------------
# site_key
# ---------------------------------------------------------------------------

class TestSiteKey:

    def test_www_prefix_stripped_and_lowercased(self):
        assert site_key("www.Example.com") == "example.com"

    def test_subdomain_not_stripped(self):
        assert site_key("sub.example.com") == "sub.example.com"

    def test_plain_domain(self):
        assert site_key("example.com") == "example.com"


# ---------------------------------------------------------------------------
# is_internal
# ---------------------------------------------------------------------------

class TestIsInternal:

    def test_www_and_bare_same_domain_no_subdomains(self):
        assert is_internal("http://example.com/", "http://www.example.com/", False) is True

    def test_subdomain_not_internal_without_flag(self):
        assert is_internal("http://sub.example.com/", "http://example.com/", False) is False

    def test_subdomain_internal_with_flag(self):
        assert is_internal("http://sub.example.com/", "http://example.com/", True) is True

    def test_different_domain_not_internal_with_flag(self):
        assert is_internal("http://other.com/", "http://example.com/", True) is False


# ---------------------------------------------------------------------------
# has_skippable_extension
# ---------------------------------------------------------------------------

class TestHasSkippableExtension:

    def test_pdf_skippable(self):
        assert has_skippable_extension("/file.pdf") is True

    def test_pdf_uppercase_case_insensitive(self):
        assert has_skippable_extension("/a.PDF") is True

    def test_html_not_skippable(self):
        assert has_skippable_extension("/a.html") is False

    def test_pdf_with_query_string_path_only(self):
        assert has_skippable_extension("/file.pdf?v=1") is True

    def test_no_extension_not_skippable(self):
        assert has_skippable_extension("/about/page") is False

    def test_js_skippable(self):
        assert has_skippable_extension("/a.js") is True


# ---------------------------------------------------------------------------
# domain_of
# ---------------------------------------------------------------------------

class TestDomainOf:

    def test_www_stripped_and_lowercased(self):
        assert domain_of("https://www.Example.com/path") == "example.com"

    def test_subdomain_preserved(self):
        assert domain_of("https://sub.host.org/x") == "sub.host.org"

"""
Tests for zirflow-search scripts/search.py
"""
import sys
import os

# Add scripts dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

# Mock the env loading before import
os.environ["TAVILY_API_KEY_1"] = "test_key_for_import"
os.environ["TAVILY_KEY_INDEX"] = "1"

import pytest
import subprocess
import json


class TestIsUrl:
    """Test is_url() helper function"""

    def test_http_url_returns_true(self):
        from search import is_url
        assert is_url("https://example.com") is True
        assert is_url("http://example.com") is True

    def test_https_url_with_path_returns_true(self):
        from search import is_url
        assert is_url("https://github.com/user/repo") is True

    def test_plain_domain_returns_true(self):
        from search import is_url
        assert is_url("example.com") is True

    def test_regular_text_returns_false(self):
        from search import is_url
        assert is_url("hello world") is False
        assert is_url("python programming") is False

    def test_empty_string_returns_false(self):
        from search import is_url
        assert is_url("") is False
        assert is_url("   ") is False


class TestIsChinese:
    """Test is_chinese() helper function"""

    def test_chinese_text_returns_true(self):
        from search import is_chinese
        assert is_chinese("你好世界") is True
        assert is_chinese("Python教程") is True

    def test_english_text_returns_false(self):
        from search import is_chinese
        assert is_chinese("hello world") is False
        assert is_chinese("python programming") is False

    def test_mixed_text_returns_true(self):
        from search import is_chinese
        assert is_chinese("Hello 你好 World") is True


class TestExtractTitle:
    """Test extract_title() helper function"""

    def test_markdown_heading(self):
        from search import extract_title
        content = "# Hello World\n\nSome content here"
        assert extract_title(content) == "Hello World"

    def test_plain_first_line(self):
        from search import extract_title
        content = "Just a plain line\n\nMore content"
        assert extract_title(content) == "Just a plain line"

    def test_none_returns_none(self):
        from search import extract_title
        assert extract_title(None) is None

    def test_empty_string_returns_none(self):
        from search import extract_title
        assert extract_title("") is None

    def test_url_line_is_skipped(self):
        from search import extract_title
        content = "https://example.com\nSecond line title"
        # First line is a URL, should skip to second
        result = extract_title(content)
        assert result == "Second line title"


class TestRunCmd:
    """Test run_cmd() helper function"""

    def test_echo_returns_output(self):
        from search import run_cmd
        stdout, stderr, code = run_cmd("echo hello")
        assert stdout == "hello"
        assert code == 0

    def test_invalid_command_returns_nonzero(self):
        from search import run_cmd
        stdout, stderr, code = run_cmd("exit 1")
        assert code == 1

    def test_timeout_returns_timeout_code(self):
        from search import run_cmd
        stdout, stderr, code = run_cmd("sleep 10", timeout=1)
        assert code == -1
        assert "TIMEOUT" in stderr


class TestJinaFetch:
    """Test Jina URL fetcher"""

    def test_jina_fetch_returns_tuple(self):
        from search import jina_fetch
        # Use a simple, fast URL for testing
        result, src = jina_fetch("https://example.com", timeout=10)
        # Should return (content, source) tuple or (None, None)
        assert isinstance(result, (str, type(None)))
        assert src is None or isinstance(src, str)

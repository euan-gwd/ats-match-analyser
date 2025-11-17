"""Unit tests for app.py"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import io
from app import (
    extract_text_from_pdf,
    fetch_text_from_url,
    get_job_description_text,
    get_linkedin_profile_text,
)


class TestExtractTextFromPDF:
    def test_extract_from_valid_pdf(self):
        # Create a simple PDF-like bytes object (mock)
        # In real scenario, you'd use a real PDF or better mock
        with patch("app.PdfReader") as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = "Sample text from PDF"

            mock_pdf = Mock()
            mock_pdf.pages = [mock_page]
            mock_reader.return_value = mock_pdf

            result = extract_text_from_pdf(b"fake pdf bytes")
            assert result == "Sample text from PDF"

    def test_extract_handles_multiple_pages(self):
        with patch("app.PdfReader") as mock_reader:
            mock_page1 = Mock()
            mock_page1.extract_text.return_value = "Page 1"
            mock_page2 = Mock()
            mock_page2.extract_text.return_value = "Page 2"

            mock_pdf = Mock()
            mock_pdf.pages = [mock_page1, mock_page2]
            mock_reader.return_value = mock_pdf

            result = extract_text_from_pdf(b"fake pdf bytes")
            assert "Page 1" in result
            assert "Page 2" in result

    def test_extract_handles_extraction_error_gracefully(self):
        with patch("app.PdfReader") as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.side_effect = Exception("Extraction failed")

            mock_pdf = Mock()
            mock_pdf.pages = [mock_page]
            mock_reader.return_value = mock_pdf

            result = extract_text_from_pdf(b"fake pdf bytes")
            # Should return empty string for failed page
            assert result == ""

    def test_extract_raises_on_invalid_pdf(self):
        with patch("app.PdfReader") as mock_reader:
            mock_reader.side_effect = Exception("Invalid PDF")

            with pytest.raises(RuntimeError, match="Failed to read PDF"):
                extract_text_from_pdf(b"invalid bytes")

    def test_extract_handles_none_text(self):
        with patch("app.PdfReader") as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = None

            mock_pdf = Mock()
            mock_pdf.pages = [mock_page]
            mock_reader.return_value = mock_pdf

            result = extract_text_from_pdf(b"fake pdf bytes")
            assert result == ""


class TestFetchTextFromURL:
    def test_fetch_successful(self):
        with patch("app.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = "<html><body><main>Job posting content</main></body></html>"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = fetch_text_from_url("https://example.com/job")
            assert "Job posting content" in result

    def test_fetch_removes_script_tags(self):
        with patch("app.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = """
            <html>
                <body>
                    <main>
                        Job content
                        <script>alert('test')</script>
                    </main>
                </body>
            </html>
            """
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = fetch_text_from_url("https://example.com/job")
            assert "alert" not in result
            assert "Job content" in result

    def test_fetch_handles_no_main_tag(self):
        with patch("app.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = "<html><body>Simple content</body></html>"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = fetch_text_from_url("https://example.com/job")
            assert "Simple content" in result

    def test_fetch_raises_on_http_error(self):
        with patch("app.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("404 Not Found")
            mock_get.return_value = mock_response

            with pytest.raises(RuntimeError, match="Failed to fetch URL"):
                fetch_text_from_url("https://example.com/job")

    def test_fetch_respects_timeout(self):
        with patch("app.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = "<html><body>Content</body></html>"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            fetch_text_from_url("https://example.com/job")
            mock_get.assert_called_once_with("https://example.com/job", timeout=10)

    def test_fetch_removes_multiple_tag_types(self):
        with patch("app.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.text = """
            <html>
                <body>
                    <nav>Navigation</nav>
                    <main>Main content</main>
                    <footer>Footer</footer>
                    <style>body { color: red; }</style>
                </body>
            </html>
            """
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            result = fetch_text_from_url("https://example.com/job")
            assert "Navigation" not in result
            assert "Footer" not in result
            assert "color: red" not in result
            assert "Main content" in result


class TestGetJobDescriptionText:
    def test_paste_text_mode(self):
        result = get_job_description_text(
            mode="Paste text",
            pasted_text="Job description here",
            jd_pdf_file=None,
            jd_url=None,
        )
        assert result == "Job description here"

    def test_paste_text_strips_whitespace(self):
        result = get_job_description_text(
            mode="Paste text",
            pasted_text="  Job description  \n\n",
            jd_pdf_file=None,
            jd_url=None,
        )
        assert result == "Job description"

    def test_paste_text_handles_none(self):
        result = get_job_description_text(
            mode="Paste text",
            pasted_text=None,
            jd_pdf_file=None,
            jd_url=None,
        )
        assert result == ""

    def test_upload_pdf_mode(self):
        with patch("app.extract_text_from_pdf") as mock_extract:
            mock_extract.return_value = "PDF content"
            mock_file = Mock()
            mock_file.read.return_value = b"pdf bytes"

            result = get_job_description_text(
                mode="Upload PDF",
                pasted_text=None,
                jd_pdf_file=mock_file,
                jd_url=None,
            )
            assert result == "PDF content"
            mock_extract.assert_called_once_with(b"pdf bytes")

    def test_upload_pdf_no_file(self):
        result = get_job_description_text(
            mode="Upload PDF",
            pasted_text=None,
            jd_pdf_file=None,
            jd_url=None,
        )
        assert result == ""

    def test_job_url_mode(self):
        with patch("app.fetch_text_from_url") as mock_fetch:
            mock_fetch.return_value = "URL content"

            result = get_job_description_text(
                mode="Job URL",
                pasted_text=None,
                jd_pdf_file=None,
                jd_url="https://example.com/job",
            )
            assert result == "URL content"
            mock_fetch.assert_called_once_with("https://example.com/job")

    def test_job_url_no_url(self):
        result = get_job_description_text(
            mode="Job URL",
            pasted_text=None,
            jd_pdf_file=None,
            jd_url=None,
        )
        assert result == ""

    def test_unknown_mode(self):
        result = get_job_description_text(
            mode="Unknown Mode",
            pasted_text="text",
            jd_pdf_file=None,
            jd_url=None,
        )
        assert result == ""


class TestGetLinkedInProfileText:
    def test_fetch_linkedin_success(self):
        with patch("app.fetch_text_from_url") as mock_fetch:
            mock_fetch.return_value = "LinkedIn profile content"

            result = get_linkedin_profile_text("https://linkedin.com/in/profile")
            assert result == "LinkedIn profile content"

    def test_fetch_linkedin_error_returns_empty(self):
        with patch("app.fetch_text_from_url") as mock_fetch:
            mock_fetch.side_effect = RuntimeError("Fetch failed")

            result = get_linkedin_profile_text("https://linkedin.com/in/profile")
            assert result == ""

    def test_no_url_provided(self):
        result = get_linkedin_profile_text(None)
        assert result == ""

    def test_empty_url(self):
        result = get_linkedin_profile_text("")
        assert result == ""

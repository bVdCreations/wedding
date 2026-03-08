"""Tests for EmailTemplates date formatting."""

from datetime import date

import pytest

from src.email_service.template_builder import EmailTemplates
from src.guests.dtos import Language


class TestDateFormatting:
    """Tests for _format_date method."""

    @pytest.fixture
    def templates(self):
        return EmailTemplates()

    def test_ceremony_date_english(self, templates):
        """Test ceremony date format in English."""
        d = date(2026, 11, 7)
        result = templates._format_date(d, Language.EN)
        assert result == "November 7, 2026"

    def test_ceremony_date_spanish(self, templates):
        """Test ceremony date format in Spanish."""
        d = date(2026, 11, 7)
        result = templates._format_date(d, Language.ES)
        assert result == "7 de noviembre de 2026"

    def test_ceremony_date_dutch(self, templates):
        """Test ceremony date format in Dutch."""
        d = date(2026, 11, 7)
        result = templates._format_date(d, Language.NL)
        assert result == "7 november 2026"

    def test_rsvp_deadline_english(self, templates):
        """Test RSVP deadline format in English."""
        d = date(2026, 4, 2)
        result = templates._format_date(d, Language.EN)
        assert result == "April 2, 2026"

    def test_rsvp_deadline_spanish(self, templates):
        """Test RSVP deadline format in Spanish."""
        d = date(2026, 4, 2)
        result = templates._format_date(d, Language.ES)
        assert result == "2 de abril de 2026"

    def test_rsvp_deadline_dutch(self, templates):
        """Test RSVP deadline format in Dutch."""
        d = date(2026, 4, 2)
        result = templates._format_date(d, Language.NL)
        assert result == "2 april 2026"

    def test_various_months(self, templates):
        """Test various months are formatted correctly."""
        test_cases = [
            (date(2026, 1, 15), Language.EN, "January 15, 2026"),
            (date(2026, 2, 28), Language.EN, "February 28, 2026"),
            (date(2026, 3, 1), Language.EN, "March 1, 2026"),
            (date(2026, 12, 31), Language.EN, "December 31, 2026"),
        ]
        for d, lang, expected in test_cases:
            result = templates._format_date(d, lang)
            assert result == expected


class TestInvitationTemplatesIncludeFormattedDates:
    """Tests that invitation templates include properly formatted dates."""

    @pytest.fixture
    def templates(self):
        return EmailTemplates()

    def test_invitation_english_contains_formatted_date(self, templates):
        """Test English invitation contains formatted ceremony date."""
        content = templates.get_invitation_templates(
            language=Language.EN,
            guest_name="John Doe",
            rsvp_url="https://example.com/rsvp",
        )
        assert "November 7, 2026" in content.html_body
        assert "November 7, 2026" in content.text_body

    def test_invitation_spanish_contains_formatted_date(self, templates):
        """Test Spanish invitation contains formatted ceremony date."""
        content = templates.get_invitation_templates(
            language=Language.ES,
            guest_name="Juan Perez",
            rsvp_url="https://example.com/rsvp",
        )
        assert "7 de noviembre de 2026" in content.html_body
        assert "7 de noviembre de 2026" in content.text_body

    def test_invitation_dutch_contains_formatted_date(self, templates):
        """Test Dutch invitation contains formatted ceremony date."""
        content = templates.get_invitation_templates(
            language=Language.NL,
            guest_name="Jan Janssen",
            rsvp_url="https://example.com/rsvp",
        )
        assert "7 november 2026" in content.html_body
        assert "7 november 2026" in content.text_body

    def test_invitation_english_contains_formatted_deadline(self, templates):
        """Test English invitation contains formatted deadline."""
        content = templates.get_invitation_templates(
            language=Language.EN,
            guest_name="John Doe",
            rsvp_url="https://example.com/rsvp",
        )
        assert "April 2, 2026" in content.html_body
        assert "April 2, 2026" in content.text_body

    def test_invitation_spanish_contains_formatted_deadline(self, templates):
        """Test Spanish invitation contains formatted deadline."""
        content = templates.get_invitation_templates(
            language=Language.ES,
            guest_name="Juan Perez",
            rsvp_url="https://example.com/rsvp",
        )
        assert "2 de abril de 2026" in content.html_body
        assert "2 de abril de 2026" in content.text_body

    def test_invitation_dutch_contains_formatted_deadline(self, templates):
        """Test Dutch invitation contains formatted deadline."""
        content = templates.get_invitation_templates(
            language=Language.NL,
            guest_name="Jan Janssen",
            rsvp_url="https://example.com/rsvp",
        )
        assert "2 april 2026" in content.html_body
        assert "2 april 2026" in content.text_body

    def test_plus_one_invitation_english_contains_formatted_dates(self, templates):
        """Test English plus one invitation contains formatted dates."""
        content = templates.get_plus_one_invitation_templates(
            language=Language.EN,
            guest_name="Jane Smith",
            inviter_name="John Doe",
            rsvp_url="https://example.com/rsvp",
        )
        assert "November 7, 2026" in content.html_body
        assert "April 2, 2026" in content.html_body

    def test_plus_one_invitation_spanish_contains_formatted_dates(self, templates):
        """Test Spanish plus one invitation contains formatted dates."""
        content = templates.get_plus_one_invitation_templates(
            language=Language.ES,
            guest_name="Jane Smith",
            inviter_name="John Doe",
            rsvp_url="https://example.com/rsvp",
        )
        assert "7 de noviembre de 2026" in content.html_body
        assert "2 de abril de 2026" in content.html_body

    def test_plus_one_invitation_dutch_contains_formatted_dates(self, templates):
        """Test Dutch plus one invitation contains formatted dates."""
        content = templates.get_plus_one_invitation_templates(
            language=Language.NL,
            guest_name="Jane Smith",
            inviter_name="John Doe",
            rsvp_url="https://example.com/rsvp",
        )
        assert "7 november 2026" in content.html_body
        assert "2 april 2026" in content.html_body


class TestConfirmationTemplatesIncludeFormattedDates:
    """Tests that confirmation templates include properly formatted dates."""

    @pytest.fixture
    def templates(self):
        return EmailTemplates()

    def test_confirmation_english_contains_formatted_date(self, templates):
        """Test English confirmation contains formatted ceremony date."""
        content = templates.get_confirmation_templates(
            language=Language.EN,
            guest_name="John Doe",
            attending="Yes",
            dietary="None",
        )
        assert "November 7, 2026" in content.html_body

    def test_confirmation_spanish_contains_formatted_date(self, templates):
        """Test Spanish confirmation contains formatted ceremony date."""
        content = templates.get_confirmation_templates(
            language=Language.ES,
            guest_name="Juan Perez",
            attending="Sí",
            dietary="Ninguno",
        )
        assert "7 de noviembre de 2026" in content.html_body

    def test_confirmation_dutch_contains_formatted_date(self, templates):
        """Test Dutch confirmation contains formatted ceremony date."""
        content = templates.get_confirmation_templates(
            language=Language.NL,
            guest_name="Jan Janssen",
            attending="Ja",
            dietary="Geen",
        )
        assert "7 november 2026" in content.html_body

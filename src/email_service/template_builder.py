from dataclasses import dataclass
from datetime import date

from src.email_service import templates
from src.email_service.config import WeddingConfig
from src.guests.dtos import Language


@dataclass
class EmailContent:
    subject: str
    html_body: str
    text_body: str


class EmailTemplates:
    _config: WeddingConfig = WeddingConfig()

    def _format_date(self, d: date, language: Language) -> str:
        """Format a date according to the guest's language."""
        month_names_en = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        month_names_es = [
            "enero",
            "febrero",
            "marzo",
            "abril",
            "mayo",
            "junio",
            "julio",
            "agosto",
            "septiembre",
            "octubre",
            "noviembre",
            "diciembre",
        ]
        month_names_nl = [
            "januari",
            "februari",
            "maart",
            "april",
            "mei",
            "juni",
            "juli",
            "augustus",
            "september",
            "oktober",
            "november",
            "december",
        ]

        day = d.day
        year = d.year

        if language == Language.EN:
            return f"{month_names_en[d.month - 1]} {day}, {year}"
        elif language == Language.ES:
            return f"{day} de {month_names_es[d.month - 1]} de {year}"
        elif language == Language.NL:
            return f"{day} {month_names_nl[d.month - 1]} {year}"
        else:
            return f"{month_names_en[d.month - 1]} {day}, {year}"

    def get_invitation_templates(
        self,
        language: Language,
        guest_name: str,
        rsvp_url: str,
    ) -> EmailContent:
        lang_suffix = language.value.upper()
        subject = getattr(
            templates, f"INVITATION_SUBJECT_{lang_suffix}", templates.INVITATION_SUBJECT_EN
        )
        html = getattr(templates, f"INVITATION_HTML_{lang_suffix}", templates.INVITATION_HTML_EN)
        text = getattr(templates, f"INVITATION_TEXT_{lang_suffix}", templates.INVITATION_TEXT_EN)

        config = self._config
        html_body = html.format(
            guest_name=guest_name,
            rsvp_url=rsvp_url,
            couple_names=config.couple_names,
            ceremony_date=self._format_date(config.ceremony_date, language),
            ceremony_time=config.ceremony_time,
            venue_name=config.venue_name,
            venue_address=config.venue_address,
            rsvp_deadline=self._format_date(config.rsvp_deadline, language),
            contact_email=config.contact_email,
            google_maps_url=config.google_maps_url,
            website_url=config.website_url,
        )
        text_body = text.format(
            guest_name=guest_name,
            rsvp_url=rsvp_url,
            couple_names=config.couple_names,
            ceremony_date=self._format_date(config.ceremony_date, language),
            ceremony_time=config.ceremony_time,
            venue_name=config.venue_name,
            venue_address=config.venue_address,
            rsvp_deadline=self._format_date(config.rsvp_deadline, language),
            contact_email=config.contact_email,
            google_maps_url=config.google_maps_url,
            website_url=config.website_url,
        )
        return EmailContent(subject=subject, html_body=html_body, text_body=text_body)

    def get_confirmation_templates(
        self,
        language: Language,
        guest_name: str,
        attending: str,
        dietary: str,
        allergies: str = "",
        taking_bus: bool = False,
    ) -> EmailContent:
        lang_suffix = language.value.upper()
        subject = getattr(
            templates, f"CONFIRMATION_SUBJECT_{lang_suffix}", templates.CONFIRMATION_SUBJECT_EN
        )
        html = getattr(
            templates, f"CONFIRMATION_HTML_{lang_suffix}", templates.CONFIRMATION_HTML_EN
        )
        text = getattr(
            templates, f"CONFIRMATION_TEXT_{lang_suffix}", templates.CONFIRMATION_TEXT_EN
        )

        taking_bus_str = "Yes" if taking_bus else "No"
        allergies_str = allergies if allergies else "None"

        config = self._config
        html_body = html.format(
            guest_name=guest_name,
            attending=attending,
            dietary=dietary,
            allergies=allergies_str,
            taking_bus=taking_bus_str,
            couple_names=config.couple_names,
            ceremony_date=self._format_date(config.ceremony_date, language),
            ceremony_time=config.ceremony_time,
            venue_name=config.venue_name,
            venue_address=config.venue_address,
            contact_email=config.contact_email,
            google_maps_url=config.google_maps_url,
            website_url=config.website_url,
        )
        text_body = text.format(
            guest_name=guest_name,
            attending=attending,
            dietary=dietary,
            allergies=allergies_str,
            taking_bus=taking_bus_str,
            couple_names=config.couple_names,
            ceremony_date=self._format_date(config.ceremony_date, language),
            ceremony_time=config.ceremony_time,
            venue_name=config.venue_name,
            venue_address=config.venue_address,
            contact_email=config.contact_email,
            google_maps_url=config.google_maps_url,
            website_url=config.website_url,
        )
        return EmailContent(subject=subject, html_body=html_body, text_body=text_body)

    def get_plus_one_invitation_templates(
        self,
        language: Language,
        guest_name: str,
        inviter_name: str,
        rsvp_url: str,
    ) -> EmailContent:
        lang_suffix = language.value.upper()
        subject = getattr(
            templates,
            f"PLUS_ONE_INVITATION_SUBJECT_{lang_suffix}",
            templates.PLUS_ONE_INVITATION_SUBJECT_EN,
        )
        html = getattr(
            templates,
            f"PLUS_ONE_INVITATION_HTML_{lang_suffix}",
            templates.PLUS_ONE_INVITATION_HTML_EN,
        )
        text = getattr(
            templates,
            f"PLUS_ONE_INVITATION_TEXT_{lang_suffix}",
            templates.PLUS_ONE_INVITATION_TEXT_EN,
        )

        config = self._config
        html_body = html.format(
            guest_name=guest_name,
            inviter_name=inviter_name,
            rsvp_url=rsvp_url,
            couple_names=config.couple_names,
            ceremony_date=self._format_date(config.ceremony_date, language),
            ceremony_time=config.ceremony_time,
            venue_name=config.venue_name,
            venue_address=config.venue_address,
            rsvp_deadline=self._format_date(config.rsvp_deadline, language),
            contact_email=config.contact_email,
            google_maps_url=config.google_maps_url,
            website_url=config.website_url,
        )
        text_body = text.format(
            guest_name=guest_name,
            inviter_name=inviter_name,
            rsvp_url=rsvp_url,
            couple_names=config.couple_names,
            ceremony_date=self._format_date(config.ceremony_date, language),
            ceremony_time=config.ceremony_time,
            venue_name=config.venue_name,
            venue_address=config.venue_address,
            rsvp_deadline=self._format_date(config.rsvp_deadline, language),
            contact_email=config.contact_email,
            google_maps_url=config.google_maps_url,
            website_url=config.website_url,
        )
        return EmailContent(subject=subject, html_body=html_body, text_body=text_body)

    def get_rsvp_declined_templates(
        self,
        language: Language,
        guest_name: str,
    ) -> EmailContent:
        lang_suffix = language.value.upper()
        subject = getattr(
            templates,
            f"RSVP_DECLINED_SUBJECT_{lang_suffix}",
            templates.RSVP_DECLINED_SUBJECT_EN,
        )
        html = getattr(
            templates,
            f"RSVP_DECLINED_HTML_{lang_suffix}",
            templates.RSVP_DECLINED_HTML_EN,
        )
        text = getattr(
            templates,
            f"RSVP_DECLINED_TEXT_{lang_suffix}",
            templates.RSVP_DECLINED_TEXT_EN,
        )

        config = self._config
        subject_body = subject.format(guest_name=guest_name)
        html_body = html.format(
            guest_name=guest_name,
            couple_names=config.couple_names,
        )
        text_body = text.format(
            guest_name=guest_name,
            couple_names=config.couple_names,
        )
        return EmailContent(subject=subject_body, html_body=html_body, text_body=text_body)
        return EmailContent(subject=subject, html_body=html_body, text_body=text_body)

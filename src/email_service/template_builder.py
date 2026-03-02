from dataclasses import dataclass

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
            ceremony_date=config.ceremony_date,
            ceremony_time=config.ceremony_time,
            venue_name=config.venue_name,
            venue_address=config.venue_address,
            reception_details=config.reception_details,
            rsvp_deadline=config.rsvp_deadline,
            contact_email=config.contact_email,
            google_maps_url=config.google_maps_url,
        )
        text_body = text.format(
            guest_name=guest_name,
            rsvp_url=rsvp_url,
            couple_names=config.couple_names,
            ceremony_date=config.ceremony_date,
            ceremony_time=config.ceremony_time,
            venue_name=config.venue_name,
            venue_address=config.venue_address,
            reception_details=config.reception_details,
            rsvp_deadline=config.rsvp_deadline,
            contact_email=config.contact_email,
            google_maps_url=config.google_maps_url,
        )
        return EmailContent(subject=subject, html_body=html_body, text_body=text_body)

    def get_confirmation_templates(
        self,
        language: Language,
        guest_name: str,
        attending: str,
        dietary: str,
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

        config = self._config
        html_body = html.format(
            guest_name=guest_name,
            attending=attending,
            dietary=dietary,
            couple_names=config.couple_names,
            ceremony_date=config.ceremony_date,
            ceremony_time=config.ceremony_time,
            venue_name=config.venue_name,
            venue_address=config.venue_address,
            contact_email=config.contact_email,
            google_maps_url=config.google_maps_url,
        )
        text_body = text.format(
            guest_name=guest_name,
            attending=attending,
            dietary=dietary,
            couple_names=config.couple_names,
            ceremony_date=config.ceremony_date,
            ceremony_time=config.ceremony_time,
            venue_name=config.venue_name,
            venue_address=config.venue_address,
            contact_email=config.contact_email,
            google_maps_url=config.google_maps_url,
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
            ceremony_date=config.ceremony_date,
            ceremony_time=config.ceremony_time,
            venue_name=config.venue_name,
            venue_address=config.venue_address,
            reception_details=config.reception_details,
            rsvp_deadline=config.rsvp_deadline,
            contact_email=config.contact_email,
            google_maps_url=config.google_maps_url,
        )
        text_body = text.format(
            guest_name=guest_name,
            inviter_name=inviter_name,
            rsvp_url=rsvp_url,
            couple_names=config.couple_names,
            ceremony_date=config.ceremony_date,
            ceremony_time=config.ceremony_time,
            venue_name=config.venue_name,
            venue_address=config.venue_address,
            reception_details=config.reception_details,
            rsvp_deadline=config.rsvp_deadline,
            contact_email=config.contact_email,
            google_maps_url=config.google_maps_url,
        )
        return EmailContent(subject=subject, html_body=html_body, text_body=text_body)

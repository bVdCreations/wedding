from dataclasses import dataclass

from src.guests.dtos import Language


@dataclass
class EmailTemplates:
    # English templates
    INVITATION_SUBJECT_EN = "You're Invited to Our Wedding!"
    INVITATION_HTML_EN = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #d4a373;">Save the Date!</h1>
        </div>

        <p>Dear {guest_name},</p>

        <p>We are delighted to invite you to our wedding celebration!</p>

        <div style="background-color: #fefae0; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #bc6c25; margin-top: 0;">Wedding Details</h2>
            <p><strong>Date:</strong> {event_date}</p>
            <p><strong>Location:</strong> {event_location}</p>
        </div>

        <p>Please let us know if you can attend by clicking the button below:</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{rsvp_url}" style="background-color: #d4a373; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-size: 18px;">
                RSVP Now
            </a>
        </div>

        <p>If the button doesn't work, you can copy and paste the following link into your browser:</p>
        <p style="word-break: break-all; color: #606c38;"><a href="{rsvp_url}">{rsvp_url}</a></p>

        <p>We kindly ask that you respond by {response_deadline}.</p>

        <p>We look forward to celebrating with you!</p>

        <p>With love,<br>{couple_names}</p>

        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

        <p style="font-size: 12px; color: #888; text-align: center;">
            If you have any questions, please don't hesitate to contact us.
        </p>
    </body>
    </html>
    """

    INVITATION_TEXT_EN = """
    Dear {guest_name},

    We are delighted to invite you to our wedding celebration!

    Wedding Details:
    - Date: {event_date}
    - Location: {event_location}

    Please let us know if you can attend by visiting:
    {rsvp_url}

    We kindly ask that you respond by {response_deadline}.

    We look forward to celebrating with you!

    With love,
    {couple_names}
    """

    CONFIRMATION_SUBJECT_EN = "Thank you for your RSVP!"
    CONFIRMATION_HTML_EN = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #d4a373;">Thank You!</h1>
        </div>

        <p>Dear {guest_name},</p>

        <p>Thank you for responding to our wedding invitation!</p>

        <div style="background-color: #fefae0; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #bc6c25; margin-top: 0;">Your Response</h2>
            <p><strong>Attending:</strong> {attending}</p>
            <p><strong>Dietary Requirements:</strong> {dietary}</p>
        </div>

        <p>We can't wait to celebrate with you!</p>

        <p>With love,<br>{couple_names}</p>
    </body>
    </html>
    """

    CONFIRMATION_TEXT_EN = """
    Dear {guest_name},

    Thank you for responding to our wedding invitation!

    Your Response:
    - Attending: {attending}
    - Dietary Requirements: {dietary}

    We can't wait to celebrate with you!

    With love,
    {couple_names}
    """

    # Spanish templates
    INVITATION_SUBJECT_ES = "¡Estás Invitado a Nuestra Boda!"
    INVITATION_HTML_ES = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #d4a373;">¡Reserva la Fecha!</h1>
        </div>

        <p>Querido/a {guest_name},</p>

        <p>¡Estamos encantados de invitarte a nuestra celebración de boda!</p>

        <div style="background-color: #fefae0; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #bc6c25; margin-top: 0;">Detalles de la Boda</h2>
            <p><strong>Fecha:</strong> {event_date}</p>
            <p><strong>Lugar:</strong> {event_location}</p>
        </div>

        <p>Por favor, haznos saber si puedes asistir haciendo clic en el botón de abajo:</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{rsvp_url}" style="background-color: #d4a373; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-size: 18px;">
                Confirmar Asistencia
            </a>
        </div>

        <p>Si el botón no funciona, puedes copiar y pegar el siguiente enlace en tu navegador:</p>
        <p style="word-break: break-all; color: #606c38;"><a href="{rsvp_url}">{rsvp_url}</a></p>

        <p>Te pedimos amablemente que respondas antes del {response_deadline}.</p>

        <p>¡Esperamos celebrar contigo!</p>

        <p>Con cariño,<br>{couple_names}</p>

        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

        <p style="font-size: 12px; color: #888; text-align: center;">
            Si tienes alguna pregunta, no dudes en contactarnos.
        </p>
    </body>
    </html>
    """

    INVITATION_TEXT_ES = """
    Querido/a {guest_name},

    ¡Estamos encantados de invitarte a nuestra celebración de boda!

    Detalles de la Boda:
    - Fecha: {event_date}
    - Lugar: {event_location}

    Por favor, haznos saber si puedes asistir visitando:
    {rsvp_url}

    Te pedimos amablemente que respondas antes del {response_deadline}.

    ¡Esperamos celebrar contigo!

    Con cariño,
    {couple_names}
    """

    CONFIRMATION_SUBJECT_ES = "¡Gracias por tu Confirmación!"
    CONFIRMATION_HTML_ES = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #d4a373;">¡Gracias!</h1>
        </div>

        <p>Querido/a {guest_name},</p>

        <p>¡Gracias por responder a nuestra invitación de boda!</p>

        <div style="background-color: #fefae0; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #bc6c25; margin-top: 0;">Tu Respuesta</h2>
            <p><strong>Asistencia:</strong> {attending}</p>
            <p><strong>Requisitos Dietéticos:</strong> {dietary}</p>
        </div>

        <p>¡Estamos deseando celebrar contigo!</p>

        <p>Con cariño,<br>{couple_names}</p>
    </body>
    </html>
    """

    CONFIRMATION_TEXT_ES = """
    Querido/a {guest_name},

    ¡Gracias por responder a nuestra invitación de boda!

    Tu Respuesta:
    - Asistencia: {attending}
    - Requisitos Dietéticos: {dietary}

    ¡Estamos deseando celebrar contigo!

    Con cariño,
    {couple_names}
    """

    # Dutch templates
    INVITATION_SUBJECT_NL = "Je Bent Uitgenodigd voor Onze Bruiloft!"
    INVITATION_HTML_NL = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #d4a373;">Save the Date!</h1>
        </div>

        <p>Beste {guest_name},</p>

        <p>We nodigen je van harte uit voor onze bruiloft!</p>

        <div style="background-color: #fefae0; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #bc6c25; margin-top: 0;">Bruiloft Details</h2>
            <p><strong>Datum:</strong> {event_date}</p>
            <p><strong>Locatie:</strong> {event_location}</p>
        </div>

        <p>Laat ons weten of je kunt komen door op de onderstaande knop te klikken:</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{rsvp_url}" style="background-color: #d4a373; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-size: 18px;">
                Bevestig Aanwezigheid
            </a>
        </div>

        <p>Als de knop niet werkt, kun je de volgende link kopiëren en plakken in je browser:</p>
        <p style="word-break: break-all; color: #606c38;"><a href="{rsvp_url}">{rsvp_url}</a></p>

        <p>We vragen je vriendelijk om te reageren voor {response_deadline}.</p>

        <p>We kijken ernaar uit om met je te vieren!</p>

        <p>Met liefde,<br>{couple_names}</p>

        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

        <p style="font-size: 12px; color: #888; text-align: center;">
            Als je vragen hebt, neem dan gerust contact met ons op.
        </p>
    </body>
    </html>
    """

    INVITATION_TEXT_NL = """
    Beste {guest_name},

    We nodigen je van harte uit voor onze bruiloft!

    Bruiloft Details:
    - Datum: {event_date}
    - Locatie: {event_location}

    Laat ons weten of je kunt komen door te bezoeken:
    {rsvp_url}

    We vragen je vriendelijk om te reageren voor {response_deadline}.

    We kijken ernaar uit om met je te vieren!

    Met liefde,
    {couple_names}
    """

    CONFIRMATION_SUBJECT_NL = "Bedankt voor je Reactie!"
    CONFIRMATION_HTML_NL = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #d4a373;">Bedankt!</h1>
        </div>

        <p>Beste {guest_name},</p>

        <p>Bedankt voor je reactie op onze bruiloftuitnodiging!</p>

        <div style="background-color: #fefae0; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #bc6c25; margin-top: 0;">Jouw Reactie</h2>
            <p><strong>Aanwezigheid:</strong> {attending}</p>
            <p><strong>Dieetwensen:</strong> {dietary}</p>
        </div>

        <p>We kunnen niet wachten om met je te vieren!</p>

        <p>Met liefde,<br>{couple_names}</p>
    </body>
    </html>
    """

    CONFIRMATION_TEXT_NL = """
    Beste {guest_name},

    Bedankt voor je reactie op onze bruiloftuitnodiging!

    Jouw Reactie:
    - Aanwezigheid: {attending}
    - Dieetwensen: {dietary}

    We kunnen niet wachten om met je te vieren!

    Met liefde,
    {couple_names}
    """

    # Legacy aliases for backwards compatibility
    INVITATION_SUBJECT = INVITATION_SUBJECT_EN
    INVITATION_HTML = INVITATION_HTML_EN
    INVITATION_TEXT = INVITATION_TEXT_EN
    CONFIRMATION_SUBJECT = CONFIRMATION_SUBJECT_EN
    CONFIRMATION_HTML = CONFIRMATION_HTML_EN
    CONFIRMATION_TEXT = CONFIRMATION_TEXT_EN

    @classmethod
    def get_invitation_templates(cls, language: Language) -> tuple[str, str, str]:
        """Get invitation templates for a specific language.

        Returns: (subject, html_body, text_body)
        """
        lang_suffix = language.value.upper()
        subject = getattr(cls, f"INVITATION_SUBJECT_{lang_suffix}", cls.INVITATION_SUBJECT_EN)
        html = getattr(cls, f"INVITATION_HTML_{lang_suffix}", cls.INVITATION_HTML_EN)
        text = getattr(cls, f"INVITATION_TEXT_{lang_suffix}", cls.INVITATION_TEXT_EN)
        return subject, html, text

    @classmethod
    def get_confirmation_templates(cls, language: Language) -> tuple[str, str, str]:
        """Get confirmation templates for a specific language.

        Returns: (subject, html_body, text_body)
        """
        lang_suffix = language.value.upper()
        subject = getattr(cls, f"CONFIRMATION_SUBJECT_{lang_suffix}", cls.CONFIRMATION_SUBJECT_EN)
        html = getattr(cls, f"CONFIRMATION_HTML_{lang_suffix}", cls.CONFIRMATION_HTML_EN)
        text = getattr(cls, f"CONFIRMATION_TEXT_{lang_suffix}", cls.CONFIRMATION_TEXT_EN)
        return subject, html, text

INVITATION_SUBJECT_EN = "You're Invited to Our Wedding!"
INVITATION_HTML_EN = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@300;400;500&display=swap');
</style>
</head>
<body style="font-family: 'Inter', sans-serif; line-height: 1.6; color: #4a4a4a; background-color: #faf9f6; margin: 0; padding: 0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; padding: 40px 20px;">
    <tr>
        <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <tr>
                    <td style="padding: 40px 40px 20px; text-align: center;">
                        <h1 style="font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 400; color: #c9a66b; margin: 0; letter-spacing: 2px;">SAVE THE DATE</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px 40px;">
                        <p style="font-size: 18px; margin-bottom: 30px;">Dear {guest_name},</p>

                        <p style="margin-bottom: 25px;">We are delighted to invite you to our wedding celebration!</p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; border-radius: 8px; margin: 25px 0;">
                            <tr>
                                <td style="padding: 25px;">
                                    <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 500; color: #8b7355; margin: 0 0 20px 0;">Wedding Details</h2>
                                    <p style="margin: 8px 0;"><strong>Date:</strong> {ceremony_date}</p>
                                    <p style="margin: 8px 0;"><strong>Time:</strong> {ceremony_time}</p>
                                    <p style="margin: 8px 0;"><strong>Venue:</strong> {venue_name}</p>
                                    <a href="{google_maps_url}" style="margin: 8px 0; font-size: 14px; color: #666; text-decoration: underline;">{venue_address}</a>
                                </td>
                            </tr>
                        </table>

                        <p style="margin: 25px 0;">Please let us know if you can attend by clicking the button below:</p>

                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td align="center" style="padding: 25px 0;">
                                    <a href="{rsvp_url}" style="background-color: #c9a66b; color: #ffffff; padding: 16px 36px; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 500; display: inline-block;">RSVP Now</a>
                                </td>
                            </tr>
                        </table>

                        <p style="font-size: 14px; color: #888; margin-top: 20px;">If the button doesn't work, copy this link:<br>
                        <a href="{rsvp_url}" style="color: #c9a66b;">{rsvp_url}</a></p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff5e6; border-radius: 8px; margin: 25px 0; border-left: 4px solid #c9a66b;">
                            <tr>
                                <td style="padding: 20px;">
                                    <p style="margin: 0; font-size: 16px; color: #8b7355;"><strong>Please respond by:</strong> {rsvp_deadline}</p>
                                </td>
                            </tr>
                        </table>

                        <p style="margin-bottom: 5px;">We look forward to celebrating with you!</p>

                        <p style="font-family: 'Cormorant Garamond', serif; font-size: 20px; color: #c9a66b; margin: 20px 0 0;">{couple_names}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px; border-top: 1px solid #e5e5e5; text-align: center;">
                        <p style="font-size: 13px; color: #8b7355; margin: 0 0 5px;">If you have any questions, please contact us at:</p>
                        <p style="font-size: 13px; color: #8b7355; margin: 0;">{contact_email}</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>
"""

INVITATION_TEXT_EN = """Dear {guest_name},

We are delighted to invite you to our wedding celebration!

Wedding Details:
- Date: {ceremony_date}
- Time: {ceremony_time}
- Venue: {venue_name}
- Address: {venue_address}

Please let us know if you can attend by visiting:
{rsvp_url}

We kindly ask that you respond by {rsvp_deadline}.

We look forward to celebrating with you!

With love,
{couple_names}

---
If you have any questions, please contact us at: {contact_email}
Get Directions: {google_maps_url}
"""

CONFIRMATION_SUBJECT_EN = "Thank you for your RSVP!"
CONFIRMATION_HTML_EN = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@300;400;500&display=swap');
</style>
</head>
<body style="font-family: 'Inter', sans-serif; line-height: 1.6; color: #4a4a4a; background-color: #faf9f6; margin: 0; padding: 0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; padding: 40px 20px;">
    <tr>
        <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <tr>
                    <td style="padding: 40px 40px 20px; text-align: center;">
                        <h1 style="font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 400; color: #c9a66b; margin: 0; letter-spacing: 2px;">THANK YOU</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px 40px;">
                        <p style="font-size: 18px; margin-bottom: 30px;">Dear {guest_name},</p>

                        <p style="margin-bottom: 25px;">Thank you for responding to our wedding invitation!</p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; border-radius: 8px; margin: 25px 0;">
                            <tr>
                                <td style="padding: 25px;">
                                    <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 500; color: #8b7355; margin: 0 0 15px 0;">Your Response</h2>
                                    <p style="margin: 8px 0;"><strong>Attending:</strong> {attending}</p>
                                    <p style="margin: 8px 0;"><strong>Dietary Requirements:</strong> {dietary}</p>
                                </td>
                            </tr>
                        </table>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; border-radius: 8px; margin: 25px 0;">
                            <tr>
                                <td style="padding: 25px;">
                                    <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 500; color: #8b7355; margin: 0 0 15px 0;">Wedding Details</h2>
                                    <p style="margin: 8px 0;"><strong>Date:</strong> {ceremony_date}</p>
                                    <p style="margin: 8px 0;"><strong>Time:</strong> {ceremony_time}</p>
                                    <p style="margin: 8px 0;"><strong>Venue:</strong> {venue_name}</p>
                                    <a href="{google_maps_url}" style="margin: 8px 0; font-size: 14px; color: #666; text-decoration: underline;">{venue_address}</a>
                                </td>
                            </tr>
                        </table>

                        <p style="margin-bottom: 5px;">We can't wait to celebrate with you!</p>

                        <p style="font-family: 'Cormorant Garamond', serif; font-size: 20px; color: #c9a66b; margin: 20px 0 0;">{couple_names}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px; border-top: 1px solid #e5e5e5; text-align: center;">
                        <p style="font-size: 13px; color: #8b7355; margin: 0 0 5px;">If you have any questions, please contact us at:</p>
                        <p style="font-size: 13px; color: #8b7355; margin: 0;">{contact_email}</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>
"""

CONFIRMATION_TEXT_EN = """Dear {guest_name},

Thank you for responding to our wedding invitation!

Your Response:
- Attending: {attending}
- Dietary Requirements: {dietary}

Wedding Details:
- Date: {ceremony_date}
- Time: {ceremony_time}
- Venue: {venue_name}
- Address: {venue_address}

We can't wait to celebrate with you!

With love,
{couple_names}

---
If you have any questions, please contact us at: {contact_email}
Get Directions: {google_maps_url}
"""

INVITATION_SUBJECT_ES = "¡Estás Invitado a Nuestra Boda!"
INVITATION_HTML_ES = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@300;400;500&display=swap');
</style>
</head>
<body style="font-family: 'Inter', sans-serif; line-height: 1.6; color: #4a4a4a; background-color: #faf9f6; margin: 0; padding: 0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; padding: 40px 20px;">
    <tr>
        <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <tr>
                    <td style="padding: 40px 40px 20px; text-align: center;">
                        <h1 style="font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 400; color: #c9a66b; margin: 0; letter-spacing: 2px;">RESERVA LA FECHA</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px 40px;">
                        <p style="font-size: 18px; margin-bottom: 30px;">Querido/a {guest_name},</p>

                        <p style="margin-bottom: 25px;">¡Estamos encantados de invitarte a nuestra celebración de boda!</p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; border-radius: 8px; margin: 25px 0;">
                            <tr>
                                <td style="padding: 25px;">
                                    <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 500; color: #8b7355; margin: 0 0 20px 0;">Detalles de la Boda</h2>
                                    <p style="margin: 8px 0;"><strong>Fecha:</strong> {ceremony_date}</p>
                                    <p style="margin: 8px 0;"><strong>Hora:</strong> {ceremony_time}</p>
                                    <p style="margin: 8px 0;"><strong>Lugar:</strong> {venue_name}</p>
                                    <a href="{google_maps_url}" style="margin: 8px 0; font-size: 14px; color: #666; text-decoration: underline;">{venue_address}</a>
                                </td>
                            </tr>
                        </table>

                        <p style="margin: 25px 0;">Por favor, haznos saber si puedes asistir haciendo clic en el botón de abajo:</p>

                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td align="center" style="padding: 25px 0;">
                                    <a href="{rsvp_url}" style="background-color: #c9a66b; color: #ffffff; padding: 16px 36px; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 500; display: inline-block;">Confirmar Asistencia</a>
                                </td>
                            </tr>
                        </table>

                        <p style="font-size: 14px; color: #888; margin-top: 20px;">Si el botón no funciona, copia este enlace:<br>
                        <a href="{rsvp_url}" style="color: #c9a66b;">{rsvp_url}</a></p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff5e6; border-radius: 8px; margin: 25px 0; border-left: 4px solid #c9a66b;">
                            <tr>
                                <td style="padding: 20px;">
                                    <p style="margin: 0; font-size: 16px; color: #8b7355;"><strong>Por favor, responde antes del:</strong> {rsvp_deadline}</p>
                                </td>
                            </tr>
                        </table>

                        <p style="margin-bottom: 5px;">¡ esperamos celebrar contigo!</p>

                        <p style="font-family: 'Cormorant Garamond', serif; font-size: 20px; color: #c9a66b; margin: 20px 0 0;">{couple_names}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px; border-top: 1px solid #e5e5e5; text-align: center;">
                        <p style="font-size: 13px; color: #8b7355; margin: 0 0 5px;">Si tienes alguna pregunta, por favor contáctanos en:</p>
                        <p style="font-size: 13px; color: #8b7355; margin: 0;">{contact_email}</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>
"""

INVITATION_TEXT_ES = """Querido/a {guest_name},

¡Estamos encantado de invitarte a nuestra celebración de boda!

Detalles de la Boda:
- Fecha: {ceremony_date}
- Hora: {ceremony_time}
- Lugar: {venue_name}
- Dirección: {venue_address}

Por favor, haznos saber si puedes asistir visitando:
{rsvp_url}

Te pedimos amablemente que respondas antes del {rsvp_deadline}.

¡ esperamos celebrar contigo!

Con cariño,
{couple_names}

---
Si tienes alguna pregunta, por favor contáctanos en: {contact_email}
Cómo Llegar: {google_maps_url}
"""

CONFIRMATION_SUBJECT_ES = "¡Gracias por tu Confirmación!"
CONFIRMATION_HTML_ES = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@300;400;500&display=swap');
</style>
</head>
<body style="font-family: 'Inter', sans-serif; line-height: 1.6; color: #4a4a4a; background-color: #faf9f6; margin: 0; padding: 0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; padding: 40px 20px;">
    <tr>
        <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <tr>
                    <td style="padding: 40px 40px 20px; text-align: center;">
                        <h1 style="font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 400; color: #c9a66b; margin: 0; letter-spacing: 2px;">GRACIAS</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px 40px;">
                        <p style="font-size: 18px; margin-bottom: 30px;">Querido/a {guest_name},</p>

                        <p style="margin-bottom: 25px;">¡Gracias por responder a nuestra invitación de boda!</p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; border-radius: 8px; margin: 25px 0;">
                            <tr>
                                <td style="padding: 25px;">
                                    <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 500; color: #8b7355; margin: 0 0 15px 0;">Tu Respuesta</h2>
                                    <p style="margin: 8px 0;"><strong>Asistencia:</strong> {attending}</p>
                                    <p style="margin: 8px 0;"><strong>Requisitos Dietéticos:</strong> {dietary}</p>
                                </td>
                            </tr>
                        </table>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; border-radius: 8px; margin: 25px 0;">
                            <tr>
                                <td style="padding: 25px;">
                                    <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 500; color: #8b7355; margin: 0 0 15px 0;">Detalles de la Boda</h2>
                                    <p style="margin: 8px 0;"><strong>Fecha:</strong> {ceremony_date}</p>
                                    <p style="margin: 8px 0;"><strong>Hora:</strong> {ceremony_time}</p>
                                    <p style="margin: 8px 0;"><strong>Lugar:</strong> {venue_name}</p>
                                    <a href="{google_maps_url}" style="margin: 8px 0; font-size: 14px; color: #666; text-decoration: underline;">{venue_address}</a>
                                </td>
                            </tr>
                        </table>

                        <p style="margin-bottom: 5px;">¡Estamos deseando celebrar contigo!</p>

                        <p style="font-family: 'Cormorant Garamond', serif; font-size: 20px; color: #c9a66b; margin: 20px 0 0;">{couple_names}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px; border-top: 1px solid #e5e5e5; text-align: center;">
                        <p style="font-size: 13px; color: #8b7355; margin: 0 0 5px;">Si tienes alguna pregunta, por favor contáctanos en:</p>
                        <p style="font-size: 13px; color: #8b7355; margin: 0;">{contact_email}</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>
"""

CONFIRMATION_TEXT_ES = """Querido/a {guest_name},

¡Gracias por responder a nuestra invitación de boda!

Tu Respuesta:
- Asistencia: {attending}
- Requisitos Dietéticos: {dietary}

Detalles de la Boda:
- Fecha: {ceremony_date}
- Hora: {ceremony_time}
- Lugar: {venue_name}
- Dirección: {venue_address}

¡Estamos deseando celebrar contigo!

Con cariño,
{couple_names}

---
Si tienes alguna pregunta, por favor contáctanos en: {contact_email}
Cómo Llegar: {google_maps_url}
"""

INVITATION_SUBJECT_NL = "Je Bent Uitgenodigd voor Onze Bruiloft!"
INVITATION_HTML_NL = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@300;400;500&display=swap');
</style>
</head>
<body style="font-family: 'Inter', sans-serif; line-height: 1.6; color: #4a4a4a; background-color: #faf9f6; margin: 0; padding: 0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; padding: 40px 20px;">
    <tr>
        <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <tr>
                    <td style="padding: 40px 40px 20px; text-align: center;">
                        <h1 style="font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 400; color: #c9a66b; margin: 0; letter-spacing: 2px;">SAVE THE DATE</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px 40px;">
                        <p style="font-size: 18px; margin-bottom: 30px;">Beste {guest_name},</p>

                        <p style="margin-bottom: 25px;">We nodigen je van harte uit voor onze bruiloft!</p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; border-radius: 8px; margin: 25px 0;">
                            <tr>
                                <td style="padding: 25px;">
                                    <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 500; color: #8b7355; margin: 0 0 20px 0;">Bruiloft Details</h2>
                                    <p style="margin: 8px 0;"><strong>Datum:</strong> {ceremony_date}</p>
                                    <p style="margin: 8px 0;"><strong>Tijd:</strong> {ceremony_time}</p>
                                    <p style="margin: 8px 0;"><strong>Locatie:</strong> {venue_name}</p>
                                    <a href="{google_maps_url}" style="margin: 8px 0; font-size: 14px; color: #666; text-decoration: underline;">{venue_address}</a>
                                </td>
                            </tr>
                        </table>

                        <p style="margin: 25px 0;">Laat ons weten of je kunt komen door op de onderstaande knop te klikken:</p>

                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td align="center" style="padding: 25px 0;">
                                    <a href="{rsvp_url}" style="background-color: #c9a66b; color: #ffffff; padding: 16px 36px; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 500; display: inline-block;">Bevestig Aanwezigheid</a>
                                </td>
                            </tr>
                        </table>

                        <p style="font-size: 14px; color: #888; margin-top: 20px;">Als de knop niet werkt, kopieer deze link:<br>
                        <a href="{rsvp_url}" style="color: #c9a66b;">{rsvp_url}</a></p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff5e6; border-radius: 8px; margin: 25px 0; border-left: 4px solid #c9a66b;">
                            <tr>
                                <td style="padding: 20px;">
                                    <p style="margin: 0; font-size: 16px; color: #8b7355;"><strong>Graag reageren voor:</strong> {rsvp_deadline}</p>
                                </td>
                            </tr>
                        </table>

                        <p style="margin-bottom: 5px;">We kijken ernaar uit om met je te vieren!</p>

                        <p style="font-family: 'Cormorant Garamond', serif; font-size: 20px; color: #c9a66b; margin: 20px 0 0;">{couple_names}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px; border-top: 1px solid #e5e5e5; text-align: center;">
                        <p style="font-size: 13px; color: #8b7355; margin: 0 0 5px;">Als je vragen hebt, neem dan contact met ons op via:</p>
                        <p style="font-size: 13px; color: #8b7355; margin: 0;">{contact_email}</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>
"""

INVITATION_TEXT_NL = """Beste {guest_name},

We nodigen je van harte uit voor onze bruiloft!

Bruiloft Details:
- Datum: {ceremony_date}
- Tijd: {ceremony_time}
- Locatie: {venue_name}
- Adres: {venue_address}

Laat ons weten of je kunt komen door te bezoeken:
{rsvp_url}

We vragen je vriendelijk om te reageren voor {rsvp_deadline}.

We kijken ernaar uit om met je te vieren!

Met liefde,
{couple_names}

---
Als je vragen hebt, neem dan contact met ons op via: {contact_email}
Routebeschrijving: {google_maps_url}
"""

CONFIRMATION_SUBJECT_NL = "Bedankt voor je Reactie!"
CONFIRMATION_HTML_NL = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@300;400;500&display=swap');
</style>
</head>
<body style="font-family: 'Inter', sans-serif; line-height: 1.6; color: #4a4a4a; background-color: #faf9f6; margin: 0; padding: 0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; padding: 40px 20px;">
    <tr>
        <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <tr>
                    <td style="padding: 40px 40px 20px; text-align: center;">
                        <h1 style="font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 400; color: #c9a66b; margin: 0; letter-spacing: 2px;">BEDANKT</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px 40px;">
                        <p style="font-size: 18px; margin-bottom: 30px;">Beste {guest_name},</p>

                        <p style="margin-bottom: 25px;">Bedankt voor je reactie op onze bruiloftuitnodiging!</p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; border-radius: 8px; margin: 25px 0;">
                            <tr>
                                <td style="padding: 25px;">
                                    <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 500; color: #8b7355; margin: 0 0 15px 0;">Jouw Reactie</h2>
                                    <p style="margin: 8px 0;"><strong>Aanwezigheid:</strong> {attending}</p>
                                    <p style="margin: 8px 0;"><strong>Dieetwensen:</strong> {dietary}</p>
                                </td>
                            </tr>
                        </table>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; border-radius: 8px; margin: 25px 0;">
                            <tr>
                                <td style="padding: 25px;">
                                    <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 500; color: #8b7355; margin: 0 0 15px 0;">Bruiloft Details</h2>
                                    <p style="margin: 8px 0;"><strong>Datum:</strong> {ceremony_date}</p>
                                    <p style="margin: 8px 0;"><strong>Tijd:</strong> {ceremony_time}</p>
                                    <p style="margin: 8px 0;"><strong>Locatie:</strong> {venue_name}</p>
                                    <a href="{google_maps_url}" style="margin: 8px 0; font-size: 14px; color: #666; text-decoration: underline;">{venue_address}</a>
                                </td>
                            </tr>
                        </table>

                        <p style="margin-bottom: 5px;">We kunnen niet wachten om met je te vieren!</p>

                        <p style="font-family: 'Cormorant Garamond', serif; font-size: 20px; color: #c9a66b; margin: 20px 0 0;">{couple_names}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px; border-top: 1px solid #e5e5e5; text-align: center;">
                        <p style="font-size: 13px; color: #8b7355; margin: 0 0 5px;">Als je vragen hebt, neem dan contact met ons op via:</p>
                        <p style="font-size: 13px; color: #8b7355; margin: 0;">{contact_email}</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>
"""

CONFIRMATION_TEXT_NL = """Beste {guest_name},

Bedankt voor je reactie op onze bruiloftuitnodiging!

Jouw Reactie:
- Aanwezigheid: {attending}
- Dieetwensen: {dietary}

Bruiloft Details:
- Datum: {ceremony_date}
- Tijd: {ceremony_time}
- Locatie: {venue_name}
- Adres: {venue_address}

We kunnen niet wachten om met je te vieren!

Met liefde,
{couple_names}

---
Als je vragen hebt, neem dan contact met ons op via: {contact_email}
Routebeschrijving: {google_maps_url}
"""

PLUS_ONE_INVITATION_SUBJECT_EN = "You're Invited to Our Wedding!"
PLUS_ONE_INVITATION_HTML_EN = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@300;400;500&display=swap');
</style>
</head>
<body style="font-family: 'Inter', sans-serif; line-height: 1.6; color: #4a4a4a; background-color: #faf9f6; margin: 0; padding: 0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; padding: 40px 20px;">
    <tr>
        <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <tr>
                    <td style="padding: 40px 40px 20px; text-align: center;">
                        <h1 style="font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 400; color: #c9a66b; margin: 0; letter-spacing: 2px;">SPECIAL INVITATION</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px 40px;">
                        <p style="font-size: 18px; margin-bottom: 30px;">Dear {guest_name},</p>

                        <p style="margin-bottom: 25px;"><strong>{inviter_name}</strong> has invited you as their plus-one to our wedding celebration!</p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; border-radius: 8px; margin: 25px 0;">
                            <tr>
                                <td style="padding: 25px;">
                                    <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 500; color: #8b7355; margin: 0 0 20px 0;">Wedding Details</h2>
                                    <p style="margin: 8px 0;"><strong>Date:</strong> {ceremony_date}</p>
                                    <p style="margin: 8px 0;"><strong>Time:</strong> {ceremony_time}</p>
                                    <p style="margin: 8px 0;"><strong>Venue:</strong> {venue_name}</p>
                                    <a href="{google_maps_url}" style="margin: 8px 0; font-size: 14px; color: #666; text-decoration: underline;">{venue_address}</a>
                                </td>
                            </tr>
                        </table>

                        <p style="margin: 25px 0;">Please let us know if you can attend by clicking the button below:</p>

                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td align="center" style="padding: 25px 0;">
                                    <a href="{rsvp_url}" style="background-color: #c9a66b; color: #ffffff; padding: 16px 36px; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 500; display: inline-block;">RSVP Now</a>
                                </td>
                            </tr>
                        </table>

                        <p style="font-size: 14px; color: #888; margin-top: 20px;">If the button doesn't work, copy this link:<br>
                        <a href="{rsvp_url}" style="color: #c9a66b;">{rsvp_url}</a></p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff5e6; border-radius: 8px; margin: 25px 0; border-left: 4px solid #c9a66b;">
                            <tr>
                                <td style="padding: 20px;">
                                    <p style="margin: 0; font-size: 16px; color: #8b7355;"><strong>Please respond by:</strong> {rsvp_deadline}</p>
                                </td>
                            </tr>
                        </table>

                        <p style="margin-bottom: 5px;">We look forward to celebrating with you!</p>

                        <p style="font-family: 'Cormorant Garamond', serif; font-size: 20px; color: #c9a66b; margin: 20px 0 0;">{couple_names}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px; border-top: 1px solid #e5e5e5; text-align: center;">
                        <p style="font-size: 13px; color: #8b7355; margin: 0 0 5px;">If you have any questions, please contact us at:</p>
                        <p style="font-size: 13px; color: #8b7355; margin: 0;">{contact_email}</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>
"""

PLUS_ONE_INVITATION_TEXT_EN = """Dear {guest_name},

{inviter_name} has invited you as their plus-one to our wedding celebration!

Wedding Details:
- Date: {ceremony_date}
- Time: {ceremony_time}
- Venue: {venue_name}
- Address: {venue_address}

Please let us know if you can attend by visiting:
{rsvp_url}

We kindly ask that you respond by {rsvp_deadline}.

We look forward to celebrating with you!

With love,
{couple_names}

---
If you have any questions, please contact us at: {contact_email}
Get Directions: {google_maps_url}
"""

PLUS_ONE_INVITATION_SUBJECT_ES = "¡Estás Invitado a Nuestra Boda!"
PLUS_ONE_INVITATION_HTML_ES = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@300;400;500&display=swap');
</style>
</head>
<body style="font-family: 'Inter', sans-serif; line-height: 1.6; color: #4a4a4a; background-color: #faf9f6; margin: 0; padding: 0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; padding: 40px 20px;">
    <tr>
        <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <tr>
                    <td style="padding: 40px 40px 20px; text-align: center;">
                        <h1 style="font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 400; color: #c9a66b; margin: 0; letter-spacing: 2px;">INVITACIÓN ESPECIAL</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px 40px;">
                        <p style="font-size: 18px; margin-bottom: 30px;">Querido/a {guest_name},</p>

                        <p style="margin-bottom: 25px;"><strong>{inviter_name}</strong> te ha invitado como su acompañante a nuestra celebración de boda!</p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; border-radius: 8px; margin: 25px 0;">
                            <tr>
                                <td style="padding: 25px;">
                                    <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 500; color: #8b7355; margin: 0 0 20px 0;">Detalles de la Boda</h2>
                                    <p style="margin: 8px 0;"><strong>Fecha:</strong> {ceremony_date}</p>
                                    <p style="margin: 8px 0;"><strong>Hora:</strong> {ceremony_time}</p>
                                    <p style="margin: 8px 0;"><strong>Lugar:</strong> {venue_name}</p>
                                    <a href="{google_maps_url}" style="margin: 8px 0; font-size: 14px; color: #666; text-decoration: underline;">{venue_address}</a>
                                </td>
                            </tr>
                        </table>

                        <p style="margin: 25px 0;">Por favor, haznos saber si puedes asistir haciendo clic en el botón de abajo:</p>

                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td align="center" style="padding: 25px 0;">
                                    <a href="{rsvp_url}" style="background-color: #c9a66b; color: #ffffff; padding: 16px 36px; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 500; display: inline-block;">Confirmar Asistencia</a>
                                </td>
                            </tr>
                        </table>

                        <p style="font-size: 14px; color: #888; margin-top: 20px;">Si el botón no funciona, copia este enlace:<br>
                        <a href="{rsvp_url}" style="color: #c9a66b;">{rsvp_url}</a></p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff5e6; border-radius: 8px; margin: 25px 0; border-left: 4px solid #c9a66b;">
                            <tr>
                                <td style="padding: 20px;">
                                    <p style="margin: 0; font-size: 16px; color: #8b7355;"><strong>Por favor, responde antes del:</strong> {rsvp_deadline}</p>
                                </td>
                            </tr>
                        </table>

                        <p style="margin-bottom: 5px;">¡ esperamos celebrate contigo!</p>

                        <p style="font-family: 'Cormorant Garamond', serif; font-size: 20px; color: #c9a66b; margin: 20px 0 0;">{couple_names}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px; border-top: 1px solid #e5e5e5; text-align: center;">
                        <p style="font-size: 13px; color: #8b7355; margin: 0 0 5px;">Si tienes alguna pregunta, por favor contáctanos en:</p>
                        <p style="font-size: 13px; color: #8b7355; margin: 0;">{contact_email}</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>
"""

PLUS_ONE_INVITATION_TEXT_ES = """Querido/a {guest_name},

{inviter_name} te ha invitado como su accompagnante a nuestra celebración de boda!

Detalles de la Boda:
- Fecha: {ceremony_date}
- Hora: {ceremony_time}
- Lugar: {venue_name}
- Dirección: {venue_address}

Por favor, haznos saber si puedes asistir visitando:
{rsvp_url}

Te pedimos amablemente que respondas antes del {rsvp_deadline}.

¡ esperamos celebrate contigo!

Con cariño,
{couple_names}

---
Si tienes alguna pregunta, por favor contáctanos en: {contact_email}
Cómo Llegar: {google_maps_url}
"""

PLUS_ONE_INVITATION_SUBJECT_NL = "Je Bent Uitgenodigd voor Onze Bruiloft!"
PLUS_ONE_INVITATION_HTML_NL = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Inter:wght@300;400;500&display=swap');
</style>
</head>
<body style="font-family: 'Inter', sans-serif; line-height: 1.6; color: #4a4a4a; background-color: #faf9f6; margin: 0; padding: 0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; padding: 40px 20px;">
    <tr>
        <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <tr>
                    <td style="padding: 40px 40px 20px; text-align: center;">
                        <h1 style="font-family: 'Cormorant Garamond', serif; font-size: 36px; font-weight: 400; color: #c9a66b; margin: 0; letter-spacing: 2px;">SPECIALE UITNODIGING</h1>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px 40px;">
                        <p style="font-size: 18px; margin-bottom: 30px;">Beste {guest_name},</p>

                        <p style="margin-bottom: 25px;"><strong>{inviter_name}</strong> heeft je uitgenodigd als hun plus-één voor onze bruiloft!</p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #faf9f6; border-radius: 8px; margin: 25px 0;">
                            <tr>
                                <td style="padding: 25px;">
                                    <h2 style="font-family: 'Cormorant Garamond', serif; font-size: 22px; font-weight: 500; color: #8b7355; margin: 0 0 20px 0;">Bruiloft Details</h2>
                                    <p style="margin: 8px 0;"><strong>Datum:</strong> {ceremony_date}</p>
                                    <p style="margin: 8px 0;"><strong>Tijd:</strong> {ceremony_time}</p>
                                    <p style="margin: 8px 0;"><strong>Locatie:</strong> {venue_name}</p>
                                    <a href="{google_maps_url}" style="margin: 8px 0; font-size: 14px; color: #666; text-decoration: underline;">{venue_address}</a>
                                </td>
                            </tr>
                        </table>

                        <p style="margin: 25px 0;">Laat ons weten of je kunt komen door op de onderstaande knop te klikken:</p>

                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td align="center" style="padding: 25px 0;">
                                    <a href="{rsvp_url}" style="background-color: #c9a66b; color: #ffffff; padding: 16px 36px; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 500; display: inline-block;">Bevestig Aanwezigheid</a>
                                </td>
                            </tr>
                        </table>

                        <p style="font-size: 14px; color: #888; margin-top: 20px;">Als de knop niet werkt, kopieer deze link:<br>
                        <a href="{rsvp_url}" style="color: #c9a66b;">{rsvp_url}</a></p>

                        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff5e6; border-radius: 8px; margin: 25px 0; border-left: 4px solid #c9a66b;">
                            <tr>
                                <td style="padding: 20px;">
                                    <p style="margin: 0; font-size: 16px; color: #8b7355;"><strong>Graag reageren voor:</strong> {rsvp_deadline}</p>
                                </td>
                            </tr>
                        </table>

                        <p style="margin-bottom: 5px;">We kijken ernaar uit om met je te vieren!</p>

                        <p style="font-family: 'Cormorant Garamond', serif; font-size: 20px; color: #c9a66b; margin: 20px 0 0;">{couple_names}</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px 40px; border-top: 1px solid #e5e5e5; text-align: center;">
                        <p style="font-size: 13px; color: #8b7355; margin: 0 0 5px;">Als je vragen hebt, neem dan contact met ons op via:</p>
                        <p style="font-size: 13px; color: #8b7355; margin: 0;">{contact_email}</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>
"""

PLUS_ONE_INVITATION_TEXT_NL = """Beste {guest_name},

{inviter_name} heeft je uitgenodigd als hun plus-één voor onze bruiloft!

Bruiloft Details:
- Datum: {ceremony_date}
- Tijd: {ceremony_time}
- Locatie: {venue_name}
- Adres: {venue_address}

Laat ons weten of je kunt komen door te bezoeken:
{rsvp_url}

We vragen je vriendelijk om te reageren voor {rsvp_deadline}.

We kijken ernaar uit om met je te vieren!

Met liefde,
{couple_names}

---
Als je vragen hebt, neem dan contact met ons op via: {contact_email}
Routebeschrijving: {google_maps_url}
"""

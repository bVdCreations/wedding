from dataclasses import dataclass


@dataclass
class EmailTemplates:
    INVITATION_SUBJECT = "You're Invited to Our Wedding!"
    INVITATION_HTML = """
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

    INVITATION_TEXT = """
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

    CONFIRMATION_SUBJECT = "Thank you for your RSVP!"
    CONFIRMATION_HTML = """
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

    CONFIRMATION_TEXT = """
    Dear {guest_name},

    Thank you for responding to our wedding invitation!

    Your Response:
    - Attending: {attending}
    - Dietary Requirements: {dietary}

    We can't wait to celebrate with you!

    With love,
    {couple_names}
    """

"""CLI commands for wedding RSVP management."""

import asyncio

import typer

from src.email.service import email_service
from src.guests.features.create_guest.write_model import SqlGuestCreateWriteModel

app = typer.Typer(help="CLI commands for wedding RSVP management")


async def _create_guest_and_send_email():
    """Async helper to create guest and send email."""
    # Hardcoded test data
    email = "test@guest.example"
    first_name = "Test"
    last_name = "Guest"

    # Create guest
    write_model = SqlGuestCreateWriteModel()
    guest = await write_model.create_guest(
        email=email,
        first_name=first_name,
        last_name=last_name,
    )

    # Send invitation email
    await email_service.send_invitation(
        to_address=email,
        guest_name=f"{first_name} {last_name}",
        event_date="August 15, 2026",
        event_location="Castillo de Example, Spain",
        rsvp_url=guest.rsvp.link,
        response_deadline="July 15, 2026",
        couple_names="Alex & Sam",
    )

    return guest


@app.command()
def create_guest():
    """Create a dummy guest and send invitation email to Mailhog."""
    # Typer doesn't support async directly, so use asyncio.run
    guest = asyncio.run(_create_guest_and_send_email())

    # Output results
    typer.secho("Guest created successfully!", fg=typer.colors.GREEN)
    typer.secho("Email: test@guest.example", fg=typer.colors.BLUE)
    typer.secho(f"RSVP URL: {guest.rsvp.link}", fg=typer.colors.CYAN)
    typer.secho(f"RSVP Token: {guest.rsvp.token}", fg=typer.colors.CYAN)
    typer.secho("Email sent to Mailhog!", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()

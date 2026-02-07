"""CLI commands for wedding RSVP management."""

import asyncio

import typer

from src.email.service import email_service
from src.guests.dtos import PlusOneDTO
from src.guests.features.create_guest.write_model import SqlGuestCreateWriteModel
from src.guests.features.create_plus_one_guest.write_model import SqlPlusOneGuestWriteModel

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


async def _create_plus_one_guest(
    original_email: str,
    plus_one_email: str,
    plus_one_first_name: str,
    plus_one_last_name: str,
):
    """Async helper to create an original guest and their plus-one."""
    # First create the original guest
    guest_write_model = SqlGuestCreateWriteModel()
    original_guest = await guest_write_model.create_guest(
        email=original_email,
        first_name="Original",
        last_name="Guest",
    )

    # Create plus-one guest linked to the original
    plus_one_write_model = SqlPlusOneGuestWriteModel()
    plus_one_data = PlusOneDTO(
        email=plus_one_email,
        first_name=plus_one_first_name,
        last_name=plus_one_last_name,
    )
    plus_one_guest = await plus_one_write_model.create_plus_one_guest(
        original_guest_user_id=original_guest.id,
        plus_one_data=plus_one_data,
    )

    return original_guest, plus_one_guest


@app.command()
def create_plus_one(
    original_email: str = typer.Option(
        "original@guest.example",
        "--original-email",
        "-o",
        help="Email for the original guest",
    ),
    plus_one_email: str = typer.Option(
        "plusone@guest.example",
        "--plus-one-email",
        "-p",
        help="Email for the plus-one guest",
    ),
    first_name: str = typer.Option(
        "Plus",
        "--first-name",
        "-f",
        help="First name of the plus-one",
    ),
    last_name: str = typer.Option(
        "One",
        "--last-name",
        "-l",
        help="Last name of the plus-one",
    ),
):
    """Create an original guest and a plus-one guest linked to them."""
    original_guest, plus_one_guest = asyncio.run(
        _create_plus_one_guest(
            original_email=original_email,
            plus_one_email=plus_one_email,
            plus_one_first_name=first_name,
            plus_one_last_name=last_name,
        )
    )

    # Output results
    typer.secho("Original guest created!", fg=typer.colors.GREEN)
    typer.secho(f"  Email: {original_email}", fg=typer.colors.BLUE)
    typer.secho(f"  RSVP URL: {original_guest.rsvp.link}", fg=typer.colors.CYAN)
    typer.secho(f"  RSVP Token: {original_guest.rsvp.token}", fg=typer.colors.CYAN)

    typer.echo()
    typer.secho("Plus-one guest created!", fg=typer.colors.GREEN)
    typer.secho(f"  Email: {plus_one_email}", fg=typer.colors.BLUE)
    typer.secho(f"  Name: {first_name} {last_name}", fg=typer.colors.BLUE)
    typer.secho(f"  RSVP URL: {plus_one_guest.rsvp.link}", fg=typer.colors.CYAN)
    typer.secho(f"  RSVP Token: {plus_one_guest.rsvp.token}", fg=typer.colors.CYAN)
    typer.secho(f"  Linked to original guest ID: {original_guest.id}", fg=typer.colors.MAGENTA)


if __name__ == "__main__":
    app()

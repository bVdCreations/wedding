"""CLI commands for wedding RSVP management."""

import asyncio
from uuid import UUID

import typer
from sqlalchemy import select

from src.config.database import async_session_manager
from src.email.service import email_service
from src.guests.dtos import PlusOneDTO
from src.guests.features.create_guest.write_model import SqlGuestCreateWriteModel
from src.guests.features.create_child_guest.write_model import SqlChildGuestCreateWriteModel
from src.guests.features.create_plus_one_guest.write_model import SqlPlusOneGuestWriteModel
from src.guests.repository.orm_models import Family, Guest
from src.models.user import User

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


# Family management commands


async def _get_guest_by_id(guest_id: UUID) -> Guest | None:
    """Get a guest by ID."""
    async with async_session_manager() as session:
        stmt = select(Guest).where(Guest.uuid == guest_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


@app.command()
def create_family(
    name: str = typer.Option(
        None,
        "--name",
        "-n",
        help="Optional family name",
    ),
    guests: list[str] = typer.Option(
        [],
        "--guest",
        "-g",
        help="Guest UUIDs to add to the family",
    ),
):
    """Create a new family and optionally add guests to it."""
    async def _create_family():
        async with async_session_manager() as session:
            # Create family
            family = Family(name=name)
            session.add(family)
            await session.flush()  # Get the UUID

            # Add guests to family if specified
            added_guests = []
            for guest_id_str in guests:
                guest_id = UUID(guest_id_str)
                stmt = select(Guest).where(Guest.uuid == guest_id)
                result = await session.execute(stmt)
                guest = result.scalar_one_or_none()
                if guest:
                    guest.family_id = family.uuid
                    added_guests.append(f"{guest.first_name} {guest.last_name}")
                else:
                    typer.secho(f"  Guest not found: {guest_id}", fg=typer.colors.RED)

            await session.commit()
            return family, added_guests

    family, added_guests = asyncio.run(_create_family())

    typer.secho("Family created!", fg=typer.colors.GREEN)
    typer.secho(f"  Family ID: {family.uuid}", fg=typer.colors.CYAN)
    if name:
        typer.secho(f"  Family Name: {name}", fg=typer.colors.BLUE)
    if added_guests:
        typer.echo()
        typer.secho("Added guests:", fg=typer.colors.GREEN)
        for guest_name in added_guests:
            typer.secho(f"  - {guest_name}", fg=typer.colors.BLUE)


@app.command()
def add_to_family(
    family_id: str = typer.Argument(
        ...,
        help="Family UUID",
    ),
    guest_id: str = typer.Argument(
        ...,
        help="Guest UUID to add to the family",
    ),
):
    """Add an existing guest to a family."""
    async def _add_to_family():
        async with async_session_manager() as session:
            # Get family
            stmt = select(Family).where(Family.uuid == UUID(family_id))
            result = await session.execute(stmt)
            family = result.scalar_one_or_none()
            if not family:
                raise ValueError(f"Family not found: {family_id}")

            # Get guest
            stmt = select(Guest).where(Guest.uuid == UUID(guest_id))
            result = await session.execute(stmt)
            guest = result.scalar_one_or_none()
            if not guest:
                raise ValueError(f"Guest not found: {guest_id}")

            # Update guest's family_id
            old_family_id = guest.family_id
            guest.family_id = family.uuid
            await session.commit()

            return family, guest, old_family_id

    try:
        family, guest, old_family_id = asyncio.run(_add_to_family())

        typer.secho("Guest added to family!", fg=typer.colors.GREEN)
        typer.secho(f"  Guest: {guest.first_name} {guest.last_name}", fg=typer.colors.BLUE)
        typer.secho(f"  Family ID: {family.uuid}", fg=typer.colors.CYAN)
        if old_family_id:
            typer.secho(f"  (Removed from previous family: {old_family_id})", fg=typer.colors.YELLOW)
    except ValueError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def link_guests(
    guest_id_1: str = typer.Argument(
        ...,
        help="First guest UUID",
    ),
    guest_id_2: str = typer.Argument(
        ...,
        help="Second guest UUID",
    ),
    family_name: str = typer.Option(
        None,
        "--name",
        "-n",
        help="Optional family name",
    ),
):
    """Link two guests together as a family (creates new family if needed)."""
    async def _link_guests():
        async with async_session_manager() as session:
            # Get first guest
            stmt = select(Guest).where(Guest.uuid == UUID(guest_id_1))
            result = await session.execute(stmt)
            guest1 = result.scalar_one_or_none()
            if not guest1:
                raise ValueError(f"Guest not found: {guest_id_1}")

            # Get second guest
            stmt = select(Guest).where(Guest.uuid == UUID(guest_id_2))
            result = await session.execute(stmt)
            guest2 = result.scalar_one_or_none()
            if not guest2:
                raise ValueError(f"Guest not found: {guest_id_2}")

            # Check if either guest is already in a family
            if guest1.family_id and guest2.family_id and guest1.family_id != guest2.family_id:
                raise ValueError(
                    f"Guests are already in different families. "
                    f"Remove them from their current families first."
                )

            # Use existing family or create new one
            if guest1.family_id:
                family_id = guest1.family_id
            elif guest2.family_id:
                family_id = guest2.family_id
            else:
                # Create new family
                family = Family(name=family_name)
                session.add(family)
                await session.flush()
                family_id = family.uuid

            # Update both guests
            guest1.family_id = family_id
            guest2.family_id = family_id
            await session.commit()

            return guest1, guest2, family_id

    try:
        guest1, guest2, family_id = asyncio.run(_link_guests())

        typer.secho("Guests linked!", fg=typer.colors.GREEN)
        typer.secho(f"  {guest1.first_name} {guest1.last_name}", fg=typer.colors.BLUE)
        typer.secho(f"  {guest2.first_name} {guest2.last_name}", fg=typer.colors.BLUE)
        typer.secho(f"  Family ID: {family_id}", fg=typer.colors.CYAN)
    except ValueError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def show_family(
    guest_id: str = typer.Argument(
        ...,
        help="Guest UUID to show family for",
    ),
):
    """Show family details for a guest."""
    async def _show_family():
        async with async_session_manager() as session:
            # Get guest
            stmt = select(Guest).where(Guest.uuid == UUID(guest_id))
            result = await session.execute(stmt)
            guest = result.scalar_one_or_none()
            if not guest:
                raise ValueError(f"Guest not found: {guest_id}")

            # Get family if exists
            family = None
            family_members = []
            if guest.family_id:
                stmt = select(Family).where(Family.uuid == guest.family_id)
                result = await session.execute(stmt)
                family = result.scalar_one_or_none()

                # Get all family members
                stmt = (
                    select(Guest)
                    .where(Guest.family_id == guest.family_id)
                    .order_by(Guest.first_name)
                )
                result = await session.execute(stmt)
                family_members = result.scalars().all()

            return guest, family, family_members

    try:
        guest, family, family_members = asyncio.run(_show_family())

        typer.secho("Guest Info", fg=typer.colors.GREEN)
        typer.secho(f"  Name: {guest.first_name} {guest.last_name}", fg=typer.colors.BLUE)
        typer.secho(f"  ID: {guest.uuid}", fg=typer.colors.CYAN)
        typer.secho(f"  Guest Type: {getattr(guest, 'guest_type', 'adult')}", fg=typer.colors.MAGENTA)
        typer.secho(f"  Email: {guest.phone or 'N/A'}", fg=typer.colors.BLUE)

        if family:
            typer.echo()
            typer.secho(f"Family: {family.name or family.uuid}", fg=typer.colors.GREEN)
            typer.secho(f"  Family ID: {family.uuid}", fg=typer.colors.CYAN)
            typer.echo()
            typer.secho("Family Members:", fg=typer.colors.GREEN)
            for member in family_members:
                is_current = " (current)" if member.uuid == guest.uuid else ""
                guest_type = getattr(member, 'guest_type', 'adult')
                type_label = f" ({guest_type})" if guest_type == 'child' else ""
                typer.secho(f"  - {member.first_name} {member.last_name}{type_label}{is_current}", fg=typer.colors.BLUE)
        else:
            typer.echo()
            typer.secho("Not part of any family", fg=typer.colors.YELLOW)
    except ValueError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def create_child(
    family_id: str = typer.Argument(
        ...,
        help="Family UUID to add the child to",
    ),
    first_name: str = typer.Argument(
        ...,
        help="First name of the child",
    ),
    last_name: str = typer.Argument(
        ...,
        help="Last name of the child",
    ),
    phone: str = typer.Option(
        None,
        "--phone",
        "-p",
        help="Phone number for the child",
    ),
):
    """Create a child guest linked to a family (no User account, no RSVP invite)."""
    async def _create_child():
        write_model = SqlChildGuestCreateWriteModel()
        guest = await write_model.create_child_guest(
            family_id=UUID(family_id),
            first_name=first_name,
            last_name=last_name,
            phone=phone,
        )
        return guest

    try:
        guest = asyncio.run(_create_child())

        typer.secho("Child guest created!", fg=typer.colors.GREEN)
        typer.secho(f"  Name: {guest.first_name} {guest.last_name}", fg=typer.colors.BLUE)
        typer.secho(f"  Guest ID: {guest.id}", fg=typer.colors.CYAN)
        typer.secho(f"  Family ID: {guest.family_id}", fg=typer.colors.CYAN)
        if guest.phone:
            typer.secho(f"  Phone: {guest.phone}", fg=typer.colors.BLUE)
        typer.echo()
        typer.secho("Note: Child guests do not receive separate RSVP invites.", fg=typer.colors.YELLOW)
        typer.secho("Their RSVP will be managed by the adult family member.", fg=typer.colors.YELLOW)
    except ValueError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

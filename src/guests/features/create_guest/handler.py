"""Handler for CreateGuestCommand execution."""

from datetime import UTC, datetime
from functools import singledispatchmethod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import async_session_manager
from src.email_service import get_email_service
from src.guests.dtos import GuestAlreadyExistsError, Language
from src.guests.features.create_guest.command import (
    CommandStatus,
    CreateGuestCommand,
    CreateGuestCommandResult,
    CreateGuestSeriesCommand,
    CreateGuestSeriesResult,
    EmailResult,
    EmailStatus,
)
from src.guests.features.create_guest.write_model import GuestCreateWriteModel
from src.guests.repository.orm_models import Guest, RSVPInfo
from src.models.user import User


class CreateGuestHandler:
    def __init__(
        self,
        create_guest_write_model: GuestCreateWriteModel,
        session_overwrite: AsyncSession | None = None,
    ):
        self.session_overwrite = session_overwrite
        self._create_guest_write_model = create_guest_write_model

    @singledispatchmethod
    async def execute(self, command):
        raise NotImplementedError(f"No handler for {type(command)}")

    @execute.register
    async def _(
        self,
        command: CreateGuestCommand,
    ) -> CreateGuestCommandResult:
        async with async_session_manager(
            session_overwrite=self.session_overwrite, auto_commit=False
        ) as db_session:
            return await self._execute_single(command, db_session)

    @execute.register
    async def _(
        self,
        command: CreateGuestSeriesCommand,
    ) -> CreateGuestSeriesResult:
        async with async_session_manager(
            session_overwrite=self.session_overwrite, auto_commit=False
        ) as db_session:
            return await self._execute_series(command, db_session)

    async def _execute_single(
        self,
        command: CreateGuestCommand,
        session: AsyncSession,
    ) -> CreateGuestCommandResult:
        try:
            return await self._create_guest(command, session)
        except GuestAlreadyExistsError as e:
            return CreateGuestCommandResult(
                status=CommandStatus.SKIPPED,
                email=command.email,
                message=str(e),
            )
        except Exception as e:
            return CreateGuestCommandResult(
                status=CommandStatus.ERROR,
                email=command.email,
                message=str(e),
            )

    async def _create_guest(
        self,
        command: CreateGuestCommand,
        session: AsyncSession,
    ) -> CreateGuestCommandResult:
        """Create guest based on command logic."""
        write_model = self._create_guest_write_model
        write_model.overwrite_session(session)

        guest_dto = await write_model.create_guest(
            email=command.email,
            first_name=command.first_name or None,
            last_name=command.last_name or None,
            preferred_language=Language(command.lang),
            send_email=False,
        )

        return CreateGuestCommandResult(
            status=CommandStatus.CREATED,
            email=command.email,
            message="User and guest created",
            guest_id=guest_dto.id,
        )

    async def _execute_series(
        self,
        command: CreateGuestSeriesCommand,
        session: AsyncSession,
    ) -> CreateGuestSeriesResult:
        """Execute series in two phases:

        Phase 1: Create all guests in a single transaction
        - Flush after each command
        - Commit only if ALL succeed
        - If any fails → rollback ALL

        Phase 2: Send emails (only if Phase 1 succeeded)
        - For each command with send_email=True
        - Update email_sent_on on RSVPInfo, flush
        - Send invitation email
        - Commit on success, rollback email_sent_on on failure
        """
        results = []
        try:
            for cmd in command.commands:
                result = await self._execute_single(cmd, session)
                results.append(result)

                if result.status == CommandStatus.ERROR:
                    await session.rollback()
                    return CreateGuestSeriesResult(
                        total=len(command.commands),
                        created=0,
                        skipped=0,
                        errors=len(command.commands),
                        emails_sent=0,
                        emails_failed=0,
                        results=results,
                    )

            await session.commit()

        except Exception as e:
            await session.rollback()
            for i in range(len(results), len(command.commands)):
                results.append(
                    CreateGuestCommandResult(
                        status=CommandStatus.ERROR,
                        email=command.commands[i].email,
                        message=f"Transaction failed: {str(e)}",
                    )
                )
            return CreateGuestSeriesResult(
                total=len(command.commands),
                created=0,
                skipped=0,
                errors=len(command.commands),
                emails_sent=0,
                emails_failed=0,
                results=results,
            )

        emails_sent = 0
        emails_failed = 0

        for i, result in enumerate(results):
            cmd = command.commands[i]

            if not cmd.send_email:
                continue

            if result.status != CommandStatus.CREATED:
                continue

            email_result = await self._send_email(result)

            result.email_status = email_result.status.value
            result.email_error = email_result.error

            if email_result.status is EmailStatus.SENT:
                emails_sent += 1
            else:
                emails_failed += 1

        return CreateGuestSeriesResult(
            total=len(results),
            created=sum(1 for r in results if r.status == CommandStatus.CREATED),
            skipped=sum(1 for r in results if r.status == CommandStatus.SKIPPED),
            errors=sum(1 for r in results if r.status == CommandStatus.ERROR),
            emails_sent=emails_sent,
            emails_failed=emails_failed,
            results=results,
        )

    async def _send_email(
        self,
        result: CreateGuestCommandResult,
    ) -> EmailResult:
        """Send invitation email and update RSVPInfo.email_sent_on."""
        async with async_session_manager() as email_session:
            try:
                rsvp_info = await email_session.execute(
                    select(RSVPInfo).where(RSVPInfo.guest_id == result.guest_id)
                )
                rsvp_info = rsvp_info.scalar_one_or_none()

                guest = await email_session.execute(
                    select(Guest).where(Guest.uuid == result.guest_id)
                )
                guest = guest.scalar_one_or_none()

                user = None
                if guest and guest.user_id:
                    user = await email_session.execute(
                        select(User).where(User.uuid == guest.user_id)
                    )
                    user = user.scalar_one_or_none()

                if not rsvp_info:
                    raise Exception("RSVPInfo not found")

                guest_name = f"{guest.first_name} {guest.last_name}".strip() or "Guest"
                rsvp_url = rsvp_info.rsvp_link if rsvp_info else ""
                email_address = user.email if user else ""
                language = Language(guest.preferred_language) if guest else Language.EN

                email_service = get_email_service()
                await email_service.send_invitation(
                    to_address=email_address,
                    guest_name=guest_name,
                    rsvp_url=rsvp_url,
                    language=language,
                    guest_id=result.guest_id,
                )

                rsvp_info.email_sent_on = datetime.now(UTC)
                await email_session.commit()

            except Exception as e:
                await email_session.rollback()
                return EmailResult(status=EmailStatus.FAILED, error=str(e))

            return EmailResult(status=EmailStatus.SENT)

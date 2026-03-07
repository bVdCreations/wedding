"""Handler for CreateGuestCommand execution."""

from functools import singledispatchmethod

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import async_session_manager
from src.guests.dtos import GuestAlreadyExistsError, Language
from src.guests.features.create_guest.command import (
    CommandStatus,
    CreateGuestCommand,
    CreateGuestCommandResult,
    CreateGuestSeriesCommand,
    CreateGuestSeriesResult,
)
from src.guests.features.create_guest.write_model import GuestCreateWriteModel


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
        """Execute series in a single transaction.

        - Flush after each command
        - Commit only if ALL succeed
        - Rollback ALL if any fails
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

            return CreateGuestSeriesResult(
                total=len(results),
                created=sum(1 for r in results if r.status == CommandStatus.CREATED),
                skipped=sum(1 for r in results if r.status == CommandStatus.SKIPPED),
                errors=sum(1 for r in results if r.status == CommandStatus.ERROR),
                emails_sent=0,
                emails_failed=0,
                results=results,
            )

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

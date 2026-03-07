"""Handler for CreateGuestCommand execution."""

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

    async def execute(
        self,
        command: CreateGuestCommand | CreateGuestSeriesCommand,
    ) -> CreateGuestCommandResult | CreateGuestSeriesResult:
        """Handle both single command and series."""
        async with async_session_manager(
            session_overwrite=self.session_overwrite, auto_commit=False
        ) as db_session:
            if isinstance(command, CreateGuestSeriesCommand):
                return await self._execute_series(command, db_session)

            return await self._execute_single(command, db_session)

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
        """Execute series - to be implemented in Phase 3."""
        raise NotImplementedError("Series execution not implemented yet")

"""Tests for SqlGuestCreateWriteModel using send_invitation_for_guest."""

from unittest.mock import AsyncMock

from src.config.database import async_session_maker
from src.email_service.dtos import EmailResult, EmailStatus
from src.guests.features.create_guest.write_model import SqlGuestCreateWriteModel


async def test_create_guest_uses_send_invitation_for_guest():
    """Test that send_invitation_for_guest is called when send_email=True."""
    mock_email_service = AsyncMock()
    mock_email_service.send_invitation_for_guest = AsyncMock(
        return_value=EmailResult(status=EmailStatus.SENT)
    )

    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(
            session_overwrite=db_session, email_service=mock_email_service
        )
        result = await write_model.create_guest(
            email="newmethod@example.com",
            first_name="New",
            last_name="Method",
            send_email=True,
        )

        mock_email_service.send_invitation_for_guest.assert_called_once()
        call_kwargs = mock_email_service.send_invitation_for_guest.call_args.kwargs
        assert call_kwargs["guest_id"] == result.id

        await db_session.rollback()


async def test_create_guest_email_failure_doesnt_raise():
    """Test that guest creation succeeds even when email fails."""
    mock_email_service = AsyncMock()
    mock_email_service.send_invitation_for_guest = AsyncMock(
        return_value=EmailResult(status=EmailStatus.FAILED, error="SMTP error")
    )

    async with async_session_maker() as db_session:
        write_model = SqlGuestCreateWriteModel(
            session_overwrite=db_session, email_service=mock_email_service
        )

        result = await write_model.create_guest(
            email="fail@example.com",
            first_name="Fail",
            last_name="Email",
            send_email=True,
        )

        assert result.email == "fail@example.com"
        assert result.first_name == "Fail"

        await db_session.rollback()

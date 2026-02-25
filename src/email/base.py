from abc import ABC, abstractmethod

from src.guests.dtos import Language


class EmailServiceBase(ABC):
    @abstractmethod
    async def send_invitation(
        self,
        to_address: str,
        guest_name: str,
        event_date: str,
        event_location: str,
        rsvp_url: str,
        response_deadline: str,
        language: Language = Language.EN,
    ) -> None:
        pass

    @abstractmethod
    async def send_confirmation(
        self,
        to_address: str,
        guest_name: str,
        attending: str,
        dietary: str,
        language: Language = Language.EN,
    ) -> None:
        pass

    @abstractmethod
    async def send_invite_one_plus_one(
        self,
        to_address: str,
        guest_name: str,
        plus_one_details: dict,
        language: Language = Language.EN,
    ) -> None:
        pass

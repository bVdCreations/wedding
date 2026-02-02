import abc

from src.guests.dtos import RSVPInfoDTO


class RSVPReadModel(abc.ABC):
    @abc.abstractmethod
    async def get_rsvp_info(self, token: str) -> RSVPInfoDTO | None: ...


class SqlRSVPReadModel(RSVPReadModel):
    @abc.abstractmethod
    async def get_rsvp_info(self, token: str) -> RSVPInfoDTO | None:
        raise NotImplementedError

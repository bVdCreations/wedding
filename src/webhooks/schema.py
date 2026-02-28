from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReceivedEmailAttachment(BaseModel):
    id: str
    filename: str
    content_type: str
    content_disposition: str | None = None
    content_id: str | None = None


class ReceivedEmailRaw(BaseModel):
    download_url: str
    expires_at: datetime


class ReceivedEmail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: str
    id: str
    to: list[str]
    from_: str = Field(alias="from")
    created_at: datetime
    subject: str
    html: str | None = None
    text: str | None = None
    headers: dict[str, str] = {}
    bcc: list[str] = []
    cc: list[str] = []
    reply_to: list[str] = []
    message_id: str
    raw: ReceivedEmailRaw
    attachments: list[ReceivedEmailAttachment] = []

"""Unit tests for ResendEmailForwarder, mocking the HTTP client."""

import base64

import httpx
import pytest

from src.webhooks.router import ResendEmailForwarder

# =============================================================================
# Mock HTTP infrastructure
# =============================================================================

EMAIL_ID = "4ef9a417-02e9-4d39-ad75-9611e0fcc33c"
RAW_DOWNLOAD_URL = "https://example.resend.com/raw/123"

RECEIVED_EMAIL_JSON = {
    "object": "email",
    "id": EMAIL_ID,
    "to": ["info@example.com"],
    "from": "Sender <sender@example.com>",
    "created_at": "2023-04-03T22:13:42.674981+00:00",
    "subject": "Hello",
    "html": "<p>Hello</p>",
    "text": "Hello",
    "headers": {},
    "bcc": [],
    "cc": [],
    "reply_to": [],
    "message_id": "<msg123>",
    "raw": {
        "download_url": RAW_DOWNLOAD_URL,
        "expires_at": "2023-04-03T23:13:42.674981+00:00",
    },
    "attachments": [],
}

RAW_EMAIL_CONTENT = "From: sender@example.com\r\nTo: info@example.com\r\nSubject: Hello\r\n\r\nHello"


class MockResponse:
    def __init__(self, *, json_data=None, text="", status_code=200):
        self._json_data = json_data
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=httpx.Request("GET", "https://example.com"),
                response=httpx.Response(self.status_code),
            )

    def json(self):
        return self._json_data


class MockHttpClient:
    """
    Replaces httpx.AsyncClient as the http_client_class.

    Usage:
        client = MockHttpClient()
        client.add_get(url, MockResponse(...))
        forwarder = ResendEmailForwarder(config=mock_config, http_client_class=client)

    The forwarder calls self._http_client_class() and uses the result as an
    async context manager, so MockHttpClient.__call__ returns self, and the
    class itself acts as the async context manager.
    """

    def __init__(self):
        self.get_calls: list[dict] = []
        self.post_calls: list[dict] = []
        self._get_responses: dict[str, MockResponse] = {}
        self._post_response = MockResponse(json_data={"id": "fwd-ok"})

    def add_get(self, url: str, response: MockResponse) -> "MockHttpClient":
        self._get_responses[url] = response
        return self

    def set_post(self, response: MockResponse) -> "MockHttpClient":
        self._post_response = response
        return self

    async def get(self, url: str, **kwargs) -> MockResponse:
        self.get_calls.append({"url": url, **kwargs})
        if url not in self._get_responses:
            raise KeyError(f"No mock response configured for GET {url}")
        return self._get_responses[url]

    async def post(self, url: str, **kwargs) -> MockResponse:
        self.post_calls.append({"url": url, **kwargs})
        return self._post_response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def __call__(self):
        """Called by ResendEmailForwarder as self._http_client_class()."""
        return self


# =============================================================================
# Fixtures
# =============================================================================


class MockConfig:
    """Mock ForwardConfig for injecting into ResendEmailForwarder."""

    resend_api_key = "test-api-key"
    emails_from = "fwd@example.com"

    def get_forward_to_emails(self) -> list[str]:
        return ["dest@example.com"]


@pytest.fixture
def mock_config() -> MockConfig:
    return MockConfig()


@pytest.fixture
def happy_path_client():
    """MockHttpClient pre-configured for a successful 3-step forward."""
    client = MockHttpClient()
    client.add_get(
        f"https://api.resend.com/emails/receiving/{EMAIL_ID}",
        MockResponse(json_data=RECEIVED_EMAIL_JSON),
    )
    client.add_get(RAW_DOWNLOAD_URL, MockResponse(text=RAW_EMAIL_CONTENT))
    return client


# =============================================================================
# Tests
# =============================================================================


@pytest.mark.asyncio
async def test_successful_forward_makes_three_http_calls(mock_config, happy_path_client):
    forwarder = ResendEmailForwarder(config=mock_config, http_client_class=happy_path_client)

    result = await forwarder(EMAIL_ID)

    assert result == {"id": "fwd-ok"}
    assert len(happy_path_client.get_calls) == 2
    assert len(happy_path_client.post_calls) == 1


@pytest.mark.asyncio
async def test_email_fetch_uses_correct_url_and_auth(mock_config, happy_path_client):
    forwarder = ResendEmailForwarder(config=mock_config, http_client_class=happy_path_client)
    await forwarder(EMAIL_ID)

    call = happy_path_client.get_calls[0]
    assert call["url"] == f"https://api.resend.com/emails/receiving/{EMAIL_ID}"
    assert call["headers"]["Authorization"] == "Bearer test-api-key"


@pytest.mark.asyncio
async def test_raw_content_downloaded_from_correct_url(mock_config, happy_path_client):
    forwarder = ResendEmailForwarder(config=mock_config, http_client_class=happy_path_client)
    await forwarder(EMAIL_ID)

    assert happy_path_client.get_calls[1]["url"] == RAW_DOWNLOAD_URL


@pytest.mark.asyncio
async def test_forward_prefixes_subject_with_fwd(mock_config, happy_path_client):
    forwarder = ResendEmailForwarder(config=mock_config, http_client_class=happy_path_client)
    await forwarder(EMAIL_ID)

    subject = happy_path_client.post_calls[0]["json"]["subject"]
    assert subject == "Fwd: Hello"


@pytest.mark.asyncio
async def test_forward_does_not_double_prefix_fwd(mock_config):
    client = MockHttpClient()
    client.add_get(
        f"https://api.resend.com/emails/receiving/{EMAIL_ID}",
        MockResponse(json_data={**RECEIVED_EMAIL_JSON, "subject": "Fwd: Hello"}),
    )
    client.add_get(RAW_DOWNLOAD_URL, MockResponse(text=RAW_EMAIL_CONTENT))

    forwarder = ResendEmailForwarder(config=mock_config, http_client_class=client)
    await forwarder(EMAIL_ID)

    assert client.post_calls[0]["json"]["subject"] == "Fwd: Hello"


@pytest.mark.asyncio
async def test_raw_content_attached_as_eml(mock_config, happy_path_client):
    forwarder = ResendEmailForwarder(config=mock_config, http_client_class=happy_path_client)
    await forwarder(EMAIL_ID)

    attachments = happy_path_client.post_calls[0]["json"]["attachments"]
    assert len(attachments) == 1
    assert attachments[0]["filename"] == "forwarded_message.eml"
    assert attachments[0]["content_type"] == "message/rfc822"
    decoded = base64.b64decode(attachments[0]["content"]).decode("utf-8")
    assert decoded == RAW_EMAIL_CONTENT


@pytest.mark.asyncio
async def test_no_recipients_skips_all_http_calls():
    class NoRecipientsConfig:
        resend_api_key = "test-api-key"
        emails_from = "fwd@example.com"

        def get_forward_to_emails(self):
            return []

    client = MockHttpClient()
    forwarder = ResendEmailForwarder(config=NoRecipientsConfig(), http_client_class=client)
    result = await forwarder(EMAIL_ID)

    assert result == {"skipped": "no recipients"}
    assert len(client.get_calls) == 0
    assert len(client.post_calls) == 0


@pytest.mark.asyncio
async def test_email_fetch_error_propagates(mock_config):
    client = MockHttpClient()
    client.add_get(
        f"https://api.resend.com/emails/receiving/{EMAIL_ID}",
        MockResponse(status_code=404),
    )

    forwarder = ResendEmailForwarder(config=mock_config, http_client_class=client)
    with pytest.raises(httpx.HTTPStatusError):
        await forwarder(EMAIL_ID)


@pytest.mark.asyncio
async def test_raw_download_error_propagates(mock_config):
    client = MockHttpClient()
    client.add_get(
        f"https://api.resend.com/emails/receiving/{EMAIL_ID}",
        MockResponse(json_data=RECEIVED_EMAIL_JSON),
    )
    client.add_get(RAW_DOWNLOAD_URL, MockResponse(status_code=500))

    forwarder = ResendEmailForwarder(config=mock_config, http_client_class=client)
    with pytest.raises(httpx.HTTPStatusError):
        await forwarder(EMAIL_ID)


@pytest.mark.asyncio
async def test_forward_send_error_propagates(mock_config, happy_path_client):
    happy_path_client.set_post(MockResponse(status_code=422))

    forwarder = ResendEmailForwarder(config=mock_config, http_client_class=happy_path_client)
    with pytest.raises(httpx.HTTPStatusError):
        await forwarder(EMAIL_ID)

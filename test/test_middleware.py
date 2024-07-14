from unittest.mock import MagicMock, AsyncMock

import pytest

from aiogram_tonconnect.middleware import AiogramTonConnectMiddleware


@pytest.mark.asyncio
async def test_user_with_null_language_code():
    mock_storage = MagicMock()
    middleware = AiogramTonConnectMiddleware(storage=mock_storage, manifest_url='https://example.com')
    dummy_handler = AsyncMock()

    class MockChat:
        type = 'private'

    class MockUser:
        id = 123
        is_bot = False
        language_code = None

    mock_state = AsyncMock()
    mock_state.get_data = AsyncMock(return_value={})

    await middleware(handler=dummy_handler, event=MagicMock(), data={
        'state': mock_state,
        'event_from_user': MockUser(),
        'event_chat': MockChat(),
    })

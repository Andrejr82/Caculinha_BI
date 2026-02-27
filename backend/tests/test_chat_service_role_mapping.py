from unittest.mock import Mock, AsyncMock, patch

import pytest

from backend.app.core.utils.session_manager import SessionManager
from backend.app.services.chat_service_v3 import ChatServiceV3


def test_normalize_role_maps_user_to_viewer():
    session_manager = Mock(spec=SessionManager)
    service = ChatServiceV3(session_manager=session_manager)

    assert service._normalize_role("user") == "viewer"


@pytest.mark.asyncio
async def test_process_message_uses_viewer_agent_for_user_role():
    session_manager = Mock(spec=SessionManager)
    session_manager.get_history.return_value = []
    session_manager.add_message = Mock()
    service = ChatServiceV3(session_manager=session_manager)

    mock_agent = Mock()
    mock_agent.run_async = AsyncMock(return_value={"response": "ok", "tool_calls": []})

    with patch.object(service, "_get_agent_for_role", return_value=mock_agent) as get_agent_mock:
        await service.process_message(
            query="consulta de vendas",
            session_id="s-role",
            user_id="u-role",
            user_role="user",
        )

    get_agent_mock.assert_called_once_with("viewer")

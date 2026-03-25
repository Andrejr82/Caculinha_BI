import logging

from backend.app.core.agents import base_agent


def test_configure_base_agent_logger_falls_back_to_stream_when_file_is_unavailable(monkeypatch):
    logger = logging.getLogger("base_agent")
    original_handlers = list(logger.handlers)
    original_propagate = logger.propagate

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    class _BrokenFileHandler:
        def __init__(self, *args, **kwargs):
            raise OSError("permission denied")

    monkeypatch.setattr(base_agent.logging, "FileHandler", _BrokenFileHandler)

    try:
        configured = base_agent._configure_base_agent_logger()

        assert configured is logger
        assert configured.handlers
        assert any(isinstance(handler, logging.StreamHandler) for handler in configured.handlers)
    finally:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
        for handler in original_handlers:
            logger.addHandler(handler)
        logger.propagate = original_propagate

"""
Tests for Logging Utilities
"""

import json
import logging
from io import StringIO
from unittest.mock import patch

from veyra.logging_utils import (
    PrettyFormatter,
    StructuredFormatter,
    get_logger,
    setup_logging,
)


class TestStructuredFormatter:
    """Test StructuredFormatter."""

    def test_format_basic(self):
        """Test basic log formatting."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data

    def test_format_with_extra(self):
        """Test formatting with extra fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        # Add extra field
        record.custom_field = "custom_value"
        record.numeric_field = 42

        output = formatter.format(record)
        data = json.loads(output)

        assert data["custom_field"] == "custom_value"
        assert data["numeric_field"] == 42

    def test_format_non_serializable_extra(self):
        """Test formatting with non-JSON-serializable extra fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        # Add non-serializable field
        record.unserializable = object()

        output = formatter.format(record)
        data = json.loads(output)

        assert "unserializable" in data
        assert isinstance(data["unserializable"], str)

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert "ValueError" in data["exception"]
        assert "Test error" in data["exception"]


class TestPrettyFormatter:
    """Test PrettyFormatter."""

    def test_format_basic(self):
        """Test basic pretty formatting."""
        formatter = PrettyFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        assert "INFO" in output
        assert "test.logger" in output
        assert "Test message" in output

    def test_format_with_colors(self):
        """Test color codes in output."""
        formatter = PrettyFormatter()

        # Test different log levels for color codes
        for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=10,
                msg="Test",
                args=(),
                exc_info=None,
            )
            output = formatter.format(record)
            # Should contain the level name
            assert logging.getLevelName(level) in output

    def test_format_with_extra(self):
        """Test formatting with extra fields."""
        formatter = PrettyFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"

        output = formatter.format(record)

        assert "custom_field=custom_value" in output

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        formatter = PrettyFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)

        assert "ValueError" in output
        assert "Test error" in output


class TestSetupLogging:
    """Test setup_logging function."""

    def teardown_method(self):
        """Clean up after each test."""
        # Reset root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    def test_setup_basic(self):
        """Test basic logging setup."""
        setup_logging(level="DEBUG")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) == 1

    def test_setup_structured(self):
        """Test structured logging setup."""
        setup_logging(level="INFO", structured=True)

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, StructuredFormatter)

    def test_setup_pretty(self):
        """Test pretty logging setup."""
        setup_logging(level="INFO", structured=False)

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, PrettyFormatter)

    def test_setup_with_file(self, tmp_path):
        """Test logging setup with file handler."""
        log_file = tmp_path / "test.log"
        setup_logging(level="INFO", log_file=str(log_file))

        root_logger = logging.getLogger()
        # Should have console and file handlers
        assert len(root_logger.handlers) == 2

        # Log something
        root_logger.info("Test log message")

        # File should exist with content
        assert log_file.exists()

    def test_clears_existing_handlers(self):
        """Test that setup clears existing handlers."""
        root_logger = logging.getLogger()
        root_logger.addHandler(logging.StreamHandler())
        root_logger.addHandler(logging.StreamHandler())

        setup_logging(level="INFO")

        # Should only have one handler now
        assert len(root_logger.handlers) == 1


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_basic(self):
        """Test getting a logger."""
        logger = get_logger("test.module")

        assert logger.name == "test.module"
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_level(self):
        """Test getting a logger with custom level."""
        logger = get_logger("test.module.custom", level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_get_same_logger_twice(self):
        """Test getting the same logger returns same instance."""
        logger1 = get_logger("test.same")
        logger2 = get_logger("test.same")

        assert logger1 is logger2


class TestLoggingIntegration:
    """Integration tests for logging."""

    def teardown_method(self):
        """Clean up after each test."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    def test_structured_logging_integration(self):
        """Test structured logging end-to-end."""
        output = StringIO()

        # Setup structured logging with custom stream
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(output)
        handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(handler)

        # Log a message
        logger = get_logger("test.integration")
        logger.info("Integration test message", extra={"request_id": "123"})

        # Verify output
        log_output = output.getvalue()
        data = json.loads(log_output)

        assert data["message"] == "Integration test message"
        assert data["request_id"] == "123"
        assert data["logger"] == "test.integration"

    def test_pretty_logging_integration(self):
        """Test pretty logging end-to-end."""
        output = StringIO()

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(output)
        handler.setFormatter(PrettyFormatter())
        root_logger.addHandler(handler)

        logger = get_logger("test.pretty")
        logger.warning("Warning message")

        log_output = output.getvalue()

        assert "WARNING" in log_output
        assert "Warning message" in log_output
        assert "test.pretty" in log_output


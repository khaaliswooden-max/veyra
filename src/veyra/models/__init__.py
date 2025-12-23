"""
Model Backends for Veyra

Provides adapters for various LLM providers and a mock backend for testing.
"""

from veyra.models.base import BaseModelBackend, ModelResponse
from veyra.models.mock import MockBackend
from veyra.models.registry import get_backend, register_backend, list_backends

__all__ = [
    "BaseModelBackend",
    "ModelResponse",
    "MockBackend",
    "get_backend",
    "register_backend",
    "list_backends",
]

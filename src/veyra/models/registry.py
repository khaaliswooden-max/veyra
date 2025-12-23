"""
Model Backend Registry

Central registry for managing model backends.
"""

from typing import Optional, Type

from veyra.models.base import BaseModelBackend
from veyra.models.mock import MockBackend


# Global registry of available backends
_REGISTRY: dict[str, Type[BaseModelBackend]] = {
    "mock": MockBackend,
}


def register_backend(name: str, backend_class: Type[BaseModelBackend]) -> None:
    """
    Register a new model backend.

    Args:
        name: Name to register the backend under
        backend_class: The backend class to register
    """
    _REGISTRY[name] = backend_class


def get_backend(name: str, **kwargs) -> BaseModelBackend:
    """
    Get an instance of a registered backend.

    Args:
        name: Name of the backend to get
        **kwargs: Arguments to pass to backend constructor

    Returns:
        Instantiated backend

    Raises:
        ValueError: If backend is not registered
    """
    # Lazy-load optional backends
    if name == "openai" and name not in _REGISTRY:
        try:
            from veyra.models.openai_backend import OpenAIBackend

            _REGISTRY["openai"] = OpenAIBackend
        except ImportError:
            raise ValueError(
                f"OpenAI backend requires the openai package. "
                f"Install with: pip install veyra[openai]"
            )

    if name == "anthropic" and name not in _REGISTRY:
        try:
            from veyra.models.anthropic_backend import AnthropicBackend

            _REGISTRY["anthropic"] = AnthropicBackend
        except ImportError:
            raise ValueError(
                f"Anthropic backend requires the anthropic package. "
                f"Install with: pip install veyra[anthropic]"
            )

    if name not in _REGISTRY:
        available = ", ".join(_REGISTRY.keys())
        raise ValueError(f"Unknown backend: {name}. Available backends: {available}")

    return _REGISTRY[name](**kwargs)


def list_backends() -> list[str]:
    """
    List all registered backend names.

    Returns:
        List of registered backend names
    """
    # Include lazy-loadable backends
    backends = set(_REGISTRY.keys())
    backends.add("openai")
    backends.add("anthropic")
    return sorted(backends)

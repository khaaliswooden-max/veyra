"""
Veyra: Post-Super-Intelligence Interplanetary LLM System

A vertically integrated intelligence platform designed to establish
frontier-level capability, reliability, and governability for LLM systems
operating in post-super-intelligence, multi-planetary contexts.
"""

__version__ = "0.1.0"

from veyra.core import VeyraCore
from veyra.config import VeyraConfig, load_config

__all__ = ["VeyraCore", "VeyraConfig", "load_config", "__version__"]

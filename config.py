"""
Configuration Management for Veyra

Handles YAML configuration files and environment variable overrides.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field

__all__ = [
    "VeyraConfig",
    "ModelConfig",
    "LatencyConfig", 
    "LoggingConfig",
    "GovernanceConfig",
    "load_config",
]

# Configuration version for migration support
CONFIG_VERSION = 1


class ModelConfig(BaseModel):
    """Model backend configuration."""
    
    backend: str = Field(
        default="mock",
        description="Model backend: mock, openai, anthropic, ollama"
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI model name"
    )
    anthropic_model: str = Field(
        default="claude-3-opus-20240229",
        description="Anthropic model name"
    )
    ollama_model: str = Field(
        default="llama3.2:1b",
        description="Ollama model name"
    )
    ollama_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API URL"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        description="Maximum tokens to generate"
    )


class LatencyConfig(BaseModel):
    """Interplanetary latency simulation configuration."""
    
    simulate_latency: bool = Field(
        default=False,
        description="Enable latency simulation"
    )
    min_delay_seconds: float = Field(
        default=180.0,
        ge=0.0,
        description="Minimum delay in seconds (Mars closest: ~3 min)"
    )
    max_delay_seconds: float = Field(
        default=1320.0,
        ge=0.0,
        description="Maximum delay in seconds (Mars farthest: ~22 min)"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: str = Field(
        default="INFO",
        description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    file: Optional[str] = Field(
        default=None,
        description="Optional log file path"
    )
    structured: bool = Field(
        default=True,
        description="Use structured JSON logging"
    )


class GovernanceConfig(BaseModel):
    """Governance and safety configuration."""
    
    audit_enabled: bool = Field(
        default=True,
        description="Enable full audit trails"
    )
    audit_persist_path: Optional[str] = Field(
        default=None,
        description="Path to persist audit trail (SQLite). None for in-memory."
    )
    safety_boundaries: bool = Field(
        default=True,
        description="Enable hard safety boundaries"
    )
    reversible_only: bool = Field(
        default=False,
        description="Only allow reversible operations"
    )


class VeyraConfig(BaseModel):
    """Main Veyra configuration.
    
    Configuration can be loaded from:
    1. YAML file (via from_yaml or load_config)
    2. Environment variables (via _apply_env_overrides)
    3. Direct instantiation
    
    Environment variables override file/default values.
    """
    
    # Metadata
    config_version: int = Field(
        default=CONFIG_VERSION,
        description="Configuration schema version"
    )
    system_name: str = Field(
        default="Veyra",
        description="System identifier"
    )
    version: str = Field(
        default="0.1.0",
        description="System version"
    )
    
    # Subsystem configs
    model: ModelConfig = Field(default_factory=ModelConfig)
    latency: LatencyConfig = Field(default_factory=LatencyConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    
    # World model settings
    world_model_enabled: bool = Field(
        default=False,
        description="Enable world model reasoning"
    )
    environment: str = Field(
        default="earth",
        description="Target environment: earth, mars, lunar, space"
    )

    @classmethod
    def from_yaml(cls, path: str | Path) -> VeyraConfig:
        """Load configuration from a YAML file.
        
        Args:
            path: Path to the YAML configuration file.
            
        Returns:
            VeyraConfig instance.
            
        Raises:
            FileNotFoundError: If the config file doesn't exist.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VeyraConfig:
        """Create configuration from a dictionary.
        
        Handles legacy 'system' key format from YAML files.
        
        Args:
            data: Configuration dictionary.
            
        Returns:
            VeyraConfig instance.
        """
        # Handle nested 'system' key from YAML (legacy format)
        if "system" in data:
            system_data = data.pop("system")
            if "name" in system_data:
                data["system_name"] = system_data["name"]
            if "version" in system_data:
                data["version"] = system_data["version"]
        
        return cls(**data)
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to this config.
        
        Environment variables take precedence over file/default values.
        
        Supported environment variables:
            VEYRA_BACKEND: Model backend name
            VEYRA_OPENAI_MODEL: OpenAI model name
            VEYRA_ANTHROPIC_MODEL: Anthropic model name
            VEYRA_OLLAMA_MODEL: Ollama model name
            VEYRA_OLLAMA_URL: Ollama API URL
            VEYRA_LOG_LEVEL: Logging level
            VEYRA_LOG_FILE: Log file path
            VEYRA_SIMULATE_LATENCY: Enable latency simulation (true/false)
            VEYRA_WORLD_MODEL_ENABLED: Enable world model (true/false)
            VEYRA_ENVIRONMENT: Target environment
            VEYRA_AUDIT_ENABLED: Enable audit trail (true/false)
            VEYRA_AUDIT_PATH: Audit trail persistence path
        """
        # Model config
        if backend := os.getenv("VEYRA_BACKEND"):
            self.model.backend = backend
        if openai_model := os.getenv("VEYRA_OPENAI_MODEL"):
            self.model.openai_model = openai_model
        if anthropic_model := os.getenv("VEYRA_ANTHROPIC_MODEL"):
            self.model.anthropic_model = anthropic_model
        if ollama_model := os.getenv("VEYRA_OLLAMA_MODEL"):
            self.model.ollama_model = ollama_model
        if ollama_url := os.getenv("VEYRA_OLLAMA_URL"):
            self.model.ollama_url = ollama_url
        
        # Logging config
        if log_level := os.getenv("VEYRA_LOG_LEVEL"):
            self.logging.level = log_level.upper()
        if log_file := os.getenv("VEYRA_LOG_FILE"):
            self.logging.file = log_file
        
        # Latency config
        if os.getenv("VEYRA_SIMULATE_LATENCY", "").lower() == "true":
            self.latency.simulate_latency = True
        elif os.getenv("VEYRA_SIMULATE_LATENCY", "").lower() == "false":
            self.latency.simulate_latency = False
        
        # World model
        if os.getenv("VEYRA_WORLD_MODEL_ENABLED", "").lower() == "true":
            self.world_model_enabled = True
        elif os.getenv("VEYRA_WORLD_MODEL_ENABLED", "").lower() == "false":
            self.world_model_enabled = False
        
        # Environment
        if env := os.getenv("VEYRA_ENVIRONMENT"):
            self.environment = env
        
        # Governance config
        if os.getenv("VEYRA_AUDIT_ENABLED", "").lower() == "true":
            self.governance.audit_enabled = True
        elif os.getenv("VEYRA_AUDIT_ENABLED", "").lower() == "false":
            self.governance.audit_enabled = False
        if audit_path := os.getenv("VEYRA_AUDIT_PATH"):
            self.governance.audit_persist_path = audit_path


def load_config(config_path: Optional[str] = None) -> VeyraConfig:
    """
    Load configuration from file with environment variable overrides.
    
    This is the primary configuration loading function. It:
    1. Loads from YAML file if path provided and exists
    2. Falls back to defaults if no file
    3. Applies environment variable overrides
    
    Args:
        config_path: Optional path to YAML config file.
        
    Returns:
        VeyraConfig instance with env overrides applied.
        
    Example:
        >>> config = load_config()  # Defaults + env vars
        >>> config = load_config("configs/production.yaml")  # File + env vars
    """
    if config_path and Path(config_path).exists():
        config = VeyraConfig.from_yaml(config_path)
    else:
        config = VeyraConfig()
    
    # Apply environment variable overrides (single place, no duplication)
    config._apply_env_overrides()
    
    return config

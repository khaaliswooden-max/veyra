"""
Configuration Management for Veyra

Handles YAML configuration files and environment variable overrides.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Model backend configuration."""
    backend: str = Field(default="mock", description="Model backend: mock, openai, anthropic")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model name")
    anthropic_model: str = Field(default="claude-3-opus-20240229", description="Anthropic model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)


class LatencyConfig(BaseModel):
    """Interplanetary latency simulation configuration."""
    simulate_latency: bool = Field(default=False, description="Enable latency simulation")
    min_delay_seconds: float = Field(default=180.0, description="Minimum delay (Mars closest: 3 min)")
    max_delay_seconds: float = Field(default=1320.0, description="Maximum delay (Mars farthest: 22 min)")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")
    file: Optional[str] = Field(default=None, description="Optional log file path")
    structured: bool = Field(default=True, description="Use structured JSON logging")


class GovernanceConfig(BaseModel):
    """Governance and safety configuration."""
    audit_enabled: bool = Field(default=True, description="Enable full audit trails")
    safety_boundaries: bool = Field(default=True, description="Enable hard safety boundaries")
    reversible_only: bool = Field(default=False, description="Only allow reversible operations")


class VeyraConfig(BaseModel):
    """Main Veyra configuration."""
    system_name: str = Field(default="Veyra", description="System identifier")
    version: str = Field(default="0.1.0")
    
    model: ModelConfig = Field(default_factory=ModelConfig)
    latency: LatencyConfig = Field(default_factory=LatencyConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    
    # World model settings
    world_model_enabled: bool = Field(default=False, description="Enable world model reasoning")
    environment: str = Field(default="earth", description="Target environment: earth, mars, lunar, space")

    @classmethod
    def from_yaml(cls, path: str | Path) -> "VeyraConfig":
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VeyraConfig":
        """Create configuration from a dictionary."""
        # Handle nested 'system' key from YAML
        if "system" in data:
            system_data = data.pop("system")
            if "name" in system_data:
                data["system_name"] = system_data["name"]
            if "version" in system_data:
                data["version"] = system_data["version"]
        
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> "VeyraConfig":
        """Create configuration from environment variables."""
        config = cls()
        
        # Override from environment
        if backend := os.getenv("VEYRA_BACKEND"):
            config.model.backend = backend
        if log_level := os.getenv("VEYRA_LOG_LEVEL"):
            config.logging.level = log_level
        if log_file := os.getenv("VEYRA_LOG_FILE"):
            config.logging.file = log_file
        if os.getenv("VEYRA_SIMULATE_LATENCY", "").lower() == "true":
            config.latency.simulate_latency = True
        if os.getenv("VEYRA_WORLD_MODEL_ENABLED", "").lower() == "true":
            config.world_model_enabled = True
        if env := os.getenv("VEYRA_ENVIRONMENT"):
            config.environment = env
            
        return config


def load_config(config_path: Optional[str] = None) -> VeyraConfig:
    """
    Load configuration from file with environment variable overrides.
    
    Args:
        config_path: Optional path to YAML config file
        
    Returns:
        VeyraConfig instance
    """
    if config_path and Path(config_path).exists():
        config = VeyraConfig.from_yaml(config_path)
    else:
        config = VeyraConfig()
    
    # Apply environment overrides
    if backend := os.getenv("VEYRA_BACKEND"):
        config.model.backend = backend
    if log_level := os.getenv("VEYRA_LOG_LEVEL"):
        config.logging.level = log_level
    if log_file := os.getenv("VEYRA_LOG_FILE"):
        config.logging.file = log_file
    if os.getenv("VEYRA_SIMULATE_LATENCY", "").lower() == "true":
        config.latency.simulate_latency = True
    if os.getenv("VEYRA_WORLD_MODEL_ENABLED", "").lower() == "true":
        config.world_model_enabled = True
    if env := os.getenv("VEYRA_ENVIRONMENT"):
        config.environment = env
        
    return config

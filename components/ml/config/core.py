import logging
import os
from abc import ABC
from functools import lru_cache
from typing import ClassVar, Literal, Optional

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FOLDER = "config"
env = os.getenv("ENVIRONMENT", "dev")


class BaseConfig(ABC):
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __getattr__(self, name):
        return None


class ServiceInfo(BaseModel):
    name: str
    description: Optional[str]


class YamlConfig(BaseConfig):
    def __init__(self, yaml_path):
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        # Handle ServiceInfo if present
        if "service_info" in data:
            self.service_info = ServiceInfo(**data["service_info"])
            # Remove 'service_info' from data to avoid duplicate processing
            del data["service_info"]
        else:
            self.service_info = None

        super().__init__(data)


def create_config(env_name=env, custom_path=None):
    """Create a config instance by loading YAML configuration.

    Loads configuration from either a custom path, or a default filepath
    based on the environment name.

    Args:
        env_name (str): The environment name, used to load default config file.
        custom_path (str): Optional custom config file path.

    Returns:
        YamlConfig: A YamlConfig instance with loaded configuration.
    """
    custom_path = custom_path or os.environ.get("CUSTOM_CONFIG_PATH")

    if custom_path is not None:
        return YamlConfig(yaml_path=custom_path)
    else:
        file_path = os.path.join(DEFAULT_CONFIG_FOLDER, f"config.{env_name}.yml")
        return YamlConfig(yaml_path=file_path)


EnvironmentType = Literal["dev", "nonprod", "prod", "local"]


class AppEnvironment(BaseModel):
    version: str = Field(default_factory=lambda: os.getenv("APP_VERSION", "NA"))
    environment: EnvironmentType = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "dev"))

    # Class variables
    ALLOWED_ENVIRONMENTS: ClassVar[set] = {"dev", "nonprod", "prod", "local"}

    class Config:
        frozen = True
        extra = "forbid"

    def __str__(self):
        return self.environment.__str__()

    @property
    def is_production(self) -> bool:
        return self.environment == "prod"

    @model_validator(mode="after")
    def validate_environment(self) -> "AppEnvironment":
        if self.environment not in self.ALLOWED_ENVIRONMENTS:
            raise ValueError(f"Invalid environment: {self.environment}")
        return self


class Settings(BaseSettings):
    hf_token: str = ""
    hf_dataset_repo_id: str = ""
    crawl_galleries: list[str] = ["dcbest", "baseball_new11"]
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

import os
from enum import Enum
from typing import Any, Dict


class Environment(str, Enum):
    """Environment enumeration."""

    LOCAL = "local"
    DEV = "dev"
    NON_PROD = "nonprod"
    PROD = "prod"


def check_env_vars(dotenv: Dict[str, Any], required_env_vars: list, secret_keys: list, print_values: bool = True):
    """Check if required environment variables are set."""
    for key in required_env_vars:
        value = dotenv.get(key) or os.environ.get(key)
        if not value:
            raise ValueError(f"Environment variable {key} is not set")
        elif print_values:
            if key in secret_keys:
                masked_value = value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "****"
                print(f"Environment variable {key} is set: {masked_value}")
            else:
                print(f"Environment variable {key} is set: {value}")

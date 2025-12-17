from typing import Optional

from pydantic import BaseModel

from ml.config import BaseConfig, create_config


class DefaultPrompt(BaseModel):
    name: str
    version: Optional[int] = None
    label: Optional[str] = None


def get_default_prompt(
    config: BaseConfig = None, name: Optional[str] = None, index: Optional[int] = None
) -> DefaultPrompt:
    """
    Retrieves a default prompt from the configuration.

    Args:
        config (BaseConfig, optional): The configuration object. If not provided, a new config is created.
        name (str, optional): The name of the desired prompt. If provided, the function will attempt to find a prompt with that name.
        index (int, optional): The index of the desired prompt in the prompt_templates list. If provided, the function will return the prompt at that index.

    Returns:
        DefaultPrompt: The default prompt object.

    Raises:
        KeyError: If the config doesn't contain the 'prompt_templates' attribute.
        IndexError: If the requested index is out of range for the 'prompt_templates' list.
    """
    if config is None:
        config = create_config()

    if not config.prompt_templates:
        raise KeyError("Config doesn't contain attribute prompt_templates (type: List).")

    if index is not None:
        if len(config.prompt_templates) <= index:
            raise IndexError(
                "Requested index of prompt value not present in config under key: prompt_templates. "
                "Prompt Names are managed in the config yaml file. Attributes: prompt_templates (type: List)"
            )
        default_prompt = config.prompt_templates[index]
    elif name is not None:
        matching_prompts = [prompt for prompt in config.prompt_templates if prompt.get("name") == name]
        if not matching_prompts:
            raise ValueError(f"Prompt with name '{name}' not in passed config.")
        else:
            default_prompt = matching_prompts[0]
    else:
        default_prompt = config.prompt_templates[0]

    return DefaultPrompt(**default_prompt)

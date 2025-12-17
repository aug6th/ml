from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.prompts.string import mustache_template_vars
from langchain_core.runnables import ConfigurableField, Runnable, RunnableConfig
from langchain_core.runnables.configurable import RunnableConfigurableFields
from langchain_core.runnables.utils import Input, Output
from langfuse import Langfuse
from langfuse.api import BasePrompt, TextPrompt
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from ml.config import BaseConfig, create_config
from ml.logging import get_logger
from ml.prompt.constants import (
    MUSTACHE,
    PROMPT_NAME,
    PROMPT_TEMPLATE,
    PROMPT_VERSION,
)
from ml.prompt.defaults import DefaultPrompt, get_default_prompt

logger = get_logger("prompt-service")


DEFAULT_CACHE_TTL = 60


class ChatPrompt(BasePrompt):
    """Langchain friendly way to represent ChatPrompts."""

    prompt: List[Tuple]


Prompt = Union[ChatPrompt, TextPrompt]


class PromptManager(BaseModel, Runnable, ABC):
    @abstractmethod
    def get_prompt(self, name: str = None, version: int = None, **kwargs) -> Prompt:
        pass

    def invoke(self, input: Input, config: Optional[RunnableConfig] = None) -> Output:
        prompt_name = input.get("prompt_name")

        prompt_template = self.get_prompt(name=prompt_name).prompt
        if isinstance(prompt_template, List):
            return ChatPromptTemplate.from_messages(messages=prompt_template, template_format="mustache").invoke(
                input, config
            )
        return PromptTemplate.from_template(template=prompt_template).invoke(input, config)


class YAMLPromptClient(PromptManager):
    prompts: Dict = {}
    default_prompt: Optional[DefaultPrompt] = None
    name: Optional[str] = "yaml"

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._read_prompt_from_yaml(data.get("prompts_config"))

    def _read_prompt_from_yaml(self, prompts_config: List[Dict]):
        for topic in prompts_config:
            if isinstance(topic, ChatPrompt):
                self.prompts[topic.name] = topic
            elif isinstance(topic.get("prompt"), List):
                self.prompts[topic.get("name")] = ChatPrompt(
                    name=topic.get("name"), prompt=topic.get("prompt"), labels=[], version=1, tags=[]
                )
            elif isinstance(topic.get("prompt"), str):
                name = topic["name"]
                self.prompts[name] = TextPrompt(
                    name=name,
                    version=topic.get("version", 1),
                    prompt=topic.get("prompt"),
                    config=topic.get("config", {}),
                    labels=[],
                    tags=[],
                )

    def get_prompt(self, name: str = None, version: int = None, **kwargs) -> Prompt:
        # TODO: Implement dynamic version for Yaml config
        if self.default_prompt is not None:
            # Set default prompt name if not passed
            if name is None:
                name = self.default_prompt.name
        if name not in self.prompts:
            raise HTTPException(status_code=400, detail=f"Topic not supported. Received: {name}")

        return self.prompts.get(name)


class LangfusePromptClient(PromptManager):
    name: Optional[str] = "langfuse"
    client: Optional[Any] = None
    default_prompt: Optional[DefaultPrompt] = None
    langfuse_config: Optional[Any] = None
    cache_ttl_seconds: Optional[int] = DEFAULT_CACHE_TTL

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, config: Optional[Any] = None, **data: Any):
        super().__init__(**data)
        self.client = data.get("client", Langfuse())
        self.default_prompt = data.get("default_prompt")

        # Call create_config only once
        config = config or create_config()

        self._set_langfuse_config(data, config)
        self._set_cache_ttl(data, config)

    def _set_langfuse_config(self, data: dict, config: Any) -> None:
        if "langfuse_config" in data:
            self.langfuse_config = data["langfuse_config"]
        else:
            self.langfuse_config = config.langfuse if hasattr(config, "langfuse") else None

    def _set_cache_ttl(self, data: dict, config: Any) -> None:
        if "cache_ttl_seconds" in data:
            self.cache_ttl_seconds = data["cache_ttl_seconds"]
        else:
            if hasattr(config, "prompt") and isinstance(config.prompt, dict):
                self.cache_ttl_seconds = config.prompt.get("cache_ttl_seconds")
            else:
                self.cache_ttl_seconds = 60

    def get_prompt(self, name: str = None, version: int = None, **kwargs) -> Prompt:
        if self.default_prompt is not None:
            # Set default prompt name and version if not passed
            if name is None:
                name = self.default_prompt.name
            # Only use default version if name matches default
            if version is None and name == self.default_prompt.name:
                version = self.default_prompt.version
        try:
            langfuse_prompt = self.client.get_prompt(
                name,
                version=version,
                cache_ttl_seconds=kwargs.get("cache_ttl_seconds") or self.cache_ttl_seconds,
            )
        except Exception:
            raise HTTPException(status_code=400, detail=f"Topic not supported. Received: {name}")

        if langfuse_prompt.config is None:
            langfuse_prompt.config = {}

        # Note: This could be deprecated if langfuse supports keeping mustache templates for langchain.
        if (
            isinstance(langfuse_prompt.prompt, List)
            and len(langfuse_prompt.prompt)
            and isinstance(langfuse_prompt.prompt[0], Dict)
        ):
            # Convert to lust of tuples
            langfuse_prompt.prompt = [(msg["role"], msg["content"]) for msg in langfuse_prompt.prompt]
        return langfuse_prompt


def get_prompt_client(config: BaseConfig, prompt_index: int = None, prompt_name: str = None):
    if config is None:
        config = create_config()
    default_prompt = get_default_prompt(config, index=prompt_index, name=prompt_name)

    if not config.prompt_client or config.prompt_client == "langfuse":
        return LangfusePromptClient(default_prompt=default_prompt)
    elif config.prompt_client == "yaml":
        return YAMLPromptClient(prompts_config=config.prompt_templates, default_prompt=default_prompt)
    else:
        raise KeyError(f"Provided prompt-client '{config.prompt_client}' not supported.")


class SkeletonPromptTemplate(PromptTemplate):
    """Class that allows an empty prompt template instantiation that isn't validated.
    It expects to be configured at runtime.

    Example:
        .. code-block:: python

        from langchain import PromptTemplate
        prompt_template = ConfigurablePromptTemplate().configurable_fields(
            template=ConfigurableField(
                id="prompt",
                name="Prompt",
                description="The prompt to use.",
            )
        )
    """

    template: str = ""
    # Placeholders to allow these two fields be configurable fields that can beo overwritten by caller.
    # Values are overwritten
    name: str = ""
    version: int = -1
    """The prompt template."""
    input_variables: List = []
    """How to parse the output of calling an LLM on this formatted prompt."""
    validate_template: bool = False

    model_config = {"not_allow_base_model_validators": True}  # This disables base model validators


class ConfigurablePromptTemplate(RunnableConfigurableFields):
    """NOTE: passing of config will be handled by per_req_config_modifier"""

    def __init__(self, default=None, fields=None):
        if default is None:
            default = SkeletonPromptTemplate(template_format=MUSTACHE)

        # Mercury is now using mustache style prompts across projects
        assert default.template_format == MUSTACHE

        if fields is None:
            fields = {
                "template": ConfigurableField(
                    id=PROMPT_TEMPLATE,
                    name="Template",
                    description="The prompt template to use.",
                ),
                "name": ConfigurableField(
                    id=PROMPT_NAME,
                    name="Name",
                    description="The name of the prompt template to use.",
                ),
                "version": ConfigurableField(
                    id=PROMPT_VERSION,
                    name="Version",
                    description="The version of the prompt template to use.",
                ),
            }

        super().__init__(default=default, fields=fields)


@lru_cache(maxsize=20)
def _mustache_template_vars(prompt: str):
    return mustache_template_vars(prompt)


def get_unsupported_variables(prompt: str, input_variables):
    variables_in_prompt = _mustache_template_vars(prompt)
    return [v for v in variables_in_prompt if v not in input_variables]


def get_missing_variables(prompt: str, input_variables):
    variables_in_prompt = _mustache_template_vars(prompt)
    return [v for v in input_variables if v not in variables_in_prompt]

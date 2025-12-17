from abc import ABC, abstractmethod
from typing import Any, Dict

from langchain_core.prompts.string import PromptTemplateFormat, get_template_variables

from ml.prompt.constants import MUSTACHE


class BasePromptTransformer(ABC):
    def __init__(self, template_format: PromptTemplateFormat = MUSTACHE, partial_variables: Dict[str, Any] = None):
        """Initialize the transformer with template format and partial variables.

        Args:
            template_format: Format of the template ('jinja2' or 'f-string')
            partial_variables: Dictionary of variables to be pre-populated
        """
        self.template_format = template_format
        self.partial_variables = partial_variables or {}
        self._cached_variables = {}  # Cache for parsed variables

    def get_variables(self, template: str) -> list[str]:
        """Get all variables from the template using LangChain's parser."""
        if template not in self._cached_variables:
            self._cached_variables[template] = get_template_variables(template, self.template_format)
        return self._cached_variables[template]

    @abstractmethod
    def transform(self, template: str) -> str:
        """Transform a prompt template by processing and injecting variables."""
        pass

    def has_variable(self, template: str, variable_name: str) -> bool:
        """Check if a specific variable exists in the template."""
        return variable_name in self.get_variables(template)

import logging
import re
from typing import List, Optional, Union


class CodeParser:
    """Parser for extracting code blocks from markdown text."""

    def __init__(self, index: Optional[int] = None):
        self.index = index

    def parse(self, text: str) -> Union[str, List[str]]:
        """Extract code blocks from markdown text.

        Args:
            text: Markdown text containing code blocks

        Returns:
            List of code blocks, or single block if index is set
        """
        code_blocks = []
        current_code_block = []
        in_code_block = False

        for line in text.split("\n"):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                if not in_code_block:
                    code_blocks.append("\n".join(current_code_block))
                    current_code_block = []
            elif in_code_block:
                current_code_block.append(line)

        if current_code_block:
            code_blocks.append("\n".join(current_code_block))

        if self.index is not None:
            if 0 <= self.index < len(code_blocks):
                return code_blocks[self.index]
            logging.info(f"No code encountered for index {self.index}. Number of code blocks: {len(code_blocks)}")
            return ""

        if not code_blocks:
            logging.info("No code encountered")
        return code_blocks


def parse_out_code(source_code: str, block_type: str, block_name: str, lang: str = "python") -> Optional[str]:
    """Extract a specific code block (function, class, etc.) from source code.

    Args:
        source_code: The source code to parse
        block_type: Type of block to extract (function, async_function, class, variable)
        block_name: Name of the block to extract
        lang: Programming language (currently only python supported)

    Returns:
        The extracted code block, or None if not found
    """
    lang_patterns = {
        "python": {
            "function": re.compile(rf"^\s*def\s+{re.escape(block_name)}\b", re.MULTILINE),
            "async_function": re.compile(rf"^\s*async\s+def\s+{re.escape(block_name)}\b", re.MULTILINE),
            "class": re.compile(rf"^\s*class\s+{re.escape(block_name)}\b", re.MULTILINE),
            "variable": re.compile(rf"^\s*{re.escape(block_name)}\s*=", re.MULTILINE),
        },
    }

    if lang not in lang_patterns or block_type not in lang_patterns[lang]:
        logging.error(f"Unsupported language '{lang}' or block type '{block_type}'.")
        return None

    if lang != "python":
        raise NotImplementedError("Only Python is currently supported")

    try:
        block_pattern = lang_patterns[lang][block_type]
        lines = source_code.split("\n")
        inside_block = False
        indent_level = None
        block_code = []

        for line in lines:
            if not inside_block:
                if block_pattern.match(line):
                    inside_block = True
                    indent_level = len(line) - len(line.lstrip())
                    block_code.append(line)
            else:
                current_indent = len(line) - len(line.lstrip())
                if line.strip() == "" or current_indent > indent_level:
                    block_code.append(line)
                elif current_indent == indent_level and line.strip():
                    break

        return "\n".join(block_code) if block_code else None

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

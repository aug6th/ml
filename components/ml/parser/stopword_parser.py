class StopwordOutputParser:
    """Parser that truncates text at a stopword."""

    def __init__(self, stopword: str):
        self.stopword = stopword

    def parse(self, text: str) -> str:
        """Parse text by truncating at stopword.

        Args:
            text: Text to parse

        Returns:
            Text up to (but not including) the stopword
        """
        stopword_index = text.find(self.stopword)
        if stopword_index != -1:
            return text[:stopword_index].strip()
        else:
            return text

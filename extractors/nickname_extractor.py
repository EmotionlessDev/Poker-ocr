class NicknameExtractor:
    """Extracts nickname from OCR results."""

    def extract(self, texts: list[str]) -> str:
        if not texts:
            return ""

        # usually nickname is first detected line
        return texts[0].strip()
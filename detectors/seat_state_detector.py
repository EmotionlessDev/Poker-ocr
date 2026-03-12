import time

class SeatStateDetector:
    """Detects whether a poker seat is active."""

    def detect(self, texts: list[str]) -> bool:
        """
        Determine if seat is active based on OCR texts.
        """
        if not texts:
            return False

        text = " ".join(texts).lower()

        if "empty seat" in text:
            return False

        if "sitting out" in text:
            return False

        return True
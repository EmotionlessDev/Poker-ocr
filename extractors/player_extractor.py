import easyocr
import re
import time

from utils.image_utils import safe_crop
from domain.state import Player


class PlayerExtractor:

    def __init__(
        self,
        hero_nickname: str,
        seat_detector,
        nickname_extractor,
        ocr_interval: float = 2.0,
    ):
        self.hero_nickname = hero_nickname or ""
        self.ocr_interval = ocr_interval

        self.reader = easyocr.Reader(["en"], gpu=True, verbose=False)

        self.seat_detector = seat_detector
        self.nickname_extractor = nickname_extractor

    def extract(self, frame, zones, players: list[Player]):
        """
        Extract player data from frame.
        """

        now = time.time()

        for i, player in enumerate(players):

            if i >= len(zones):
                break

            zone = zones[i]

            # --- invalid zone
            if zone is None or zone.width <= 0 or zone.height <= 0:
                self._reset_player(player)
                continue

            player.zone = zone

            # --- OCR throttling
            if now - player.last_ocr_time < self.ocr_interval:
                continue

            crop = safe_crop(frame, zone)

            if crop is None:
                self._reset_player(player)
                continue

            # --- run OCR once
            texts = self.reader.readtext(crop, detail=0)

            # --- detect seat state
            is_active = self.seat_detector.detect(texts)

            if not is_active:
                self._reset_player(player)
                player.last_ocr_time = now
                continue

            player.is_active = True

            # --- nickname extraction
            nickname = self.nickname_extractor.extract(texts)

            if nickname:
                player.nickname = nickname

            # --- hero detection
            player.is_hero = self._is_hero(player.nickname)

            player.last_ocr_time = now

    def _reset_player(self, player: Player):
        """Reset player state."""
        player.is_active = False
        player.nickname = ""
        player.is_hero = False
        player.zone = None

    def _is_hero(self, nickname: str) -> bool:
        if not nickname or not self.hero_nickname:
            return False

        clean_nick = re.sub(r"\s+", "", nickname).lower()
        clean_hero = re.sub(r"\s+", "", self.hero_nickname).lower()

        return clean_nick == clean_hero
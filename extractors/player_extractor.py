import pytesseract
import re
import time
from utils.image_utils import safe_crop
from domain.state import Player
from domain.geometry import Rect

class PlayerExtractor:
    def __init__(self, hero_nickname: str, ocr_interval: float = 1.0):
        self.hero_nickname = hero_nickname or ""
        self.ocr_interval = ocr_interval

    def extract(self, frame, zones, players: list[Player]):
        """Обновляет players[i].nickname, .zone, .is_hero. OCR троттлится по игроку."""
        now = time.time()

        for i, zone in enumerate(zones):
            if i >= len(players):
                break

            p = players[i]
            p.zone = zone

            # throttle OCR per player
            if now - p.last_ocr_time < self.ocr_interval:
                continue

            # crop area slightly above panel for nickname
            y1 = max(0, zone.y1 - 20)
            tmp_rect = Rect(zone.x1, y1, zone.x2, zone.y2)
            crop = safe_crop(frame, tmp_rect)
            if crop is None:
                continue

            text = pytesseract.image_to_string(crop)
            nickname = text.strip()

            if nickname:
                p.nickname = nickname

            p.last_ocr_time = now

            # hero detection fuzzy
            if self._is_hero(nickname):
                p.is_hero = True

    def _is_hero(self, nickname: str):
        text_clean = re.sub(r'\W+', '', (nickname or "")).lower()
        hero_clean = re.sub(r'\W+', '', (self.hero_nickname or "")).lower()
        return hero_clean != "" and hero_clean in text_clean
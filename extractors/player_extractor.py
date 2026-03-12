import easyocr
import re
import time
import cv2
import numpy as np
from utils.image_utils import safe_crop
from domain.state import Player
from domain.geometry import Rect

class PlayerExtractor:
    def __init__(self, hero_nickname: str, ocr_interval: float = 1.0):
        self.hero_nickname = hero_nickname or ""
        self.ocr_interval = ocr_interval
        self.reader = easyocr.Reader(['en'], gpu=True, verbose=False)

    def extract(self, frame, zones, players: list[Player]):
        """Extract nicknames for players using OCR, with throttling per player."""
        now = time.time()

        for i, zone in enumerate(zones):
            if i >= len(players):
                break

            p = players[i]

            if zone is None:
                p.zone = None
                p.nickname = ""
                p.is_hero = False
                p.is_active = False
                continue
            
            p.is_active = True
            p.zone = zone

            # throttle OCR per player
            if now - p.last_ocr_time < self.ocr_interval:
                continue

            # crop player area
            tmp_rect = zone
            crop = safe_crop(frame, tmp_rect)
            if crop is None:
                continue

            # OCR
            result = self.reader.readtext(crop, detail=0)
            if not result:
                continue
            nickname = result[0]

            if nickname:
                p.nickname = nickname

            p.last_ocr_time = now

            # hero detection fuzzy
            if self._is_hero(nickname):
                p.is_hero = True
            
            print(f"Extracted player {p.seat}: '{p.nickname}' (Hero: {p.is_hero})")

    def _is_hero(self, nickname):
        if not self.hero_nickname:
            return False

        clean_nick = re.sub(r"\s+", "", nickname).lower()
        clean_hero = re.sub(r"\s+", "", self.hero_nickname).lower()

        return clean_nick == clean_hero
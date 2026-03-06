import pytesseract
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

    def extract(self, frame, zones, players: list[Player]):
        """Обновляет players[i].nickname, .zone, .is_hero. OCR троттлится по игроку.
        Ники ищутся по цвету #A4A4A4 вместо жёсткого кропа."""
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
            
            # # imshow zone
            # cv2.imshow("Player Zone", safe_crop(frame, zone))
            # cv2.waitKey(1)
            
            p.is_active = True
            p.zone = zone

            # throttle OCR per player
            if now - p.last_ocr_time < self.ocr_interval:
                continue

            # берем всю зону игрока
            tmp_rect = zone
            crop = safe_crop(frame, tmp_rect)
            if crop is None:
                continue

            # маска для белого/серого цвета никнейма (#A4A4A4)
            mask = self._mask_nickname_color(crop)

            # сглаживание и бинаризация
            mask = cv2.medianBlur(mask, 3)

            # OCR
            text = pytesseract.image_to_string(mask, config="--psm 7")  # single line
            nickname = text.strip()

            if nickname:
                p.nickname = nickname

            p.last_ocr_time = now

            # hero detection fuzzy
            if self._is_hero(nickname):
                p.is_hero = True

    def _mask_nickname_color(self, crop):
        """Возвращает бинарную маску пикселей цвета никнейма (#A4A4A4)."""
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        # диапазон для "серого/белого" с небольшой погрешностью
        lower = np.array([0, 0, 160])   # H,S,V
        upper = np.array([180, 50, 180])
        mask = cv2.inRange(hsv, lower, upper)
        return mask

    def _is_hero(self, nickname: str):
        text_clean = re.sub(r'\W+', '', (nickname or "")).lower()
        hero_clean = re.sub(r'\W+', '', (self.hero_nickname or "")).lower()
        return hero_clean != "" and hero_clean in text_clean
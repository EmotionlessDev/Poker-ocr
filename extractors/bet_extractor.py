import time

import cv2
import numpy as np
import easyocr
import re

from utils.image_utils import safe_crop


class BetExtractor:

    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=True, verbose=False)

    def extract(self, frame, zone) -> float | None:
        crop = safe_crop(frame, zone)
        if crop is None:
            return None

        panel = self._find_bet_panel(crop)

        if panel is None:
            return None

        processed = self._preprocess(panel)

        texts = self.reader.readtext(processed, detail=0)

        return self._parse_amount(texts)
    
    def _preprocess(self, crop):
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

        gray = cv2.convertScaleAbs(gray, alpha=2.5, beta=0)

        _, thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # текст должен быть чёрным на белом
        thresh = 255 - thresh

        return thresh

    def _find_bet_panel(self, crop):
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        # тёмные цвета (плашка)
        lower = np.array([0, 0, 0])
        upper = np.array([180, 255, 60])

        mask = cv2.inRange(hsv, lower, upper)

        # сглаживаем
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None

        # берём самый большой тёмный прямоугольник
        best = max(contours, key=cv2.contourArea)

        x, y, w, h = cv2.boundingRect(best)

        # фильтр — чтобы не схватить весь стол
        if w < 25 or h < 10:
            return None

        return crop[y:y+h, x:x+w]
    
    def _parse_amount(self, texts: list[str]) -> float | None:
            for text in texts:
                text = text.replace(",", "")
                text = text.replace("S", "5")
                text = text.replace("I", "1")
                text = text.replace("|", "1")
                text = text.replace("O", "0")

                match = re.search(r"\d+(\.\d+)?", text)
                if match:
                    try:
                        return float(match.group())
                    except:
                        continue
            return None
    
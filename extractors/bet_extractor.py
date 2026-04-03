import cv2
import numpy as np
import easyocr
import re
import time

from utils.image_utils import safe_crop


class BetExtractor:

    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=True, verbose=False)

    def extract(self, frame, zone) -> float | None:
        """
        zone — это уже уточнённая зона панели со ставкой (или None)
        """
        crop = safe_crop(frame, zone)
        if crop is None:
            return None
        
        # save for debug
        timestamp = int(time.time() * 1000)
        cv2.imwrite(f"./debug/bet_zone_{timestamp}.png", crop)

        processed = self._preprocess(crop)

        texts = self.reader.readtext(
            processed, 
            detail=0,
            paragraph=False,
            contrast_ths=0.15,
            text_threshold=0.4
        )

        return self._parse_amount(texts)
    
    def _preprocess(self, crop):
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        # Upscale (очень важно)
        gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

        # Увеличиваем контраст
        gray = cv2.convertScaleAbs(gray, alpha=2.5, beta=0)

        # Бинаризация
        _, thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # Текст должен быть чёрным на белом
        thresh = 255 - thresh

        return thresh

    def _parse_amount(self, texts: list[str]) -> float | None:
        # Склеиваем все тексты (на случай если "1" и "0" раздельно)
        full_text = "".join(texts)
        
        full_text = full_text.replace(",", "")
        full_text = full_text.replace(" ", "")


        full_text = full_text.replace("S", "5")
        full_text = full_text.replace("I", "1")
        full_text = full_text.replace("|", "1")
        full_text = full_text.replace("O", "0")
        full_text = full_text.replace("l", "1")
        full_text = full_text.replace("B", "8")
        full_text = full_text.replace("G", "6")
        full_text = full_text.replace("q", "9")

        match = re.search(r"\d+(\.\d+)?", full_text)
        if match:
            try:
                return float(match.group())
            except:
                pass

        return None
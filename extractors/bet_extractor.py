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
        crop = safe_crop(frame, zone)
        if crop is None:
            return None

        processed = self._preprocess(crop)

        texts = self.reader.readtext(
            processed, 
            detail=0,
            paragraph=False,
            contrast_ths=0.15,
            text_threshold=0.4,
            allowlist='0123456789.'
        )

        return self._parse_amount(texts)
    
    def _preprocess(self, crop):
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        return gray

    def _parse_amount(self, texts: list[str]) -> float | None:
        if not texts:
            print("  [OCR] No text detected!")
            return None
        
        full_text = "".join(texts)
        full_text = full_text.replace(",", "").replace(" ", "").strip()

        print(f"  [Parse] Cleaned: '{full_text}'")

        replacements = {
            'S': '5', 's': '5',
            'I': '1', 'l': '1', '|': '1',
            'O': '0', 'o': '0',
            'B': '8', 'b': '8',
        }
        for old, new in replacements.items():
            full_text = full_text.replace(old, new)

        match = re.search(r'\d+(\.\d+)?', full_text)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass

        return None
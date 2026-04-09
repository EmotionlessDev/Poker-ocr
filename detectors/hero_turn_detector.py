import cv2
import numpy as np
from domain.geometry import Rect
import time
import easyocr


class HeroTurnDetector:
    """
    Детектирует, дошла ли очередь до героя.
    Ищет красные кнопки действий + текст (FOLD, CALL, RAISE, BET)
    """
    
    def __init__(self):
        # Зона где обычно находятся кнопки
        self.button_zone_ratio = {
            'x_start': 0.60,
            'y_start': 0.65,
            'x_end': 1.0,
            'y_end': 0.98
        }
        
        # Красный цвет кнопок (HSV)
        self.lower_red1 = np.array([0, 120, 120])
        self.upper_red1 = np.array([10, 255, 255])
        self.lower_red2 = np.array([160, 120, 120])
        self.upper_red2 = np.array([180, 255, 255])
        
        # Минимальное количество красных пикселей
        self.min_red_pixels = 10000
        
        # Keywords для поиска
        self.keywords = ["FOLD", "CALL", "RAISE", "BET"]
        
        # OCR reader (ленивая инициализация)
        self._reader = None
        
        # Кэш последнего состояния
        self.last_state = False
        self.consecutive_frames = 0
        self.stable_threshold = 2

    @property
    def reader(self):
        """Ленивая инициализация OCR"""
        if self._reader is None:
            self._reader = easyocr.Reader(['en'], gpu=True, verbose=False)
        return self._reader

    def _detect_keywords(self, button_zone: np.ndarray) -> bool:
        """
        Ищет keywords (FOLD, CALL, RAISE, BET) в зоне кнопок.
        Возвращает True если найден хотя бы один keyword.
        """
        if button_zone.size == 0:
            return False
        
        # Конвертируем в серый для лучшего OCR
        gray = cv2.cvtColor(button_zone, cv2.COLOR_BGR2GRAY)
        
        # Увеличиваем контраст
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        
        # Бинаризация (белый текст на тёмном фоне)
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        
        # OCR
        try:
            results = self.reader.readtext(
                thresh,
                detail=0,
                paragraph=False,
                contrast_ths=0.3,
                text_threshold=0.3
            )
            
            # Ищем keywords
            found_keywords = []
            for text in results:
                text_upper = text.upper().strip()
                for keyword in self.keywords:
                    if keyword in text_upper:
                        found_keywords.append(keyword)
            
            if found_keywords:
                print(f"   📝 Found keywords: {found_keywords}")
                return True
            
        except Exception as e:
            print(f"   ⚠️ OCR error: {e}")
            return False
        
        return False

    def detect(self, frame: np.ndarray) -> bool:
        h, w = frame.shape[:2]
        
        # 1. Выделяем зону кнопок
        x1 = int(w * self.button_zone_ratio['x_start'])
        y1 = int(h * self.button_zone_ratio['y_start'])
        x2 = int(w * self.button_zone_ratio['x_end'])
        y2 = int(h * self.button_zone_ratio['y_end'])
        
        button_zone = frame[y1:y2, x1:x2]
        
        if button_zone.size == 0:
            return False
        
        # 2. HSV + маска красного
        hsv = cv2.cvtColor(button_zone, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # 3. Морфология
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        # 4. Считаем пиксели
        red_pixels = cv2.countNonZero(mask)
        zone_area = button_zone.shape[0] * button_zone.shape[1]
        red_ratio = red_pixels / zone_area * 100
        
        # 5. Проверяем наличие кнопок (красный цвет ИЛИ текст)
        has_red_buttons = red_pixels > self.min_red_pixels
        has_keywords = self._detect_keywords(button_zone)
        
        # Комбинируем оба условия
        current_state = has_red_buttons and has_keywords
        
        # 6. Debug
        if current_state != self.last_state:
            print(f"🔍 Hero turn {'DETECTED' if current_state else 'ENDED'}: "
                f"Red={red_pixels}, Keywords={has_keywords}")
        
        # 7. Стабилизация
        if current_state:
            self.consecutive_frames += 1
        else:
            self.consecutive_frames = 0
        
        # Меняем состояние если стабильно N кадров
        if self.consecutive_frames >= self.stable_threshold:
            if not self.last_state:
                print(f"✅ Hero turn DETECTED!")
            self.last_state = True
        else:
            self.last_state = False
        
        return self.last_state
from PIL.ImageOps import crop
import cv2
import numpy as np
from domain.geometry import Rect
import time


def refine_zone_by_dark_panel(
    frame,
    zone: Rect,
    padding: int = 8,
    min_area_ratio: float = 0.05,
) -> Rect | None:
    """
    Уточняет зону игрока по тёмной панели внутри грубой зоны.

    frame: BGR изображение (cv2)
    zone: грубая зона (Rect)
    padding: расширение итоговой рамки
    min_area_ratio: минимальная площадь найденного контура
                    относительно ROI (чтобы отсеять шум)
    """

    # --- Безопасность координат ---
    h, w = frame.shape[:2]

    x1 = max(0, zone.x1)
    y1 = max(0, zone.y1)
    x2 = min(w, zone.x2)
    y2 = min(h, zone.y2)

    if x2 <= x1 or y2 <= y1:
        return zone

    roi = frame[y1:y2, x1:x2]

    if roi.size == 0:
        return zone

    # --- HSV маска тёмного ---
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    lower = np.array([0, 0, 0])
    upper = np.array([180, 255, 70])

    mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # --- Контуры ---
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    # --- Берём самый большой контур ---
    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)

    roi_area = roi.shape[0] * roi.shape[1]

    # если контур слишком маленький — игнорируем
    if area < roi_area * min_area_ratio:
        return None

    x, y, w_box, h_box = cv2.boundingRect(largest)

    refined = Rect(
        x1 + x - padding,
        y1 + y - padding,
        x1 + x + w_box + padding,
        y1 + y + h_box + padding,
    )

    # --- Ограничение рамки в пределах экрана ---
    refined = Rect(
        max(0, refined.x1),
        max(0, refined.y1),
        min(w, refined.x2),
        min(h, refined.y2),
    )

    return refined

def find_bet_panel_in_zone(frame, zone):
    """
    Находит панель со ставкой.
    Если avatar_zone передан — используем как fallback.
    """
    if zone is None:
        return None

    x1, y1, x2, y2 = zone.x1, zone.y1, zone.x2, zone.y2
    h, w = frame.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    if x2 <= x1 or y2 <= y1:
        return None

    crop = frame[y1:y2, x1:x2]
    crop_area = crop.shape[0] * crop.shape[1]
    
    # === 1. ГРАДИЕНТНАЯ маска (лучше для тёмных панелей) ===
    # Полупрозрачный чёрный лучше детектится через градиенты
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    
    # Тёмные области (адаптивный порог)
    _, mask_dark = cv2.threshold(gray, 70, 255, cv2.THRESH_BINARY_INV)
    
    # Белые цифры (яркие)
    _, mask_bright = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    # Морфология
    kernel = np.ones((3, 3), np.uint8)
    mask_dark = cv2.morphologyEx(mask_dark, cv2.MORPH_CLOSE, kernel)
    mask_bright = cv2.dilate(mask_bright, kernel, iterations=1)
    
    # === 2. Ищем контуры ===
    contours, _ = cv2.findContours(
        mask_dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    # === 3. АДАПТИВНАЯ фильтрация ===
    candidates = []
    
    for cnt in contours:
        bx, by, bw, bh = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)
        
        # Более мягкие фильтры
        if area < crop_area * 0.01 or area > crop_area * 0.6:
            continue
        
        # Минимальный размер (меньше для "4")
        if bw < 20 or bh < 10:
            continue
        
        # АДАПТИВНЫЙ aspect ratio
        # "4" → ~1.5-2.5, "100" → ~3-5, "2443" → ~4-6
        aspect_ratio = bw / float(bh)
        if aspect_ratio < 1.0 or aspect_ratio > 6.0:
            continue
        
        # === 4. Проверка белых цифр ===
        roi_x, roi_y = max(0, bx), max(0, by)
        roi_w, roi_h = min(crop.shape[1] - bx, bw), min(crop.shape[0] - by, bh)
        
        bright_roi = mask_bright[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
        bright_pixels = cv2.countNonZero(bright_roi)
        roi_area = roi_w * roi_h
        
        # Адаптивный порог (для "4" нужно меньше)
        min_bright = max(8, int(roi_area * 0.02))
        if bright_pixels < min_bright:
            continue
        
        bright_ratio = bright_pixels / roi_area if roi_area > 0 else 0
        if bright_ratio < 0.02 or bright_ratio > 0.7:
            continue
        
        # === 5. Проверка формы (не круглая как аватар) ===
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        
        circularity = 4 * np.pi * (area / (perimeter * perimeter))
        
        # Аватарки круглые (>0.85), панели овальные (0.5-0.8)
        if circularity > 0.85:
            continue
        
        # === 6. Score ===
        score = area * bright_ratio * (1 + bright_pixels / 100)
        
        candidates.append({
            'cnt': cnt,
            'bbox': (bx, by, bw, bh),
            'score': score,
            'bright_pixels': bright_pixels,
            'aspect_ratio': aspect_ratio
        })
    
    # === 7. Выбираем лучшего ===
    if candidates:
        candidates.sort(key=lambda x: x['score'], reverse=True)
        best = candidates[0]
        bx, by, bw, bh = best['bbox']
        
        # Debug
        # timestamp = int(time.time() * 1000)
        # debug_crop = crop.copy()
        # cv2.rectangle(debug_crop, (bx, by), (bx + bw, by + bh), (0, 255, 0), 2)
        # cv2.putText(debug_crop, f"AR:{best['aspect_ratio']:.1f}", 
        #            (bx, by-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        # cv2.imwrite(f"./debug/bet_panel_{timestamp}.png", debug_crop)
        
        padding = 3
        return Rect(
            x1 + max(0, bx - padding),
            y1 + max(0, by - padding),
            x1 + min(crop.shape[1], bx + bw + padding),
            y1 + min(crop.shape[0], by + bh + padding)
        )
    
    return None
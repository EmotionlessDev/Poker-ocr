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
    Находит панель со ставкой по комбинации признаков:
    - Тёмный фон
    - Яркие цифры внутри
    - Определённый aspect ratio
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
    
    # === 1. Ищем тёмные области (фон панели) ===
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    
    # Тёмные цвета (плашка)
    lower_dark = np.array([0, 0, 0])
    upper_dark = np.array([180, 255, 80])  # Немного ярче
    mask_dark = cv2.inRange(hsv, lower_dark, upper_dark)
    
    # === 2. Ищем яркие области (цифры) ===
    # Белые/светлые цифры
    lower_bright = np.array([0, 0, 200])
    upper_bright = np.array([180, 20, 255])
    mask_bright = cv2.inRange(hsv, lower_bright, upper_bright)
    
    # Морфология для цифр
    kernel_small = np.ones((2, 2), np.uint8)
    mask_bright = cv2.morphologyEx(mask_bright, cv2.MORPH_CLOSE, kernel_small)
    mask_bright = cv2.dilate(mask_bright, kernel_small, iterations=1)
    
    # === 3. Ищем контуры тёмных областей ===
    kernel = np.ones((5, 5), np.uint8)
    mask_dark = cv2.morphologyEx(mask_dark, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(
        mask_dark,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    # === 4. Фильтруем контуры ===
    candidates = []
    crop_area = crop.shape[0] * crop.shape[1]
    
    for cnt in contours:
        bx, by, bw, bh = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)
        
        # Фильтр по размеру
        if area < crop_area * 0.02 or area > crop_area * 0.5:
            continue
        
        if bw < 30 or bh < 15:
            continue
        
        # Aspect ratio (панель обычно шире чем высокая)
        aspect_ratio = bw / float(bh)
        if aspect_ratio < 1.2 or aspect_ratio > 4.0:
            continue
        
        # === 5. Проверяем наличие ярких цифр внутри ===
        # Берём ROI тёмной области
        roi_x, roi_y = max(0, bx - 5), max(0, by - 5)
        roi_w, roi_h = min(crop.shape[1] - roi_x, bw + 10), min(crop.shape[0] - roi_y, bh + 10)
        
        bright_roi = mask_bright[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
        bright_pixels = cv2.countNonZero(bright_roi)
        
        # Должно быть достаточно ярких пикселей (цифры)
        if bright_pixels < 20:  # Минимум цифр
            continue
        
        # Яркие пиксели должны быть внутри тёмной области
        bright_ratio = bright_pixels / (roi_w * roi_h)
        if bright_ratio < 0.05 or bright_ratio > 0.5:
            continue
        
        # === 6. Проверяем форму (овальная/закруглённая) ===
        # Approximate contour
        epsilon = 0.02 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        
        # Овалы обычно имеют 4+ вершины после аппроксимации
        # Или можно проверить circularity
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        
        circularity = 4 * np.pi * (area / (perimeter * perimeter))
        
        # Панель не идеальный круг, но и не прямоугольник
        # circularity ~ 0.6-0.8 для овалов
        if circularity < 0.4 or circularity > 0.85:
            continue
        
        # === 7. Считаем score ===
        score = area * bright_ratio * circularity
        
        candidates.append({
            'cnt': cnt,
            'bbox': (bx, by, bw, bh),
            'score': score,
            'bright_pixels': bright_pixels
        })
    
    if not candidates:
        return None
    
    # === 8. Выбираем лучший кандидат ===
    # Сортируем по score (площадь * наличие цифр * форма)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    best = candidates[0]
    
    bx, by, bw, bh = best['bbox']
    
    # Добавляем небольшой padding
    padding = 3

    timestamp = int(time.time() * 1000)
    debug_crop = crop.copy()
    cv2.rectangle(debug_crop, (bx, by), (bx + bw, by + bh), (0, 255, 0), 2)
    cv2.imwrite(f"./debug/bet_panel_{timestamp}.png", debug_crop)
    # cv2.imwrite(f"./debug/mask_dark_{timestamp}.png", mask_dark)
    # cv2.imwrite(f"./debug/mask_bright_{timestamp}.png", mask_bright)
    return Rect(
        x1 + max(0, bx - padding),
        y1 + max(0, by - padding),
        x1 + min(crop.shape[1], bx + bw + padding),
        y1 + min(crop.shape[0], by + bh + padding)
    )
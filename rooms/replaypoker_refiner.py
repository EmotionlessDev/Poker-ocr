import cv2
import numpy as np
from domain.geometry import Rect


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
    """Находит панель со ставкой (тёмный прямоугольник с цифрами)"""
    if zone is None:
        return None

    x1, y1, x2, y2 = zone.x1, zone.y1, zone.x2, zone.y2
    h, w = frame.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    if x2 <= x1 or y2 <= y1:
        return None

    crop = frame[y1:y2, x1:x2]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    # Тёмные цвета (плашка ставки)
    lower = np.array([0, 0, 0])
    upper = np.array([180, 255, 60])
    mask = cv2.inRange(hsv, lower, upper)

    # Сглаживаем
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    # Берём самый большой тёмный прямоугольник
    best = max(contours, key=cv2.contourArea)
    bx, by, bw, bh = cv2.boundingRect(best)

    # Фильтр — чтобы не схватить весь стол
    if bw < 25 or bh < 10:
        return None

    return Rect(
        x1 + bx,
        y1 + by,
        x1 + bx + bw,
        y1 + by + bh
    )
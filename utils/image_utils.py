import numpy as np
import cv2

def safe_crop(frame, rect):
    """Возвращает None если кроп выходит за границы или пуст."""
    h, w = frame.shape[:2]
    x1 = max(0, int(rect.x1))
    y1 = max(0, int(rect.y1))
    x2 = min(w, int(rect.x2))
    y2 = min(h, int(rect.y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return frame[y1:y2, x1:x2]

def prepare_nn_canvas(crop, target_w=1280, target_h=800):
    """
    Центрирует crop в canvas фиксированного размера.
    Если crop больше canvas — ресайзим пропорционально.
    """
    if crop is None or crop.size == 0:
        return np.zeros((target_h, target_w, 3), dtype=np.uint8)

    h, w = crop.shape[:2]

    # scale down if too large
    if w > target_w or h > target_h:
        scale = min(target_w / w, target_h / h)
        w_new = int(w * scale)
        h_new = int(h * scale)
        crop = cv2.resize(crop, (w_new, h_new))
        h, w = h_new, w_new

    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    x_offset = (target_w - w) // 2
    y_offset = (target_h - h) // 2
    canvas[y_offset:y_offset+h, x_offset:x_offset+w] = crop
    return canvas
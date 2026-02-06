import cv2
import numpy as np
from domain.geometry import Point, Rect


class TableCenterEstimator:
    def estimate_from_panels(self, panels, frame=None):
        import cv2
        import numpy as np
        from domain.geometry import Point

        # Если достаточно панелей, используем их
        if len(panels) >= 3:
            points = np.array([[(p.x1 + p.x2)//2, (p.y1 + p.y2)//2] for p in panels], dtype=np.float32)
            (cx, cy), radius = cv2.minEnclosingCircle(points)
            return Point(int(cx), int(cy))

        # TODO: Доделать..
        # Fallback: поиск стола по цвету
        # if frame is not None:
        #     hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        #     lower_table = np.array([0, 0, 200])   # серый-белый, V высокая
        #     upper_table = np.array([180, 30, 255])
        #     mask = cv2.inRange(hsv, lower_table, upper_table)
        #     contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        #     if contours:
        #         largest = max(contours, key=cv2.contourArea)
        #         x, y, w, h = cv2.boundingRect(largest)
        #         return Point(x + w//2, y + h//2)

        return None

import cv2
from domain.geometry import Rect

class PanelDetector:
    def __init__(self, ui_profile):
        self.profile = ui_profile

    def detect(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(
            hsv,
            self.profile.panel_color.lower,
            self.profile.panel_color.upper
        )

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        panels = []
        h_img, w_img = frame.shape[:2]

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            g = self.profile.panel_geometry

            if w < g.min_width or h < g.min_height:
                continue
            if w > 0.6 * w_img:
                continue

            aspect = w / h
            if not (g.aspect_min <= aspect <= g.aspect_max):
                continue

            panels.append(Rect(x, y, x + w, y + h))

        return panels

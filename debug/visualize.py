import cv2
from domain.geometry import Rect

class DebugVisualizer:
    @staticmethod
    def draw_panels(frame, panels, color=(0, 255, 0)):
        for p in panels:
            cv2.rectangle(
                frame,
                (p.x1, p.y1),
                (p.x2, p.y2),
                color,
                2
            )

    @staticmethod
    def draw_table_center(frame, center):
        if center is None:
            return

        cv2.circle(
            frame,
            (center.x, center.y),
            8,
            (0, 0, 255),
            -1
        )

    @staticmethod
    def draw_rect(frame, rect: Rect, color=(255, 0, 0), thickness=2):
        cv2.rectangle(
            frame,
            (rect.x1, rect.y1),
            (rect.x2, rect.y2),
            color,
            thickness
        )

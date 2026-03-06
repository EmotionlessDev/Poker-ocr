import cv2
import numpy as np


class DealerButtonDetector:

    def __init__(self, template_path: str, threshold: float = 0.75):

        self.template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        self.template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)

        self.w = self.template.shape[1]
        self.h = self.template.shape[0]

        self.threshold = threshold

    def detect(self, frame):

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(
            gray,
            self.template_gray,
            cv2.TM_CCOEFF_NORMED
        )

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        if max_val < self.threshold:
            return None

        x, y = max_loc

        center = (x + self.w // 2, y + self.h // 2)

        return center
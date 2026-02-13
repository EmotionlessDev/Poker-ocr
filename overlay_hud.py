import sys
import win32gui
import numpy as np
import mss
import cv2
import math

from PyQt6 import QtWidgets, QtGui, QtCore

from app.pipeline import PokerVisionPipeline


# -----------------------------
# KEYWORDS
# -----------------------------
_POKER_KEYWORDS = [
    "replaypoker", "replay poker", "casino.org",
    "- nl ", "- pl ", "hold'em", "holdem", "omaha",
    "no limit", "pot limit", "stakes", "tournament",
    "ring game", "sit & go",
]


# -----------------------------
# Find window
# -----------------------------
def find_poker_window():
    candidates = []

    def enum_callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return

        title = win32gui.GetWindowText(hwnd)
        if not title:
            return

        title_lower = title.lower()
        score = sum(1 for kw in _POKER_KEYWORDS if kw in title_lower)

        if score > 0:
            candidates.append((score, hwnd, title))

    win32gui.EnumWindows(enum_callback, None)

    if not candidates:
        return None

    candidates.sort(reverse=True, key=lambda x: x[0])
    best = candidates[0]
    print(f"Найдено окно: {best[2]}")
    return best[1]


def get_window_rect(hwnd):
    x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)
    return x1, y1, x2 - x1, y2 - y1


# -----------------------------
# Overlay HUD
# -----------------------------
class OverlayHUD(QtWidgets.QWidget):
    def __init__(self, hwnd):
        super().__init__()

        self.hwnd = hwnd
        self.pipeline_result = None

        self.pipeline = PokerVisionPipeline(seats=6)
        self.sct = mss.mss()

        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Tool
        )

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.update_position()

        # Обновление позиции окна
        self.pos_timer = QtCore.QTimer()
        self.pos_timer.timeout.connect(self.update_position)
        self.pos_timer.start(100)

        # Обработка кадра (10 FPS)
        self.cv_timer = QtCore.QTimer()
        self.cv_timer.timeout.connect(self.process_frame)
        self.cv_timer.start(100)

    def update_position(self):
        if not win32gui.IsWindow(self.hwnd):
            self.close()
            return

        x, y, w, h = get_window_rect(self.hwnd)
        self.setGeometry(x, y, w, h)

    def process_frame(self):
        x, y, w, h = get_window_rect(self.hwnd)

        monitor = {
            "left": x,
            "top": y,
            "width": w,
            "height": h,
        }

        screenshot = self.sct.grab(monitor)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        self.pipeline_result = self.pipeline.process(frame)
        self.update()

    def paintEvent(self, event):
        if self.pipeline_result is None:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Центр стола
        center = self.pipeline_result["table_center"]

        pen = QtGui.QPen(QtGui.QColor(0, 0, 255))
        pen.setWidth(10)
        painter.setPen(pen)
        painter.drawPoint(center.x, center.y)
        painter.drawText(20, 20, f"{self.width()} x {self.height()}")

        # Позиции игроков
        pen = QtGui.QPen(QtGui.QColor(0, 255, 0))
        pen.setWidth(3)
        painter.setPen(pen)

        for p in self.pipeline_result["player_positions"]:
            painter.drawEllipse(p.x - 12, p.y - 12, 24, 24)
            painter.drawRect(p.x - 60, p.y - 25, 120, 50)


# -----------------------------
# MAIN
# -----------------------------
def main():
    app = QtWidgets.QApplication(sys.argv)

    hwnd = find_poker_window()
    if not hwnd:
        print("Окно не найдено")
        return

    overlay = OverlayHUD(hwnd)
    overlay.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

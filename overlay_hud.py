
import sys
import time
import mss
import numpy as np
from PyQt6 import QtWidgets, QtGui, QtCore

from ui_profiles.replay import REPLAYPOKER_PROFILE
from detectors.panel_detector import PanelDetector
from app.pipeline import PokerVisionPipeline
from debug.visualize import DebugVisualizer

# ---------------- PyQt Overlay ----------------
class Overlay(QtWidgets.QWidget):
    def __init__(self, geometry):
        super().__init__()

        # Frameless, прозрачное окно поверх всех
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.Tool
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(*geometry)  # x, y, width, height

        self.pipeline_result = None

    def set_pipeline_result(self, result):
        self.pipeline_result = result
        self.update()  # перерисовка

    def paintEvent(self, event):
        if self.pipeline_result is None:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Рисуем панели
        pen = QtGui.QPen(QtGui.QColor(0, 255, 0))
        pen.setWidth(2)
        painter.setPen(pen)
        for p in self.pipeline_result["panels"]:
            painter.drawRect(p.x1, p.y1, p.x2 - p.x1, p.y2 - p.y1)

        # Рисуем центр стола
        center = self.pipeline_result.get("table_center")
        if center:
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            painter.drawEllipse(center.x - 5, center.y - 5, 10, 10)

        # Рисуем зону общих карт
        comm = self.pipeline_result.get("community_zone")
        if comm:
            pen = QtGui.QPen(QtGui.QColor(0, 0, 255))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(comm.x1, comm.y1, comm.x2 - comm.x1, comm.y2 - comm.y1)

# ----------------- Main -----------------
def main():
    # Настройка PyQt приложения
    app = QtWidgets.QApplication(sys.argv)

    # Геометрия overlay: весь экран (можно подставить координаты окна браузера)
    screen = app.primaryScreen()
    geometry = (0, 0, screen.size().width(), screen.size().height())

    overlay = Overlay(geometry)
    overlay.show()

    # ----------------- Инициализация пайплайна -----------------
    panel_detector = PanelDetector(REPLAYPOKER_PROFILE)
    pipeline = PokerVisionPipeline(panel_detector)

    # ----------------- Захват экрана -----------------
    sct = mss.mss()
    monitor = sct.monitors[1]  # основной монитор

    # Таймер для обновления overlay ~30 FPS
    def update():
        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

        result = pipeline.process(frame)
        overlay.set_pipeline_result(result)

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(33)  # примерно 30 FPS

    sys.exit(app.exec())

if __name__ == "__main__":
    import cv2
    main()

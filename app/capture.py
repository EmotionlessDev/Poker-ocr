import win32gui
import mss
import numpy as np
import cv2

def get_window_rect(hwnd):
    x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)
    return x1, y1, x2 - x1, y2 - y1

def capture_window(hwnd):
    x, y, w, h = get_window_rect(hwnd)
    with mss.mss() as sct:
        monitor = {"left": x, "top": y, "width": w, "height": h}
        screenshot = sct.grab(monitor)
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    return frame
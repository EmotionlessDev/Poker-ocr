import numpy as np
import mss
import time
from datetime import datetime

from ui_profiles.replay import REPLAYPOKER_PROFILE
from detectors.panel_detector import PanelDetector
from app.pipeline import PokerVisionPipeline
from debug.visualize import DebugVisualizer
from domain.geometry import Rect

# --- Инициализация пайплайна ---
panel_detector = PanelDetector(REPLAYPOKER_PROFILE)
pipeline = PokerVisionPipeline(panel_detector)

# --- Захват экрана ---
with mss.mss() as sct:
    monitor = sct.monitors[1]  # основной монитор
    print("Нажмите 'q', чтобы выйти...")

    last_save_time = time.time()  # время последнего сохранения
    save_interval = 10  # каждые 10 секунд

    while True:
        # Захват кадра
        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)  # RGBA
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

        # --- Обработка пайплайном ---
        result = pipeline.process(frame)

        # --- Отрисовка ---
        DebugVisualizer.draw_panels(frame, result["panels"])
        DebugVisualizer.draw_table_center(frame, result["table_center"])
        DebugVisualizer.draw_rect(frame, result["community_zone"], color=(0, 0, 255), thickness=2)

        # --- Сохраняем каждые 10 секунд ---
        current_time = time.time()
        if current_time - last_save_time >= save_interval:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshots/screenshot_{timestamp}.png"
            cv2.imwrite(filename, frame)
            print(f"[INFO] Screenshot saved: {filename}")
            last_save_time = current_time

        # --- Показываем кадр ---
        cv2.imshow("Poker Vision Real-Time", frame)

        # --- Выход по 'q' ---
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()


import argparse
import time
import win32gui
import logging
from app import state_manager
from poker_app.capture import capture_window
from poker_app.state_manager import PokerStateManager

def find_poker_window():
    keywords = ["replaypoker", "holdem", "omaha"]
    candidates = []

    def enum_callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if title and any(k in title.lower() for k in keywords):
            candidates.append(hwnd)

    win32gui.EnumWindows(enum_callback, None)
    return candidates[0] if candidates else None

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument("--room", default="replaypoker")
    parser.add_argument("--seats", type=int, default=6)
    parser.add_argument("--hero", default="Elots")
    args = parser.parse_args()

    hwnd = find_poker_window()
    if not hwnd:
        print("❌ Окно не найдено")
        return
    
    title = win32gui.GetWindowText(hwnd)
    print(f"✅ Найдено окно: {title}")

    state_manager = PokerStateManager(
        room_name=args.room, 
        seats=args.seats, 
        hero_nickname=args.hero,
        hwnd=hwnd,
        enable_overlay=True  # Включаем оверлей по умолчанию
    )

    try:
        while True:
            frame = capture_window(hwnd)
            state_manager.update_from_frame(frame)
            
    except KeyboardInterrupt:
        print("\nStopped")
        if state_manager.enable_overlay:
            state_manager.overlay_window.hide_overlay()

if __name__ == "__main__":
    main()
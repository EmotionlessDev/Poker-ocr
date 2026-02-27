import argparse
import time
import win32gui
from app.capture import capture_window
from app.state_manager import PokerStateManager

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
    parser = argparse.ArgumentParser()
    parser.add_argument("--room", default="replaypoker")
    parser.add_argument("--seats", type=int, default=6)
    args = parser.parse_args()

    hwnd = find_poker_window()
    if not hwnd:
        print("Окно не найдено")
        return

    state_manager = PokerStateManager(args.room, args.seats, hero_nickname="Elots")  # TODO: получать ник героя от пользователя

    try:
        while True:
            frame = capture_window(hwnd)
            state_manager.update_from_frame(frame)
            
            # Печатаем состояние стола для отладки
            print(state_manager.table)
            time.sleep(0.1)

    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
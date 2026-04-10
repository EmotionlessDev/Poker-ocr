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
        hwnd=hwnd
    )

    try:
        while True:
            frame = capture_window(hwnd)
            state_manager.update_from_frame(frame)
            
            # Показываем Debug инфу ТОЛЬКО когда очередь героя
            if state_manager.table.is_hero_turn:
                hero_turn_icon = "🟢"
                print(f"\n{hero_turn_icon} Hero turn: {state_manager.table.is_hero_turn}")
                
                # Печатаем состояние стола
                print("Players:")
                for p in state_manager.table.players:
                    print(f"  seat {p.seat}: (Hero: {p.is_hero}, Position: {p.position}, "
                        f"Nickname: {p.nickname}, Active: {p.is_active}, Bet: {p.last_bet})")
                print(f"Community cards: {state_manager.table.community_cards}")
                print(f"Hero cards: {next((p.cards for p in state_manager.table.players if p.is_hero), [])}")
                print("=" * 50)
            else:
                print(".", end="", flush=True)
                time.sleep(0.5)
                continue
            
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopped by user")

if __name__ == "__main__":
    main()
from domain.geometry import Rect, Point
from .base import BaseRoomGeometry
from .replaypoker_refiner import refine_zone_by_dark_panel, find_bet_panel_in_zone
import win32gui
import re

class ReplayPokerGeometry(BaseRoomGeometry):
    BLIND_PATTERN = r'(\d+)/(\d+)\s*-\s*NL\s*Holdem'

    def compute_table_center(self, frame_shape):
        h, w = frame_shape[:2]
        return Point(w // 2, h // 2)

    def compute_community_zone(self, table_center, table_rect):
        zone_w_ratio = 0.45
        zone_h_ratio = 0.15
        vert_offset_ratio = -0.05

        w = int(table_rect.width * zone_w_ratio)
        h = int(table_rect.width * zone_h_ratio)

        cx = table_center.x
        cy = table_center.y + int(table_rect.height * vert_offset_ratio)

        return Rect(
            cx - w // 2,
            cy - h // 2,
            cx + w // 2,
            cy + h // 2
        )

    def compute_player_zones(self, table_rect, frame=None):
        table_center = self.compute_table_center(frame.shape)
      
        seat_ratios = [
            (0.68, 0.67), 
            (0.81, 0.46),
            (0.68, 0.25),
            (0.32, 0.25),
            (0.20, 0.46),
            (0.32, 0.67),
        ]

        zone_w_ratio = 0.25
        zone_h_ratio = 0.12

        zones = []

        for rx, ry in seat_ratios:
            cx = int(table_rect.width * rx)
            cy = int(table_rect.height * ry)

            w = int(table_rect.width * zone_w_ratio)
            h = int(table_rect.height * zone_h_ratio)

            zones.append(Rect(
                cx - w // 2,
                cy - h // 2,
                cx + w // 2,
                cy + h // 2
            ))

        if frame is not None:
            refined = []
            for z in zones:
                refined_zone = refine_zone_by_dark_panel(frame, z)
                if refined_zone is None:
                    refined.append(None)
                    continue
            
                # Expand the refined zone to include the player's cards and stack
                refined_zone = refined_zone.expand_towards(
                    target=table_center,
                    expand_main=140,
                    expand_cross=50,
                    bounds=frame.shape
                )

                refined.append(refined_zone)


            zones= refined
            return zones

    # def compute_bet_zones(self, player_zones, table_center) -> list[Rect]:
    #     bet_zones = []

    #     for zone in player_zones:
    #         if zone is None:
    #             bet_zones.append(None)
    #             continue

    #         px = (zone.x1 + zone.x2) // 2
    #         py = (zone.y1 + zone.y2) // 2

    #         # --- смещение только по X (в центр)
    #         if px < table_center.x:
    #             # игрок слева → двигаем вправо
    #             cx = px + 110
    #         else:
    #             # игрок справа → двигаем влево
    #             cx = px - 110

    #         # --- Y почти не трогаем
    #         cy = py

    #         w = 160
    #         h = 100

    #         bet_zones.append(Rect(
    #             cx - w // 2,
    #             cy - h // 2,
    #             cx + w // 2,
    #             cy + h // 2
    #         ))

    #     return bet_zones
    
    def compute_bet_zones(self, player_zones, table_center, frame=None) -> list[Rect]:
        """
        Вычисляет зоны для ставок.
        Если передан frame, то находит конкретные панели со ставками.
        """
        bet_zones = []

        for zone in player_zones:
            if zone is None:
                bet_zones.append(None)
                continue

            px = (zone.x1 + zone.x2) // 2
            py = (zone.y1 + zone.y2) // 2

            # Смещение только по X (в центр)
            if px < table_center.x:
                cx = px + 110
            else:
                cx = px - 110

            cy = py

            w = 160
            h = 100

            # Базовая зона (примерная)
            base_bet_zone = Rect(
                cx - w // 2,
                cy - h // 2,
                cx + w // 2,
                cy + h // 2
            )

            # Если есть frame, уточняем зону (ищем тёмную панель)
            if frame is not None:
                refined_bet_zone = find_bet_panel_in_zone(frame, base_bet_zone)
                bet_zones.append(refined_bet_zone)
            else:
                bet_zones.append(base_bet_zone)

        return bet_zones

    def get_table_info_from_hwnd(self, hwnd: int) -> dict:
        """
        Извлекает информацию о столе из заголовка окна.
        Возвращает: {"small_blind": 100, "big_blind": 200, "table_name": "...", "valid": True}
        """
        try:
            title = win32gui.GetWindowText(hwnd)
        except Exception as e:
            print(f"Error getting window title: {e}")
            return {"valid": False}
        
        if not title:
            return {"valid": False}
        
        # Парсим блайнды
        match = re.search(self.BLIND_PATTERN, title, re.IGNORECASE)
        
        if match:
            sb = float(match.group(1))
            bb = float(match.group(2))
            
            # Парсим название стола (опционально)
            parts = title.split(' - ')
            table_name = parts[1].strip() if len(parts) >= 3 else ""
            stakes_level = parts[0].strip() if len(parts) >= 1 else ""
            
            return {
                "small_blind": sb,
                "big_blind": bb,
                "table_name": table_name,
                "stakes_level": stakes_level,
                "valid": True
            }
        
        return {"valid": False}

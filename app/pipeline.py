from domain.geometry import Rect
from rooms.factory import get_room_geometry


class PokerVisionPipeline:

    def __init__(self, room: str, seats: int = 6):
        self.geometry = get_room_geometry(room, seats)

    def process(self, frame):
        h, w = frame.shape[:2]

        table_rect = Rect(0, 0, w, h)

        table_center = self.geometry.compute_table_center(frame.shape)
        community_zone = self.geometry.compute_community_zone(
            table_center,
            table_rect
        )
        player_zones = self.geometry.compute_player_zones(table_rect, frame=frame)
        bet_zones = self.geometry.compute_bet_zones(player_zones, table_center, frame=frame)

        return {
            "table_center": table_center,
            "community_zone": community_zone,
            "player_zones": player_zones,
            "bet_zones": bet_zones
        }
    
    def get_table_info(self, hwnd: int) -> dict:
        """Получает информацию о столе (блайнды, название) из заголовка окна"""
        return self.geometry.get_table_info_from_hwnd(hwnd)
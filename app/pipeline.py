from domain.geometry import (
    Rect,
    Point,
    compute_community_cards_zone,
    compute_player_positions
)


class PokerVisionPipeline:
    def __init__(self, seats: int = 6):
        self.seats = seats

    def process(self, frame):
        h, w = frame.shape[:2]

        # Центр = центр окна
        table_center = Point(w // 2, h // 2)

        # Стол = всё окно
        table_rect = Rect(0, 0, w, h)

        # Комьюнити карты
        community_zone = compute_community_cards_zone(
            table_center,
            table_rect
        )

        # Позиции игроков
        player_positions = compute_player_positions(table_rect)


        return {
            "table_center": table_center,
            "community_zone": community_zone,
            "player_positions": player_positions
        }

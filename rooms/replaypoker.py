from domain.geometry import Rect, Point
from .base import BaseRoomGeometry

class ReplayPokerGeometry(BaseRoomGeometry):

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

    def compute_player_zones(self, table_rect):

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

        return zones
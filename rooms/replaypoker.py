from domain.geometry import Rect, Point
from .base import BaseRoomGeometry
from .replaypoker_refiner import refine_zone_by_dark_panel

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
import math
from dataclasses import dataclass

@dataclass
class Rect:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self):
        return self.x2 - self.x1

    @property
    def height(self):
        return self.y2 - self.y1
    
    @property
    def center(self):
        return Point(
            (self.x1 + self.x2) // 2,
            (self.y1 + self.y2) // 2
        )
    
    def expand(self, left=0, top=0, right=0, bottom=0, bounds=None):
        x1 = self.x1 - left
        y1 = self.y1 - top
        x2 = self.x2 + right
        y2 = self.y2 + bottom

        if bounds is not None:
            h, w = bounds[:2]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

        return Rect(x1, y1, x2, y2)

    def expand_towards(self,
                       target: "Point",
                       expand_main=120,
                       expand_cross=40,
                       bounds=None) -> "Rect":

        cx, cy = self.center.x, self.center.y
        dx = target.x - cx
        dy = target.y - cy

        x1, y1, x2, y2 = self.x1, self.y1, self.x2, self.y2

        if abs(dx) > abs(dy):
            # горизонтальное направление
            if dx > 0:
                x2 += expand_main
            else:
                x1 -= expand_main

            y1 -= expand_cross
            y2 += expand_cross
        else:
            # вертикальное направление
            if dy > 0:
                y2 += expand_main
            else:
                y1 -= expand_main

            x1 -= expand_cross
            x2 += expand_cross

        if bounds is not None:
            h, w = bounds[:2]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)

        return Rect(x1, y1, x2, y2)
    
    
    
    

@dataclass
class Point:
    x: int
    y: int


# def compute_community_cards_zone(table_center: Point, table_rect: Rect) -> Rect:
#     """
#     Вычисляет пропорциональную зону для флопа/терна/ривера.
#     Коэффициенты можно подбирать под UI.
#     """
#     # коэффициенты (подбираются под твой UI)
#     zone_w_ratio = 0.45        # ширина зоны = 40% ширины стола
#     zone_h_ratio = 0.15        # высота зоны = 10% ширины стола (чтобы пропорции сохранялись)
#     vert_offset_ratio = -0.05 # вертикальный сдвиг относительно центра стола

#     w = int(table_rect.width * zone_w_ratio)
#     h = int(table_rect.width * zone_h_ratio)

#     cx = table_center.x
#     cy = table_center.y + int(table_rect.height * vert_offset_ratio)

#     x1 = cx - w // 2
#     y1 = cy - h // 2
#     x2 = cx + w // 2
#     y2 = cy + h // 2

#     return Rect(x1, y1, x2, y2)

# def compute_player_positions(table_rect: Rect) -> list[Point]:
#     """
#     Точные позиции 6-max ReplayPoker.
#     Масштабируются от размера окна.
#     """

#     seat_ratios = [

#         (0.68, 0.67),  # правый нижний
#         (0.81, 0.46),  # правый средний
#         (0.68, 0.25),  # правый верхний

#         (0.32, 0.25),  # левый верхний
#         (0.20, 0.46),  # левый средний
#         (0.32, 0.67),  # левый нижний
#     ]

#     positions = []

#     for rx, ry in seat_ratios:
#         x = int(table_rect.width * rx)
#         y = int(table_rect.height * ry)
#         positions.append(Point(x, y))

#     return positions

# def compute_player_zones(table_rect: Rect) -> list[Rect]:
#     """
#     Вычисляет прямоугольные зоны вокруг игроков.
#     Размеры зон подбираются под UI.
#     """
#     seat_ratios = [
#         (0.68, 0.67),  # правый нижний
#         (0.81, 0.46),  # правый средний
#         (0.68, 0.25),  # правый верхний
#         (0.32, 0.25),  # левый верхний
#         (0.20, 0.46),  # левый средний
#         (0.32, 0.67),  # левый нижний
#     ]

#     zones = []

#     # Пропорции прямоугольника зоны от размера стола
#     zone_w_ratio = 0.25
#     zone_h_ratio = 0.12

#     for rx, ry in seat_ratios:
#         cx = int(table_rect.width * rx)
#         cy = int(table_rect.height * ry)

#         w = int(table_rect.width * zone_w_ratio)
#         h = int(table_rect.height * zone_h_ratio)

#         x1 = cx - w // 2
#         y1 = cy - h // 2
#         x2 = cx + w // 2
#         y2 = cy + h // 2

#         zones.append(Rect(x1, y1, x2, y2))

#     return zones


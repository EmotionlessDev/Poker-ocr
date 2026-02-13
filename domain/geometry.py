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

@dataclass
class Point:
    x: int
    y: int


def compute_community_cards_zone(table_center: Point, table_rect: Rect) -> Rect:
    """
    Вычисляет пропорциональную зону для флопа/терна/ривера.
    Коэффициенты можно подбирать под UI.
    """
    # коэффициенты (подбираются под твой UI)
    zone_w_ratio = 0.45        # ширина зоны = 40% ширины стола
    zone_h_ratio = 0.15        # высота зоны = 10% ширины стола (чтобы пропорции сохранялись)
    vert_offset_ratio = -0.05 # вертикальный сдвиг относительно центра стола

    w = int(table_rect.width * zone_w_ratio)
    h = int(table_rect.width * zone_h_ratio)

    cx = table_center.x
    cy = table_center.y + int(table_rect.height * vert_offset_ratio)

    x1 = cx - w // 2
    y1 = cy - h // 2
    x2 = cx + w // 2
    y2 = cy + h // 2

    return Rect(x1, y1, x2, y2)

def compute_player_positions(table_rect: Rect) -> list[Point]:
    """
    Точные позиции 6-max ReplayPoker.
    Масштабируются от размера окна.
    """

    seat_ratios = [

        (0.68, 0.67),  # правый нижний
        (0.81, 0.46),  # правый средний
        (0.68, 0.25),  # правый верхний

        (0.32, 0.25),  # левый верхний
        (0.20, 0.46),  # левый средний
        (0.32, 0.67),  # левый нижний
    ]

    positions = []

    for rx, ry in seat_ratios:
        x = int(table_rect.width * rx)
        y = int(table_rect.height * ry)
        positions.append(Point(x, y))

    return positions

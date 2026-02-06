from dataclasses import dataclass
import numpy as np

@dataclass
class PanelColorRange:
    lower: np.ndarray
    upper: np.ndarray


@dataclass
class PanelGeometry:
    min_width: int
    min_height: int
    aspect_min: float
    aspect_max: float


@dataclass
class UIProfile:
    panel_color: PanelColorRange
    panel_geometry: PanelGeometry

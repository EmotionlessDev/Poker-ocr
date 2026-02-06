import numpy as np
from .base import UIProfile, PanelColorRange, PanelGeometry

REPLAYPOKER_PROFILE = UIProfile(
    panel_color=PanelColorRange(
        lower=np.array([0, 0, 0]),
        upper=np.array([180, 255, 80])
    ),
    panel_geometry=PanelGeometry(
        min_width=50,
        min_height=50,
        aspect_min=2.0,
        aspect_max=8.0
    )
)

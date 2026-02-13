import numpy as np
from .base import UIProfile, PanelColorRange, PanelGeometry

REPLAYPOKER_PROFILE = UIProfile(
    panel_color=PanelColorRange(
        # Dark player-info panels (low value, low-moderate saturation)
        lower=np.array([80, 15, 10]),
        upper=np.array([130, 120, 55])
    ),
    panel_geometry=PanelGeometry(
        min_width=80,
        min_height=30,
        aspect_min=1.5,
        aspect_max=6.0
    )
)

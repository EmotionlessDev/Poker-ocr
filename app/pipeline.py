class PokerVisionPipeline:
    def __init__(self, panel_detector):
        self.panel_detector = panel_detector

    def process(self, frame):
        panels = self.panel_detector.detect(frame)
        return panels

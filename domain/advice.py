from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List


class ActionRecommendation(Enum):
    FOLD = auto()
    CALL = auto()
    RAISE = auto()
    CHECK = auto()
    ALL_IN = auto()


class Confidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Advice:
    """Структурированная рекомендация для игрока"""
    
    action: ActionRecommendation
    confidence: Confidence
    reason: str  # Человекочитаемое объяснение
    
    # Дополнительные данные для отладки/расширения
    hand_strength: Optional[float] = None  # 0.0-1.0
    range_coverage: Optional[float] = None  # % рук в рендже
    alternative_actions: List[ActionRecommendation] = field(default_factory=list)
    
    def __str__(self) -> str:
        emoji = {
            ActionRecommendation.FOLD: "❌",
            ActionRecommendation.CALL: "🟡",
            ActionRecommendation.RAISE: "🟢",
            ActionRecommendation.CHECK: "⚪",
            ActionRecommendation.ALL_IN: "🔥",
        }.get(self.action, "❓")
        
        conf_icon = {
            Confidence.LOW: "⚠️",
            Confidence.MEDIUM: "✓",
            Confidence.HIGH: "✅",
        }.get(self.confidence, "?")
        
        return f"{emoji} {self.action.name} {conf_icon} — {self.reason}"
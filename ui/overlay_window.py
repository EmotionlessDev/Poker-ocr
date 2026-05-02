import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from .overlay_controller import OverlayData


class OverlayWindow(QWidget):
    """
    Прозрачное окно оверлея.
    - Always on top
    - Click-through (можно кликать сквозь окно)
    - Обновляется в real-time
    """
    
    def __init__(self):
        super().__init__()
        
        # Настройка окна
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |      # Без рамок
            Qt.WindowType.WindowStaysOnTopHint |     # Всегда поверх
            Qt.WindowType.Tool                       # Не показывать в taskbar
        )
        
        # Прозрачность
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Click-through (можно кликать сквозь окно)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Позиция и размер
        self.setGeometry(100, 100, 400, 300)
        
        # UI элементы
        self._init_ui()
        
        # Таймер для авто-обновления (опционально)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._refresh)
        self.update_timer.start(500)  # Обновление каждые 500ms
    
    def _init_ui(self):
        """Инициализация UI элементов"""
        layout = QVBoxLayout()
        
        # Заголовок
        self.title_label = QLabel(" PokerOCR Overlay")
        self.title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #00ff00; background: rgba(0,0,0,0.7); padding: 5px;")
        layout.addWidget(self.title_label)
        
        # Hero info
        self.hero_label = QLabel("Hero: --")
        self.hero_label.setFont(QFont("Arial", 11))
        self.hero_label.setStyleSheet("color: #ffffff; background: rgba(0,0,0,0.7); padding: 3px;")
        layout.addWidget(self.hero_label)
        
        # Table info
        self.table_label = QLabel("Table: --")
        self.table_label.setFont(QFont("Arial", 10))
        self.table_label.setStyleSheet("color: #aaaaaa; background: rgba(0,0,0,0.7); padding: 3px;")
        layout.addWidget(self.table_label)
        
        # Advice (самое важное)
        self.advice_label = QLabel("💡 Advice: --")
        self.advice_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.advice_label.setStyleSheet(
            "color: #00ff00; background: rgba(0,100,0,0.8); padding: 8px; border-radius: 5px;"
        )
        layout.addWidget(self.advice_label)
        
        # Status
        self.status_label = QLabel("Status: --")
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setStyleSheet("color: #888888; background: rgba(0,0,0,0.7); padding: 3px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def update_data(self, data: OverlayData):
        """Обновляет UI с новыми данными"""
        # Hero info
        hero_text = f"🦸 Hero: {data.hero_cards} ({data.hero_position})"
        if data.is_hero_turn:
            hero_text += " ⏰ YOUR TURN!"
        self.hero_label.setText(hero_text)
        
        # Table info
        self.table_label.setText(
            f"🪙 {data.blinds} | 👥 {data.active_players} players | "
            f"📊 {data.raises_count} raises | 🎯 {data.street}"
        )
        
        # Advice
        if data.advice_action:
            emoji = {"RAISE": "🟢", "FOLD": "❌", "CALL": "🟡"}.get(data.advice_action, "❓")
            conf_icon = {"HIGH": "✅", "MEDIUM": "✓", "LOW": "⚠️"}.get(data.advice_confidence, "?")
            self.advice_label.setText(f"💡 {emoji} {data.advice_action} {conf_icon} — {data.advice_reason}")
        else:
            self.advice_label.setText("💡 Advice: --")
        
        # Status
        status_emoji = {"OK": "✅", "ERROR": "❌", "WAITING": "⏳"}.get(data.parsing_status, "?")
        self.status_label.setText(f"{status_emoji} Status: {data.parsing_status}")
    
    def _refresh(self):
        """Авто-обновление (если нужно)"""
        pass  # Данные приходят через update_data()
    
    def show_overlay(self):
        """Показывает оверлей"""
        self.show()
    
    def hide_overlay(self):
        """Скрывает оверлей"""
        self.hide()
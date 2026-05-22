import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class OverlayWindow(QWidget):
    """
    Минималистичное прозрачное окно оверлея.
    - Always on top
    - Click-through (можно кликать сквозь окно)
    - Обновляется в real-time
    - Современный дизайн с цветовым кодированием
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
        
        # Позиция и размер (компактный)
        self.setGeometry(100, 100, 340, 220)
        
        # UI элементы
        self._init_ui()
        
        # Таймер для авто-обновления позиции (опционально)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._refresh)
        self.update_timer.start(500)
    
    def _init_ui(self):
        """Инициализация UI элементов"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Основной стиль контейнера
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 20, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
            QLabel {
                padding: 2px;
            }
        """)
        
        # Header: Table info and Stage
        self.title_label = QLabel("Table: Unknown | Preflop")
        self.title_label.setObjectName("headerLabel")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: 600;
                color: #AAAAAA;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                padding-bottom: 6px;
                margin-bottom: 4px;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Hero cards (крупно, моноширинный шрифт)
        self.hero_label = QLabel("Cards: --")
        self.hero_label.setObjectName("heroLabel")
        self.hero_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 700;
                color: #FFFFFF;
                font-family: 'Consolas', 'Monaco', monospace;
                letter-spacing: 1px;
            }
        """)
        layout.addWidget(self.hero_label)
        
        # Table info (позиция, пот, оппоненты)
        self.table_label = QLabel("Pos: - | Pot: 0 | Villains: 0")
        self.table_label.setObjectName("infoLabel")
        self.table_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #CCCCCC;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        layout.addWidget(self.table_label)
        
        # Advice (самое важное - с цветовым кодированием)
        self.advice_label = QLabel("WAITING FOR HAND...")
        self.advice_label.setObjectName("adviceLabel")
        self.advice_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.advice_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 800;
                padding: 10px;
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.05);
                color: #AAAAAA;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
        """)
        layout.addWidget(self.advice_label)
        
        # Status (маленький индикатор внизу)
        self.status_label = QLabel("● System Ready")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #4CAF50;
                font-style: italic;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
        """)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def update_data(self, data):
        """Обновляет UI с новыми данными"""
        if not data:
            self.reset()
            return
        
        # Header: Table name + Stage
        table_name = data.get('table_name', 'Unknown')
        stage = data.get('stage', 'Unknown')
        self.title_label.setText(f"Table: {table_name} | {stage}")
        
        # Hero cards
        cards = data.get('cards', '--')
        if cards:
            self.hero_label.setText(f"Cards: {cards}")
        else:
            self.hero_label.setText("Cards: --")
        
        # Table info
        pos = data.get('hero_pos', '-')
        pot = data.get('pot_size', 0)
        villains = data.get('villains_count', 0)
        self.table_label.setText(f"Pos: {pos} | Pot: {pot} | Villains: {villains}")
        
        # Advice с цветовым кодированием
        advice = data.get('advice', 'WAITING...')
        action = data.get('action', 'WAIT')
        
        self.advice_label.setText(advice)
        
        # Сброс стиля
        base_style = """
            QLabel {{
                font-size: 18px;
                font-weight: 800;
                padding: 10px;
                border-radius: 6px;
                text-align: center;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }}
        """
        
        # Цветовое кодирование действий
        if action in ['RAISE', '3BET', '4BET']:
            color = "#4CAF50"  # Зеленый - действие/агрессия
            bg = "rgba(76, 175, 80, 0.15)"
            self.advice_label.setStyleSheet(base_style.format("") + f"""
                background-color: {bg};
                color: {color};
                border: 1px solid {color};
            """)
        elif action in ['CALL', 'CHECK']:
            color = "#FFC107"  # Желтый - нейтральное действие
            bg = "rgba(255, 193, 7, 0.15)"
            self.advice_label.setStyleSheet(base_style.format("") + f"""
                background-color: {bg};
                color: {color};
                border: 1px solid {color};
            """)
        elif action == 'FOLD':
            color = "#F44336"  # Красный - отказ
            bg = "rgba(244, 67, 54, 0.15)"
            self.advice_label.setStyleSheet(base_style.format("") + f"""
                background-color: {bg};
                color: {color};
                border: 1px solid {color};
            """)
        else:
            # По умолчанию / ожидание
            self.advice_label.setStyleSheet(base_style.format("") + """
                background-color: rgba(255, 255, 255, 0.05);
                color: #AAAAAA;
            """)
        
        # Если не префлоп - скрываем совет
        if stage != 'Preflop' and stage != 'Unknown':
            self.advice_label.setText("POSTFLOP (No Analysis)")
            self.advice_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: 600;
                    padding: 10px;
                    border-radius: 6px;
                    background-color: rgba(255, 255, 255, 0.05);
                    color: #666666;
                    text-align: center;
                    font-family: 'Segoe UI', 'Roboto', sans-serif;
                    border: 1px dashed #444444;
                }
            """)
        
        # Status
        status = data.get('status', 'OK')
        status_color = {"OK": "#4CAF50", "ERROR": "#F44336", "WAITING": "#FFC107"}.get(status, "#888888")
        self.status_label.setText(f"● {status}")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                font-size: 10px;
                color: {status_color};
                font-style: italic;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }}
        """)
    
    def _refresh(self):
        """Авто-обновление (если нужно)"""
        pass  # Данные приходят через update_data()
    
    def show_overlay(self):
        """Показывает оверлей"""
        self.show()
    
    def hide_overlay(self):
        """Скрывает оверлей"""
        self.hide()
    
    def reset(self):
        """Сброс к состоянию по умолчанию"""
        self.title_label.setText("Table: Unknown | Waiting")
        self.hero_label.setText("Cards: --")
        self.table_label.setText("Pos: - | Pot: 0 | Villains: 0")
        self.advice_label.setText("WAITING FOR HAND...")
        self.advice_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 800;
                padding: 10px;
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.05);
                color: #AAAAAA;
                text-align: center;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
        """)
        self.status_label.setText("● Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #4CAF50;
                font-style: italic;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
        """)
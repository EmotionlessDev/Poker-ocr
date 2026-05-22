import sys
import win32gui
import win32con
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QDialog, QLineEdit, QSpinBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class WindowSelectorDialog(QDialog):
    """Диалог выбора окна для захвата"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выберите окно покера")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.selected_hwnd = None
        
        layout = QVBoxLayout(self)
        
        # Инструкция
        info_label = QLabel("Выберите окно покерного стола из списка:")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Список окон
        self.window_list = QListWidget()
        self.window_list.setAlternatingRowColors(True)
        layout.addWidget(self.window_list)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Обновить список")
        refresh_btn.clicked.connect(self.refresh_windows)
        button_layout.addWidget(refresh_btn)
        
        select_btn = QPushButton("✅ Выбрать")
        select_btn.setDefault(True)
        select_btn.clicked.connect(self.select_window)
        button_layout.addWidget(select_btn)
        
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Заполняем список при открытии
        self.refresh_windows()
        
        # Двойной клик для выбора
        self.window_list.itemDoubleClicked.connect(self.select_window)
    
    def refresh_windows(self):
        """Обновить список доступных окон"""
        self.window_list.clear()
        windows = self.enumerate_visible_windows()
        
        for hwnd, title in windows:
            item = QListWidgetItem(f"{title}")
            item.setData(Qt.ItemDataRole.UserRole, hwnd)
            self.window_list.addItem(item)
        
        if self.window_list.count() > 0:
            self.window_list.setCurrentRow(0)
    
    def enumerate_visible_windows(self):
        """Получить список видимых окон"""
        windows = []
        
        def enum_callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            
            # Получаем только окна верхнего уровня
            if win32gui.GetParent(hwnd) != 0:
                return
            
            title = win32gui.GetWindowText(hwnd)
            if title and title.strip():
                windows.append((hwnd, title))
        
        win32gui.EnumWindows(enum_callback, None)
        return windows
    
    def select_window(self):
        """Выбрать текущее окно"""
        current_item = self.window_list.currentItem()
        if current_item:
            self.selected_hwnd = current_item.data(Qt.ItemDataRole.UserRole)
            self.accept()
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите окно из списка!")


class SettingsDialog(QDialog):
    """Диалог настроек приложения"""
    
    def __init__(self, parent=None, room="replaypoker", seats=6, hero="Elots"):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(300)
        
        self.room = room
        self.seats = seats
        self.hero = hero
        
        layout = QFormLayout(self)
        
        # Комната
        self.room_edit = QLineEdit(room)
        layout.addRow("Комната:", self.room_edit)
        
        # Количество мест
        self.seats_spin = QSpinBox()
        self.seats_spin.setRange(2, 10)
        self.seats_spin.setValue(seats)
        layout.addRow("Мест за столом:", self.seats_spin)
        
        # Ник героя
        self.hero_edit = QLineEdit(hero)
        layout.addRow("Ваш никнейм:", self.hero_edit)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow(button_layout)
    
    def save_settings(self):
        """Сохранить настройки"""
        self.room = self.room_edit.text().strip() or "replaypoker"
        self.seats = self.seats_spin.value()
        self.hero = self.hero_edit.text().strip() or "Elots"
        self.accept()


class PokerAppGUI(QWidget):
    """Главное окно GUI приложения"""
    
    def __init__(self):
        super().__init__()
        self.hwnd = None
        self.is_running = False
        self.state_manager = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_cycle)
        
        # Настройки по умолчанию
        self.room = "replaypoker"
        self.seats = 6
        self.hero = "Elots"
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Poker Assistant")
        self.setMinimumWidth(400)
        self.setFixedSize(400, 300)
        
        # Устанавливаем шрифт
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title = QLabel("♠️ Poker Assistant ♥️")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Статус
        self.status_label = QLabel("Статус: Окно не выбрано")
        self.status_label.setStyleSheet("color: #7f8c8d; padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Информация о выбранном окне
        self.window_info = QLabel("")
        self.window_info.setStyleSheet("color: #34495e; font-style: italic;")
        self.window_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.window_info.setWordWrap(True)
        layout.addWidget(self.window_info)
        
        # Разделитель
        line = QLabel()
        line.setStyleSheet("background-color: #bdc3c7; min-height: 1px; max-height: 1px;")
        layout.addWidget(line)
        
        # Кнопки управления
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        # Кнопка выбора окна
        self.select_btn = QPushButton("🎯 Добавить стол (Выбрать окно)")
        self.select_btn.setMinimumHeight(45)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.select_btn.clicked.connect(self.select_window)
        button_layout.addWidget(self.select_btn)
        
        # Кнопка запуска/остановки
        self.start_btn = QPushButton("▶️ Запустить")
        self.start_btn.setMinimumHeight(45)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.start_btn.clicked.connect(self.toggle_running)
        self.start_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)
        
        layout.addLayout(button_layout)
        
        # Нижняя панель с настройками
        settings_layout = QHBoxLayout()
        
        self.settings_btn = QPushButton("⚙️ Настройки")
        self.settings_btn.clicked.connect(self.open_settings)
        settings_layout.addWidget(self.settings_btn)
        
        settings_layout.addStretch()
        
        layout.addLayout(settings_layout)
    
    def select_window(self):
        """Открыть диалог выбора окна"""
        dialog = WindowSelectorDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.hwnd = dialog.selected_hwnd
            title = win32gui.GetWindowText(self.hwnd)
            
            self.status_label.setText("Статус: ✅ Окно выбрано")
            self.status_label.setStyleSheet("color: #27ae60; padding: 10px; background-color: #d5f5e3; border-radius: 5px;")
            
            self.window_info.setText(f"Окно: {title}")
            self.start_btn.setEnabled(True)
            
            print(f"✅ Выбрано окно: {title} (HWND: {self.hwnd})")
    
    def toggle_running(self):
        """Запуск/остановка приложения"""
        if self.is_running:
            self.stop_application()
        else:
            self.start_application()
    
    def start_application(self):
        """Запустить основное приложение"""
        try:
            from poker_app.state_manager import PokerStateManager
            from poker_app.capture import capture_window
            
            self.state_manager = PokerStateManager(
                room_name=self.room,
                seats=self.seats,
                hero_nickname=self.hero,
                hwnd=self.hwnd,
                enable_overlay=True
            )
            
            self.is_running = True
            self.start_btn.setText("⏹️ Остановить")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
                QPushButton:pressed {
                    background-color: #a93226;
                }
            """)
            self.select_btn.setEnabled(False)
            self.settings_btn.setEnabled(False)
            
            self.status_label.setText("Статус: 🟢 Работает")
            self.status_label.setStyleSheet("color: #27ae60; padding: 10px; background-color: #d5f5e3; border-radius: 5px;")
            
            # Запускаем цикл обновления
            self.timer.start(100)  # 10 FPS
            
            print("🟢 Приложение запущено")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить приложение:\n{str(e)}")
            self.is_running = False
    
    def stop_application(self):
        """Остановить приложение"""
        self.timer.stop()
        self.is_running = False
        
        if self.state_manager and self.state_manager.enable_overlay:
            self.state_manager.overlay_window.hide_overlay()
        
        self.start_btn.setText("▶️ Запустить")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.select_btn.setEnabled(True)
        self.settings_btn.setEnabled(True)
        
        self.status_label.setText("Статус: ⏸️ Остановлено")
        self.status_label.setStyleSheet("color: #d35400; padding: 10px; background-color: #fdebd0; border-radius: 5px;")
        
        print("⏹️ Приложение остановлено")
    
    def update_cycle(self):
        """Цикл обновления (вызывается таймером)"""
        try:
            from poker_app.capture import capture_window
            
            frame = capture_window(self.hwnd)
            self.state_manager.update_from_frame(frame)
        except Exception as e:
            print(f"Ошибка в цикле обновления: {e}")
            self.stop_application()
            QMessageBox.warning(self, "Ошибка", f"Ошибка захвата окна:\n{str(e)}")
    
    def open_settings(self):
        """Открыть диалог настроек"""
        dialog = SettingsDialog(self, self.room, self.seats, self.hero)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.room = dialog.room
            self.seats = dialog.seats
            self.hero = dialog.hero
            print(f"Настройки обновлены: комната={self.room}, мест={self.seats}, герой={self.hero}")


def main():
    app = QApplication(sys.argv)
    
    # Устанавливаем стиль приложения
    app.setStyle("Fusion")
    
    window = PokerAppGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

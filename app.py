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
    """Window selection dialog for capture"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Poker Window")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.selected_hwnd = None
        
        layout = QVBoxLayout(self)
        
        # Instruction
        info_label = QLabel("Select a poker table window from the list:")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Window list
        self.window_list = QListWidget()
        self.window_list.setAlternatingRowColors(True)
        layout.addWidget(self.window_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh List")
        refresh_btn.clicked.connect(self.refresh_windows)
        button_layout.addWidget(refresh_btn)
        
        select_btn = QPushButton("✅ Select")
        select_btn.setDefault(True)
        select_btn.clicked.connect(self.select_window)
        button_layout.addWidget(select_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Populate list on open
        self.refresh_windows()
        
        # Double-click to select
        self.window_list.itemDoubleClicked.connect(self.select_window)
    
    def refresh_windows(self):
        """Refresh list of available windows"""
        self.window_list.clear()
        windows = self.enumerate_visible_windows()
        
        for hwnd, title in windows:
            item = QListWidgetItem(f"{title}")
            item.setData(Qt.ItemDataRole.UserRole, hwnd)
            self.window_list.addItem(item)
        
        if self.window_list.count() > 0:
            self.window_list.setCurrentRow(0)
    
    def enumerate_visible_windows(self):
        """Get list of visible windows"""
        windows = []
        
        def enum_callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            
            # Get only top-level windows
            if win32gui.GetParent(hwnd) != 0:
                return
            
            title = win32gui.GetWindowText(hwnd)
            if title and title.strip():
                windows.append((hwnd, title))
        
        win32gui.EnumWindows(enum_callback, None)
        return windows
    
    def select_window(self):
        """Select current window"""
        current_item = self.window_list.currentItem()
        if current_item:
            self.selected_hwnd = current_item.data(Qt.ItemDataRole.UserRole)
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "Select a window from the list!")


class SettingsDialog(QDialog):
    """Application settings dialog"""
    
    def __init__(self, parent=None, room="replaypoker", seats=6, hero="Elots"):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(300)
        
        self.room = room
        self.seats = seats
        self.hero = hero
        
        layout = QFormLayout(self)
        
        # Room
        self.room_edit = QLineEdit(room)
        layout.addRow("Room:", self.room_edit)
        
        # Number of seats
        self.seats_spin = QSpinBox()
        self.seats_spin.setRange(2, 10)
        self.seats_spin.setValue(seats)
        layout.addRow("Seats at table:", self.seats_spin)
        
        # Hero nickname
        self.hero_edit = QLineEdit(hero)
        layout.addRow("Your nickname:", self.hero_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow(button_layout)
    
    def save_settings(self):
        """Save settings"""
        self.room = self.room_edit.text().strip() or "replaypoker"
        self.seats = self.seats_spin.value()
        self.hero = self.hero_edit.text().strip() or "Elots"
        self.accept()


class PokerAppGUI(QWidget):
    """Main GUI application window"""
    
    def __init__(self):
        super().__init__()
        self.hwnd = None
        self.is_running = False
        self.state_manager = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_cycle)
        
        # Default settings
        self.room = "replaypoker"
        self.seats = 6
        self.hero = "Elots"
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize interface"""
        self.setWindowTitle("Poker Assistant")
        self.setMinimumWidth(400)
        self.setFixedSize(400, 300)
        
        # Set font
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("♠️ Poker Assistant ♥️")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Status
        self.status_label = QLabel("Status: No window selected")
        self.status_label.setStyleSheet("color: #7f8c8d; padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Selected window info
        self.window_info = QLabel("")
        self.window_info.setStyleSheet("color: #34495e; font-style: italic;")
        self.window_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.window_info.setWordWrap(True)
        layout.addWidget(self.window_info)
        
        # Separator
        line = QLabel()
        line.setStyleSheet("background-color: #bdc3c7; min-height: 1px; max-height: 1px;")
        layout.addWidget(line)
        
        # Control buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        # Select window button
        self.select_btn = QPushButton("🎯 Add Table (Select Window)")
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
        
        # Start/Stop button
        self.start_btn = QPushButton("▶️ Start")
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
        
        # Bottom settings panel
        settings_layout = QHBoxLayout()
        
        self.settings_btn = QPushButton("⚙️ Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        settings_layout.addWidget(self.settings_btn)
        
        settings_layout.addStretch()
        
        layout.addLayout(settings_layout)
    
    def select_window(self):
        """Open window selection dialog"""
        dialog = WindowSelectorDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.hwnd = dialog.selected_hwnd
            title = win32gui.GetWindowText(self.hwnd)
            
            self.status_label.setText("Status: ✅ Window selected")
            self.status_label.setStyleSheet("color: #27ae60; padding: 10px; background-color: #d5f5e3; border-radius: 5px;")
            
            self.window_info.setText(f"Window: {title}")
            self.start_btn.setEnabled(True)
            
            print(f"✅ Window selected: {title} (HWND: {self.hwnd})")
    
    def toggle_running(self):
        """Start/stop application"""
        if self.is_running:
            self.stop_application()
        else:
            self.start_application()
    
    def start_application(self):
        """Start main application"""
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
            self.start_btn.setText("⏹️ Stop")
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
            
            self.status_label.setText("Status: 🟢 Running")
            self.status_label.setStyleSheet("color: #27ae60; padding: 10px; background-color: #d5f5e3; border-radius: 5px;")
            
            # Start update cycle
            self.timer.start(100)  # 10 FPS
            
            print("🟢 Application started")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start application:\n{str(e)}")
            self.is_running = False
    
    def stop_application(self):
        """Stop application"""
        self.timer.stop()
        self.is_running = False
        
        if self.state_manager and self.state_manager.enable_overlay:
            self.state_manager.overlay_window.hide_overlay()
        
        self.start_btn.setText("▶️ Start")
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
        
        self.status_label.setText("Status: ⏸️ Stopped")
        self.status_label.setStyleSheet("color: #d35400; padding: 10px; background-color: #fdebd0; border-radius: 5px;")
        
        print("⏹️ Application stopped")
    
    def update_cycle(self):
        """Update cycle (called by timer)"""
        try:
            from poker_app.capture import capture_window
            
            frame = capture_window(self.hwnd)
            self.state_manager.update_from_frame(frame)
        except Exception as e:
            print(f"Error in update cycle: {e}")
            self.stop_application()
            QMessageBox.warning(self, "Error", f"Window capture error:\n{str(e)}")
    
    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self, self.room, self.seats, self.hero)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.room = dialog.room
            self.seats = dialog.seats
            self.hero = dialog.hero
            print(f"Settings updated: room={self.room}, seats={self.seats}, hero={self.hero}")


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    window = PokerAppGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

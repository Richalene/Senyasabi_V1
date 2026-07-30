"""Sign Sprint minigame."""

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt


class SignSprintWindow(QMainWindow):


    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign Sprint")
        self.resize(1920, 1080)
        
        # TODO: Initialize game UI here
        # self.setup_ui()
    
    def setup_ui(self):
        """Set up the game UI."""
        pass
    
    def start_game(self):
        """Start the game."""
        pass
    
    def end_game(self):
        """End the game."""
        pass
    
    def closeEvent(self, event):
        """Handle window close event."""
        super().closeEvent(event)

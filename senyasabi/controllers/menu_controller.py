"""Menu controller for managing game selection and navigation."""

from PySide6.QtWidgets import QWidget


class MenuController(QWidget):
    """Controller for menu navigation between games."""

    def __init__(self):
        super().__init__()

    def open_game(self, game_name):
        """Open a specific game.
        
        Args:
            game_name: Name of the game to open (e.g., 'sign_sprint')
        """
        pass

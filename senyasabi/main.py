import sys

from PySide6.QtWidgets import QApplication

from screens.app_controller import AppController
from backend import initialize_database


def main() -> int:
    # Initialize SQLite database on startup
    initialize_database()

    app = QApplication(sys.argv)
    controller = AppController()
    controller.show_welcome()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

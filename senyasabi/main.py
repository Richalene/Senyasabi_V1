import sys

from PySide6.QtWidgets import QApplication

from screens.app_controller import AppController


def main() -> int:
    app = QApplication(sys.argv)
    controller = AppController()
    controller.show_login()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

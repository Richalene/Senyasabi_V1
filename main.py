#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SenyaSabi - Sign Language Learning Game Suite
Main entry point for the application.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from senyasabi.controllers.mainwindow import MainWindow


def main():
    """Initialize and run the SenyaSabi application."""
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

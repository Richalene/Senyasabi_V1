# -*- coding: utf-8 -*-
"""Core startup utilities for SenyaSabi application."""

from pathlib import Path

from senyasabi.ui.ui_mainwindow import Ui_SenyaSabi


def get_resource_path(relative_path):
    """Return an absolute path from the project root."""
    base_path = Path(__file__).resolve().parents[2]
    return str(base_path / relative_path)


# Backward compatibility for the old generated UI import pattern.
Ui_MainWindow = Ui_SenyaSabi


def init_application():
    """Initialize application resources and configuration."""
    return None


from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QLineEdit, QToolButton


class _TogglePositioner(QObject):
    def __init__(self, field: QLineEdit, toggle: QToolButton):
        super().__init__(field)
        self.field = field
        self.toggle = toggle

    def eventFilter(self, watched, event):
        if watched is self.field and event.type() == QEvent.Type.Resize:
            self.toggle.setGeometry(
                self.field.width() - 52, (self.field.height() - 30) // 2, 46, 30
            )
        return super().eventFilter(watched, event)


def add_password_visibility_toggle(field: QLineEdit) -> QToolButton:
    toggle = QToolButton(field)
    toggle.setObjectName(f"{field.objectName()}VisibilityToggle")
    toggle.setCheckable(True)
    toggle.setCursor(Qt.CursorShape.PointingHandCursor)
    toggle.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    toggle.setStyleSheet(
        "QToolButton { color: #704833; background: transparent; border: none; "
        "font-size: 12px; font-weight: 600; padding: 2px 4px; }"
        "QToolButton:hover { color: #526536; }"
    )
    field.setTextMargins(0, 0, 54, 0)

    def update_visibility(visible: bool):
        field.setEchoMode(QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password)
        toggle.setText("Hide" if visible else "Show")
        toggle.setAccessibleName("Hide password" if visible else "Show password")

    toggle.toggled.connect(update_visibility)
    toggle.setText("Show")
    toggle.setAccessibleName("Show password")
    toggle.setGeometry(field.width() - 52, (field.height() - 30) // 2, 46, 30)
    field.visibility_toggle = toggle
    field.visibility_toggle_positioner = _TogglePositioner(field, toggle)
    field.installEventFilter(field.visibility_toggle_positioner)
    return toggle
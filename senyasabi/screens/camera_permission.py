import sys

from PySide6.QtCore import QCoreApplication, Qt, QCameraPermission
_pending = []

def ensure_camera_permission(callback):
    """Request camera permission on macOS, then call callback(granted: bool)."""

    if sys.platform != "darwin":
        callback(True)
        return

    app = QCoreApplication.instance()
    if app is None:
        callback(False)
        return

    permission = QCameraPermission()
    status = app.checkPermission(permission)

    if status == Qt.PermissionStatus.Granted:
        callback(True)

    elif status == Qt.PermissionStatus.Denied:
        callback(False)

    else:
        def done(p):
            if handler in _pending:
                _pending.remove(handler)
            callback(p.status() == Qt.PermissionStatus.Granted)
        handler = done
        _pending.append(handler)
        app.requestPermission(permission, app, handler)
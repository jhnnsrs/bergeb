try:
    from PyQt5 import QtWidgets
    has_qt = True
    qt_error = False
        
except ImportError as e:
    has_qt = e
    QtWidgets = None


try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    has_webview = True
        
except ImportError as e:
    has_webview = False


class GraphicalBackend:


    def __init__(self, parent=None) -> None:
        self.parent = parent
        self.spawned_app = None


    def __enter__(self):
        global has_qt
        assert has_qt == True, f"You cannot run with a Qt Backend if no QT Backend is installed. Please install PyQT5 {str(has_qt)}"

        if QtWidgets.QApplication.instance() is None:
            # if it does not exist then a QApplication is created
            self.spawned_app = QtWidgets.QApplication([])

        return self


    def __exit__(self, *args, **kwargs):
        if self.spawned_app: self.spawned_app.exit()


    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, *args, **kwargs):
        return self.__exit__(*args, **kwargs)
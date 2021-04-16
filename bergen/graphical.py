

try:
    from PyQt5 import QtWidgets
    has_qt = True
        
except ImportError as e:
    has_qt = False
    QtWidgets = None


class GraphicalBackend:


    def __init__(self, parent=None, run_before_when_no_app=None) -> None:
        self.parent = parent
        self.spawned_app = None
        self.run_before_when_no_app = run_before_when_no_app
        
        

    def __enter__(self):
        global has_qt
        assert has_qt, "You cannot run with a Qt Backend if no QT Backend is installed. Please install PyQT5"
        if QtWidgets.QApplication.instance() is None:
            # if it does not exist then a QApplication is created
            if self.run_before_when_no_app: self.run_before_when_no_app()
            self.spawned_app = QtWidgets.QApplication([])

        return self


    def __exit__(self, *args, **kwargs):
        if self.spawned_app: self.spawned_app.exit()


    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, *args, **kwargs):
        return self.__exit__(*args, **kwargs)
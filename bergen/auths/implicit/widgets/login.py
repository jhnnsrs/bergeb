
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView


class LoginWindow(QWebEngineView):
    """ A Login window for the OSF """

    def __init__(self, backend = None, tokenCallback=None):
        super(LoginWindow, self).__init__()
        self.state = None
        self.session = backend.session
        self.backend = backend

        auth_url, state = self.session.authorization_url(self.backend.auth_url)
        #print("Generated authorization url: {}".format(auth_url))

        self.urlChanged.connect(self.check_URL)
        self.callback = tokenCallback

        self.load(QtCore.QUrl(auth_url))
        self.set_state(state)


    def set_state(self,state):
        self.state = state

    def check_URL(self, url: QtCore.QUrl):
        url = url.url()
        #print(url)
        if url.startswith(self.backend.redirect_uri):
            token = self.session.token_from_fragment(url)
            if token: self.callback(token)
            
        #url is a QUrl object, covert it to string for easier usage
        pass


class LoginDialog(QDialog):
    def __init__(self, backend = None, parent = None):
        super(LoginDialog, self).__init__(parent)
        self.setModal(True)
        layout = QVBoxLayout(self)

        # nice widget for editing the date
        self.webview = LoginWindow(backend=backend, tokenCallback=self.tokenReady)
        layout.addWidget(self.webview)

        self.token = None
        # OK and Cancel buttons

    def tokenReady(self, token):
        self.token = token
        self.accept()

    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def getToken(backend = None, parent = None):
        dialog = LoginDialog(backend=backend, parent=parent)
        result = dialog.exec_()
        token = dialog.token
        return token, result == QDialog.Accepted
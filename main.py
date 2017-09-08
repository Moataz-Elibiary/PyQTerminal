from Terminal import QTerminal
from Background import Session
from PyQt4.QtGui import QApplication
from sys import argv


if __name__ == '__main__':
    app = QApplication(argv)
    _s = Session()
    _s.start_session('10.74.231.56', 'myousry', '1qa2ws#ED')
    win = QTerminal(session=_s)
    # win = PyQTerminal()
    win.resize(1030, 670)
    win.show()
    exit(app.exec_())

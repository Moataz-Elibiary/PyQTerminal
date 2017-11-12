from Terminal import QTerminal
from Background import Session
from PyQt5.QtWidgets import QApplication
from sys import argv
import getpass


IP_dest=''
user_dest=''
pass_dest=''
def get_destination(self):
    IP_dest=getpass._raw_input("Server: ").encode('utf-8')
    user_dest=getpass.getpass("Username: ").encode('utf-8')
    pass_dest=getpass.getpass("Password: ").encode('utf-8')

if __name__ == '__main__':
    app = QApplication(argv)
    _s = Session()
    #_s.start_session('10.74.231.56', 'myousry', '1qa2ws#ED')
    '''get_destination(IP_dest)
    get_destination(user_dest)
    get_destination(pass_dest)
    '''
    get_destination(self=IP_dest)
    _s.start_session(server=IP_dest,username=user_dest,password=pass_dest)
    win = QTerminal(session=_s)
    # win = PyQTerminal()
    win.resize(1030, 670)
    win.show()
    exit(app.exec_())

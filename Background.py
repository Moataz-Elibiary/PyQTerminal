from PyQt5.QtCore import QObject,pyqtSignal
from threading import Thread
from time import sleep
from _socket import error
from paramiko import SSHClient, AutoAddPolicy

try:
    QString = unicode
except NameError:
    # Python 3
    QString = str

class Connection(QObject):
    clear_all = pyqtSignal()
    reset_timer = pyqtSignal()
    add_text = pyqtSignal('QString')
    stop_timer = pyqtSignal()
    DATA_READ_INT = 0.1                  # Read data every 0.5 [s]

    def __init__(self):
        super(Connection, self).__init__()
        self._session = None
        self._channel = None
        self._exit_reading_flag = False
        self._reading_thread = None
        self._reading_interval = Connection.DATA_READ_INT

    def set_session(self, session):
        self._session = session

    def get_session(self):
        return self._session

    def set_channel(self, channel):
        self._channel = channel

    def get_channel(self):
        return self._channel

    def set_reading_interval(self, interval):
        self._reading_interval = interval

    def is_connected(self):
        session = self.get_session()
        channel = self.get_channel()
        if session and channel:
            if channel in session.get_channels():
                if session.is_connected():
                    try:
                        session.get_client().get_transport().send_ignore()
                        return True
                    except EOFError:
                        print("Checking connection error")
                    except:
                        print("Checking connection error")
                session.remove_channel(channel)
        return False

    def start_connection(self):
        def worker():
            if session:
                if session.is_connected():
                    self.add_text.emit((QString), "\nStarting new channel ...\n")
                    channel = session.open_channel()
                    if channel:
                        self.set_channel(channel)
                        self.clear_all.emit()
                        self.reset_timer.emit()
                        self.read_data()
                        return
            self.add_text.emit("\nError: Unable to start connection.\n")

        session = self.get_session()
        thread1 = Thread(target=worker)
        thread1.start()

    def read_data(self):
        def worker():
            while True and self.is_connected() and not self._exit_reading_flag:
                if channel.recv_ready():
                    data = channel.recv(1024).decode().replace('\r', '')
                    self.add_text.emit(data)
                    self.reset_timer.emit()
                    continue
                sleep(self._reading_interval)

        channel = self.get_channel()
        self._reading_thread = Thread(target=worker)
        self._reading_thread.start()

    def close_connection(self):
        # Exit Reading
        self._exit_reading_flag = True
        self._reading_thread.join(1)
        self._exit_reading_flag = False
        # Close the channel
        session = self.get_session()
        channel = self.get_channel()
        if session:
            if channel:
                session.close_channel(channel)
                self.set_channel(None)
        self.stop_timer.emit()
        self.add_text.emit("\nConnection closed\n")
        return True

    def close_session(self):
        session = self.get_session()
        if session:
            if self.get_channel():
                self.close_connection()
            session.close_session()
            self.set_session(None)
        self.add_text.emit("\nSession closed\n\n")
        return True

    def send(self, cmd):
        channel = self.get_channel()
        if self.is_connected():
            try:
                sent = channel.send(cmd)
                # channel.recv(len(str(key))).decode().replace('\r', '')
                return True and sent
            except error as e:
                print("sending command error")
                assert e
        return False

    def timeout(self):
        self.add_text.emit("\nTimeout")
        self.close_connection()


class Session:
    SESSIONS_COUNT = 0     # Number of opened sessions
    MAX_CHANNELS = 10      # Maximum number of opened channels per session

    def __init__(self):
        """
        This Class is used to open an SSH connection (session) with remote server.
        """
        Session.SESSIONS_COUNT += 1
        self.channelCount = 0
        self._channels = []
        self._error = ''
        self._client = None

    def get_channel_count(self):
        return len(self._channels)

    def add_channel(self, channel):
        self._channels.append(channel)

    def remove_channel(self, channel):
        if channel in self._channels:
            self._channels.remove(channel)

    def get_channels(self):
        return self._channels

    def set_client(self, client):
        self._client = client

    def get_client(self):
        return self._client

    def start_session(self, server, username='', password='', timeout=15):
        """
        This method is used to start a new connection to server.
        :param
            server: The remote server in order to initiate ssh connection with
            username: Remote server username
            password: Remote server password
            timeout: Timeout while trying to connect [s]
        """
        try:
            client = SSHClient()
            client.set_missing_host_key_policy(AutoAddPolicy())
            client.connect(server, username=username, password=password, timeout=timeout)
            self.set_client(client)
            return True
        except error as e:
            print("opening session error")
            self._error = e
            return False

    def close_session(self):
        """
        This method is used to close the connection to remote server.
        """
        try:
            if self.get_client():
                self.get_client().close()
                Session.SESSIONS_COUNT -= 1
                return True
            else:
                return False
        except error as e:
            print("closing session error")
            self._error = e
            return False

    def is_connected(self):
        if self.get_client():
            if self.get_client().get_transport():
                if self.get_client().get_transport().is_active():
                    return True
        return False

    def open_channel(self, timeout=120):
        """
        This method is used to open a new channel.
        :return shell terminal status, and the shell channel
        """
        if self.get_channel_count() < self.MAX_CHANNELS and self.is_connected():
            try:
                channel = self.get_client().invoke_shell()
                channel.settimeout(timeout)
                self.add_channel(channel)
                return channel
            except error as e:
                print("opening channel error")
                self._error = e
        # return None

    def close_channel(self, channel):
        """
        This method is used to close a channel with the remote server.
        :param channel: The channel that will be closed
        """
        if channel in self.get_channels():
            channel.close()
            self.remove_channel(channel)
            return True
        return False

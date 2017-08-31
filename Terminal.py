from PyQt4.QtGui import QTextCursor, QTextEdit, QFont, QTextCharFormat, QFontMetrics
from PyQt4.QtCore import QTimer, Qt, QCoreApplication, SIGNAL
from Background import Connection
from ControlSequence import *
from re import match, sub, findall, finditer


class QTerminal(QTextEdit):
    TIMEOUT = 60       # Timeout after 60 [s]
    MAX_OUTPUT = 1000  # Maximum output is 1000 lines
    MAX_HISTORY = 100  # Maximum history is 100 lines

    def __init__(self, master=None, session=None):
        super(QTerminal, self).__init__(master)
        self.master = master

        # Define the connection
        self._session = session
        self._connection = Connection()
        if self._session:
            self._connection.set_session(self._session)
            self._connection.start_connection()

        # Define timer
        self._timeout = self.TIMEOUT * 1000  # _timeout in [ms]
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)

        # Update the GUI
        self.font = QFont("Lucida Console", 10)
        self.setFont(self.font)
        self.document().setMaximumBlockCount(self.MAX_OUTPUT)
        self.setCurrentCharFormat(self.default_text_format())    # Reset the text format
        self.set_title('Terminal')
        self._selection_cursor = self.textCursor()
        self._select_cursor_format = self.currentCharFormat()
        self._deselect_cursor_format = self.currentCharFormat()
        self._select_cursor_format.setBackground(Qt.blue)
        self._deselect_cursor_format.setBackground(Qt.white)
        # noinspection PyArgumentList
        self._app = QCoreApplication.instance()
        self._clipboard = self._app.clipboard()

        # Update cursor and cursor position
        self.setCursorWidth(QFontMetrics(self.font).width('M'))
        self.setCursor(Qt.IBeamCursor)

        # Update signals connections
        self._connect_signals()

    def __del__(self):
        self._connection.close_session()

    def _connect_signals(self):
        # Connect pyqt signals
        QTerminal.connect(self, SIGNAL("selectionChanged()"), self.on_selection_changed)
        Connection.connect(self._connection, SIGNAL("add_text(QString)"), self.add_received_text)
        Connection.connect(self._connection, SIGNAL("clear_all()"), self.clear)
        Connection.connect(self._connection, SIGNAL("reset_timer()"), lambda: self.timer.start(self._timeout))
        Connection.connect(self._connection, SIGNAL("stop_timer()"), self.timer.stop)
        QTimer.connect(self.timer, SIGNAL("timeout()"), self._connection.timeout)

    def closeEvent(self, *args, **kwargs):
        self._connection.close_session()
        return QTextEdit.closeEvent(self, *args, **kwargs)

    def resizeEvent(self, event):
        frame_format = self.document().rootFrame().frameFormat()
        frame_format.setBottomMargin(self.viewport().height() - QFontMetrics(self.document().defaultFont()).height() - 2)
        self.document().rootFrame().setFrameFormat(frame_format)
        return QTextEdit.resizeEvent(self, event)

    def focusInEvent(self, event):
        if self._connection:
            self._connection.set_reading_interval(Connection.DATA_READ_INT)    # Reset the data reading interval
        return QTextEdit.focusInEvent(self, event)

    def focusOutEvent(self, event):
        if self._connection:
            # increase the data reading interval, as to reduce the application load
            self._connection.set_reading_interval(Connection.DATA_READ_INT * 20)
        return QTextEdit.focusOutEvent(self, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.paste()
            return

        elif event.button() == Qt.LeftButton:
            self._clear_cursor_selection()
            self._selection_cursor.setPosition(self.cursorForPosition(event.pos()).position(), QTextCursor.MoveAnchor)
            return

        elif event.button() == Qt.RightButton:
            return

        return QTextEdit.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        return

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._clear_cursor_selection()
            self._selection_cursor.movePosition(self.cursorForPosition(event.pos()).StartOfWord, QTextCursor.MoveAnchor)
            self._selection_cursor.movePosition(QTextCursor.EndOfWord, QTextCursor.KeepAnchor)
            self._selection_cursor.setCharFormat(self._select_cursor_format)
            if self._selection_cursor.hasSelection:
                self._clipboard.setText(self._selection_cursor.selectedText())
        return

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self._selection_cursor.setCharFormat(self._deselect_cursor_format)
            self._selection_cursor.setPosition(self.cursorForPosition(event.pos()).position(), QTextCursor.KeepAnchor)
            self._selection_cursor.setCharFormat(self._select_cursor_format)
            if self._selection_cursor.hasSelection:
                self._clipboard.setText(self._selection_cursor.selectedText())
        return QTextEdit.mouseMoveEvent(self, event)

    def _clear_cursor_selection(self):
        if self._selection_cursor.hasSelection():
            self._selection_cursor.setCharFormat(self._deselect_cursor_format)
            self._selection_cursor.clearSelection()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.send_text(CSI + 'A')
            return

        if event.key() == Qt.Key_Down:
            self.send_text(CSI + 'B')
            return

        if event.key() == Qt.Key_Right:
            self.send_text(CSI + 'C')
            return

        elif event.key() == Qt.Key_Left:
            self.send_text(CSI + 'D')
            return

        elif event.key() == Qt.Key_Return:
            # Move cursor to end of line before sending
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.MoveAnchor)
            cursor.setCharFormat(self.currentCharFormat())
            self.setTextCursor(cursor)
            self.send_text(event.text())
            return

        if event.modifiers() == Qt.NoModifier:
            self.send_text(event.text())
            return

        elif event.modifiers() == Qt.ShiftModifier:
            if event.text():
                self.send_text(event.text())
                return

        # if event.key() == Qt.Key_Home:
        #         if event.modifiers() == Qt.ShiftModifier:
        #             self.set_cursor_pos(self._readonly_end_pos, QTextCursor.KeepAnchor)
        #             return
        #         elif event.modifiers() == Qt.NoModifier:
        #             self.set_cursor_pos(self._readonly_end_pos, QTextCursor.MoveAnchor)
        #             return
        #
        #     elif event.key() == Qt.Key_Escape:
        #         # self._connection.send(ControlSequence.ESC)
        #         return

        return QTextEdit.keyPressEvent(self, event)

    def send_text(self, cmd=''):
        if self._connection.is_connected():
            self._connection.send(str(cmd))
        elif cmd == '\r':
            self.clear()
            self._connection.start_connection()

    def on_selection_changed(self):
        if self.textCursor().selectedText():
            self.copy()

    def print_data(self, data):
        for char_i in data:
            # Decode ASCII character
            if char_i == BEL:    # Beep
                self._app.beep()

            elif char_i == BS:   # Backspace
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor)
                cursor.setCharFormat(self.currentCharFormat())
                self.setTextCursor(cursor)

            elif str(char_i):    # Normal characters
                # Replace the existing character
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
                cursor.setCharFormat(self.currentCharFormat())
                cursor.insertText(str(char_i))
                self.setTextCursor(cursor)

    def add_received_text(self, data):
        if ESC in data:
            # Slice the data with Escape
            new_data_list = [ESC + d for d in data.split(ESC)]
            new_data_list[0] = new_data_list[0][1:]
            for data_slice in new_data_list:
                self.print_data(self.decode_data(data_slice))
        else:
            self.print_data(self.decode_data(data))

        # Close connection on exit
        if match('.*\n?logout\n+', data):
            self.close()

    def insertFromMimeData(self, mime_data):
        self.send_text(self._clipboard.text())
        return

    def set_title(self, title):
        self.setWindowTitle(title.strip() if title.strip() else 'Terminal')

    def decode_data(self, data):
        def moving_cursor(d, pattern):
            """
            This function is used to moves the cursor by COUNT rows/column depending on the received data.
            The default count is 1.
            """
            if pattern:
                if pattern.group()[-1] == 'A':    # Move Cursor Up
                    action = QTextCursor.Up
                elif pattern.group()[-1] == 'B':  # Move Cursor Down
                    action = QTextCursor.Down
                elif pattern.group()[-1] == 'C':  # Move Cursor Right
                    action = QTextCursor.Right
                elif pattern.group()[-1] == 'D':  # Move Cursor Left
                    action = QTextCursor.Left
                elif pattern.group()[-1] == 'E':  # Move Cursor Next Block
                    action = QTextCursor.NextBlock
                elif pattern.group()[-1] == 'F':  # Move Cursor Previous Block
                    action = QTextCursor.PreviousBlock
                else:
                    action = None

                if action:
                    count = pattern.group()[2:-1]
                    if count:
                        try:
                            cursor.movePosition(action, QTextCursor.MoveAnchor, int(count))
                        except ValueError:
                            print("Receiving non-integer value for escape sequence.")
                    else:  # same as value = 1
                        cursor.movePosition(action, QTextCursor.MoveAnchor)
                    return sub("%s\d*[ABCDEF]" % rCSI, '', d)
            return d

        def scroll_cursor(d, pattern):
            """
            This function is used to scroll the text depending on the received data.
            Sets the cursor position where subsequent text will begin.
            If no row/column parameters are provided ( i.e. <ESC>[H ), the cursor will
            move to the home position, at the upper left of the screen.
            """
            if pattern:
                count = pattern.group()[2:-1]
                if count:
                    try:
                        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum() - int(count))
                    except ValueError:
                        print("Receiving non-integer value for escape sequence.")
                else:
                    self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
                return sub("%s\d*H" % rCSI, '', d)
            return d

        cursor = self.textCursor()
        text_format = self.currentCharFormat()

        # Decode escape characters
        if ESC in data:
            if data.startswith(CSI):        # CSI Codes ( ESC + [ )
                """ Moving Cursor Patterns """
                data = moving_cursor(data, match("%s\d*[ABCDEF]" % rCSI, data))   # pattern = <ESC>[{value} A|B|C|D|E|F

                # TODO: To be implemented later
                # # Move Cursor Character Absolute  [column] (default = [row,1])
                # matched_pattern = match("%s\d*G" % rCSI, data)  # pattern = <ESC>[{value}G
                # if matched_pattern:
                #     data = sub("%s\d*G" % rCSI, '', data)
                #     moving_cursor(matched_pattern, QTextCursor.PreviousBlock)

                # Move Cursor Position [row;column] (default = [1,1])
                data = scroll_cursor(data, match("%s\d*H" % rCSI, data))   # pattern = <ESC>[{value};{value}H

                # # Move Cursor Forward Tabulation (default = 1)
                # matched_pattern = match("%s\d*I" % rCSI, data)  # pattern = <ESC>[{value}I
                # if matched_pattern:
                #     data = sub("%s\d*I" % rCSI, '', data)
                #     moving_cursor(matched_pattern, QTextCursor.WordLeft)

                """ Erase Patterns """
                # Text Erase in Display
                matched_pattern = match("%s\d*J" % rCSI, data)   # pattern = <ESC>[{value}J
                if matched_pattern:
                    data = sub("%s\d*J" % rCSI, '', data)
                    matched_code = matched_pattern.group()[2:-1]
                    if matched_code:
                        if matched_code == 0:
                            # EL0 = CSI + '0J'  ==> Erase Below (from cursor down)
                            cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
                        elif matched_code == 1:
                            # EL1 = CSI + '1J'  ==> Erase Above (from cursor up)
                            cursor.movePosition(QTextCursor.Start, QTextCursor.KeepAnchor)
                        elif matched_code == 2:
                            # EL2 = CSI + '2J'  ==> Erase All
                            cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
                            cursor.movePosition(QTextCursor.Start, QTextCursor.KeepAnchor)
                        else:
                            # unsupported number
                            print("Unsupported escape sequence.")
                    else:
                        # EL = CSI + 'J'  ==> Erase Below (from cursor down)
                        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
                    if cursor.hasSelection():
                        cursor.removeSelectedText()

                # Text Erase in Line (EL)
                matched_pattern = match("%s\d?K" % rCSI, data)     # pattern = <ESC>[{value}K
                if matched_pattern:
                    data = sub("%s\d?K" % rCSI, '', data)
                    matched_code = matched_pattern.group()[2:-1]
                    if matched_code:
                        if matched_code == 0:
                            # EL0 = CSI + '0K'  ==> Clear from cursor to end of line (from cursor right)
                            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                        elif matched_code == 1:
                            # EL1 = CSI + '1K'  ==> Clear from cursor to start of line (from cursor left)
                            cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
                        elif matched_code == 2:
                            # EL2 = CSI + '2K'  ==> Clear entire line
                            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.MoveAnchor)
                            cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
                        else:
                            # Cursor already in position, or unsupported number
                            pass
                    else:
                        # EL = CSI + 'K'  ==> Clear from cursor to end of line (from cursor right)
                        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                    if cursor.hasSelection():
                        cursor.removeSelectedText()

                # Text Graphical Format
                matched_pattern = match("%s(\d+;?)+m" % rCSI, data)      # pattern = <ESC>[{value};{value}m
                if matched_pattern:
                    data = data[len(matched_pattern.group()):]
                    matched_code = finditer('\d+', matched_pattern.group())
                    if matched_code:
                        for code in matched_code:
                            text_format = self.update_text_format(int(code.group()), text_format)

            elif data.startswith(OSC):      # OSC Codes ( ESC + ] )
                # Update Terminal Title
                matched_pattern = match("%s\d+;.*(%s|%s)" % (rOSC, BEL, rST), data)   # pattern = <ESC>]{value};{string} + ST|BEL
                if matched_pattern:
                    data = data[len(matched_pattern.group()):]
                    matched_code = str(findall('\d+', matched_pattern.group())[0])
                    if matched_code in '02':    # Ignore all other codes
                        self.set_title(matched_pattern.group()[4:-1])

        cursor.setCharFormat(text_format)
        self.setTextCursor(cursor)
        return sub(ESC, '', data)

    def update_text_format(self, code, text_format):
        # Set Default Text Graphical Format
        default_format = self.default_text_format()

        # Text attributes
        if code == 0:                                      # Default
            text_format = default_format
        elif code == 1:                                    # Bold
            text_format.setFontWeight(QFont.Bold)
        elif code == 2:                                    # Low Intensity
            text_format.setFontWeight(QFont.Light)
        elif code == 3:                                    # Italic
            text_format.setFontItalic(True)
        elif code == 4:                                    # Underline
            text_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
            text_format.setFontUnderline(True)
        elif code == 5:                                    # Blink, Appears as Bold
            text_format.setFontWeight(QFont.Bold)
        elif code == 6:                                    # Blink, Appears as Very Bold
            text_format.setFontWeight(QFont.Black)
        elif code == 7:                                    # Reverse/Inverse
            foreground_color = text_format.foreground()
            text_format.setForeground(text_format.background())
            text_format.setBackground(foreground_color)
        elif code == 8:                                    # Hidden/Invisible (for password)
            text_format.setForeground(text_format.background())
        elif code == 9:                                    # Crossed-out
            text_format.setFontStrikeOut(True)
        elif code == 21:                                   # Bold OFF
            text_format.setFontWeight(QFont.Normal)
        elif code == 22:                                   # Faint OFF
            text_format.setFontWeight(QFont.Normal)
        elif code == 23:                                   # Italic OFF
            text_format.setFontItalic(False)
        elif code == 24:                                   # Underline OFF
            text_format.setUnderlineStyle(QTextCharFormat.NoUnderline)
            text_format.setFontUnderline(False)
        elif code == 25:                                   # Steady (Not Blinking/Bold)
            text_format.setFontWeight(QFont.Normal)
        elif code == 27:                                   # Positive (non-inverted)
            foreground_color = text_format.foreground()
            text_format.setForeground(text_format.background())
            text_format.setBackground(foreground_color)
        elif code == 28:                                   # Visible (not hidden)
            text_format.setForeground(default_format.foreground())
            text_format.setBackground(default_format.background())
        elif code == 29:                                   # Crossed-out OFF
            text_format.setFontStrikeOut(False)

        # Foreground colors
        elif code == 30:                                   # Foreground Black
            text_format.setForeground(Qt.darkGray)
        elif code == 31:                                   # Foreground Red
            text_format.setForeground(Qt.red)
        elif code == 32:                                   # Foreground Green
            text_format.setForeground(Qt.green)
        elif code == 33:                                   # Foreground Yellow
            text_format.setForeground(Qt.yellow)
        elif code == 34:                                   # Foreground Blue
            text_format.setForeground(Qt.blue)
        elif code == 35:                                   # Foreground Magenta
            text_format.setForeground(Qt.magenta)
        elif code == 36:                                   # Foreground Cyan
            text_format.setForeground(Qt.cyan)
        elif code == 37:                                   # Foreground White
            text_format.setForeground(Qt.white)
        elif code == 39:                                   # Foreground Default
            text_format.setForeground(default_format.foreground())

        # Background colors
        elif code == 40:                                   # Background Black
            text_format.setBackground(Qt.darkGray)
        elif code == 41:                                   # Background Red
            text_format.setBackground(Qt.red)
        elif code == 42:                                   # Background Green
            text_format.setBackground(Qt.green)
        elif code == 43:                                   # Background Yellow
            text_format.setBackground(Qt.yellow)
        elif code == 44:                                   # Background Blue
            text_format.setBackground(Qt.blue)
        elif code == 45:                                   # Background Magenta
            text_format.setBackground(Qt.magenta)
        elif code == 46:                                   # Background Cyan
            text_format.setBackground(Qt.cyan)
        elif code == 47:                                   # Background White
            text_format.setBackground(Qt.white)
        elif code == 49:                                   # Background Default
            text_format.setBackground(default_format.background())
        else:
            pass

        return text_format

    def default_text_format(self):
        text_format = self.currentCharFormat()
        text_format.setFontWeight(QFont.Normal)
        text_format.setFontItalic(False)
        text_format.setUnderlineStyle(QTextCharFormat.NoUnderline)
        text_format.setFontUnderline(False)
        text_format.setFontStrikeOut(False)
        text_format.setForeground(Qt.darkGray)
        text_format.setBackground(Qt.white)
        return text_format

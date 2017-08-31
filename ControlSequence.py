"""
http://invisible-island.net/xterm/ctlseqs/ctlseqs.html
http://en.wikipedia.org/wiki/ANSI_escape_code
"""


# ASCII Codes
NUL = '\x00'  # NULL (^@)
SOH = '\x01'  # Start of header (^A)
STX = '\x02'  # Start of text (^B)
ETX = '\x03'  # End of text (^C)
EOT = '\x04'  # End of transmission (^D)
ENQ = '\x05'  # Enquiry (^E)
ACK = '\x06'  # Acknowledge (^F)
BEL = '\x07'  # Bell (^G)
BS = '\x08'   # Backspace (^H)
TAB = '\x09'  # Horizontal tab (^I)
LF = '\x0A'   # NL line feed, new line (^J)
VT = '\x0B'   # Vertical tab - Home (^K)
FF = '\x0C'   # NP form feed, new page (^L)
CR = '\x0D'   # Carriage return (^M)
SO = '\x0E'   # Shift out (^N)
SI = '\x0F'   # Shift in (^O)
DLE = '\x10'  # Data link escape (^P)
DC1 = '\x11'  # Device control 1 (^Q)
NAK = '\x15'  # Negative acknowledge (^U)
CAN = '\x18'  # Cancel (~X)
SUB = '\x1A'  # Substitute (^Z)
ESC = '\x1B'  # Escape (^[)
# FS = '\x1B\x5C'   # file separator - cursor right (^\)
# GS = '\x1B\x5D'   # group separator - cursor left (^])
# RS = '\x1B\x5E'   # Record separator - cursor up (^^)
# US = '\x1B\x5F'   # Unit separator - cursor down (^_)


# Common Escape Characters
IND = ESC + 'D'          # Index
NEL = ESC + 'E'          # Next Line
HTS = ESC + 'H'          # Tab Set
RI = ESC + 'M'           # Reverse Index
SS2 = ESC + 'N'          # Single Shift Two
SS3 = ESC + 'O'          # Single Shift Three
DCS = ESC + 'P'          # Device Control String
SPA = ESC + 'V'          # Start of Guarded Area
EPA = ESC + 'W'          # End of Guarded Area
SOS = ESC + 'X'          # Start of String
DECID = ESC + 'Z'        # Return Terminal ID
CSI = ESC + '\x5B'       # Control Sequence Introducer ( ESC + [ )
rCSI = ESC + '\x5C\x5B'  # ESC + \[
ST = ESC + '\x5C'        # String Terminator ( ESC + \ )
rST = ESC + '\x5C\x5C'   # ESC + \\
OSC = ESC + '\x5D'       # Operating System Command ( ESC + ] )
rOSC = ESC + '\x5C\x5D'  # ESC + \]
PM = ESC + '\x5E'        # Privacy Message ( ESC + ^ )
rPM = ESC + '\x5C\x5E'   # ESC + \^
APC = ESC + '\x5F'       # Application Program Command ( ESC + _ )
RIS = ESC + 'c'          # Reset to Initial State

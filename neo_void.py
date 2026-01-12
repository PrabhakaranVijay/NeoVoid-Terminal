# #!/usr/bin/env python3
# """
# NeoVoid - minimal native terminal emulator demo (PyQt6).
# Features:
#  - Launches /bin/zsh in a PTY
#  - Reads/writes to PTY
#  - Basic SGR color -> HTML mapping
#  - Resizing via ioctl(TIOCSWINSZ)
#  - Scrollable native widget
# Limitations:
#  - Minimal ANSI/VT handling (only SGR colors)
#  - Not a drop-in replacement for iTerm2/Terminal.app (but a solid base)
# """

# import os
# import pty
# import select
# import sys
# import fcntl
# import termios
# import struct
# import re

# from PyQt6.QtCore import QSocketNotifier, Qt, QTimer
# from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QWidget, QVBoxLayout
# from PyQt6.QtGui import QFont, QTextCursor

# # -------------------------
# # Helper: set PTY window size
# # -------------------------
# def set_pty_winsize(fd, rows, cols, xpix=0, ypix=0):
#     # struct winsize: unsigned short ws_row, ws_col, ws_xpixel, ws_ypixel
#     winsize = struct.pack("HHHH", rows, cols, xpix, ypix)
#     TIOCSWINSZ = getattr(termios, 'TIOCSWINSZ', 0x5414)  # fallback value
#     fcntl.ioctl(fd, TIOCSWINSZ, winsize)


# # -------------------------
# # Minimal ANSI SGR -> HTML converter
# # Handles codes like \x1b[31m, \x1b[1;32m, \x1b[0m
# # -------------------------
# SGR_RE = re.compile(r'\x1b\[([0-9;]*)m')

# ANSI_TO_CSS = {
#     30: 'color: #000000;',  # black
#     31: 'color: #cd0000;',  # red
#     32: 'color: #00cd00;',  # green
#     33: 'color: #cdcd00;',  # yellow
#     34: 'color: #0000ee;',  # blue
#     35: 'color: #cd00cd;',  # magenta
#     36: 'color: #00cdcd;',  # cyan
#     37: 'color: #e5e5e5;',  # white / light gray
#     90: 'color: #7f7f7f;',  # bright black / grey
#     91: 'color: #ff0000;',  # bright red
#     92: 'color: #00ff00;',
#     93: 'color: #ffff00;',
#     94: 'color: #5c5cff;',
#     95: 'color: #ff00ff;',
#     96: 'color: #00ffff;',
#     97: 'color: #ffffff;',
#     40: 'background-color: #000000;',
#     41: 'background-color: #cd0000;',
#     42: 'background-color: #00cd00;',
#     43: 'background-color: #cdcd00;',
#     44: 'background-color: #0000ee;',
#     45: 'background-color: #cd00cd;',
#     46: 'background-color: #00cdcd;',
#     47: 'background-color: #e5e5e5;',
# }

# def sgr_to_html(text):
#     """
#     Convert text with SGR escape sequences into simple HTML.
#     Only handles SGR sequences and plain text.
#     """
#     out = []
#     last = 0
#     open_spans = []

#     for m in SGR_RE.finditer(text):
#         pre = text[last:m.start()]
#         if pre:
#             out.append(escape_html(pre))

#         codes_raw = m.group(1)
#         if codes_raw == '':
#             codes = [0]
#         else:
#             codes = [int(x) if x.isdigit() else 0 for x in codes_raw.split(';')]

#         for code in codes:
#             if code == 0:  # reset
#                 # close all spans
#                 while open_spans:
#                     out.append('</span>')
#                     open_spans.pop()
#             elif code == 1:  # bold
#                 out.append('<span style="font-weight:bold;">')
#                 open_spans.append('bold')
#             elif 30 <= code <= 47 or 90 <= code <= 97 or 40 <= code <= 47:
#                 css = ANSI_TO_CSS.get(code)
#                 if css:
#                     out.append(f'<span style="{css}">')
#                     open_spans.append('color')
#             # else ignore other codes for now
#         last = m.end()

#     tail = text[last:]
#     if tail:
#         out.append(escape_html(tail))

#     # close anything left
#     while open_spans:
#         out.append('</span>')
#         open_spans.pop()

#     # replace newlines with <br> so HTML lines display correctly
#     result = ''.join(out).replace('\n', '<br/>')
#     return result

# def escape_html(s):
#     # minimal html escape
#     return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# # -------------------------
# # Terminal Widget (QTextEdit)
# # -------------------------
# class TerminalWidget(QTextEdit):
#     def __init__(self, pty_fd, parent=None):
#         super().__init__(parent)
#         self.pty_fd = pty_fd

#         # Appearance: minimal black & white
#         self.setStyleSheet("background: black; color: white;")
#         self.setFont(QFont("Menlo", 12))   # Menlo is a nice macOS monospace
#         self.setUndoRedoEnabled(False)
#         self.setAcceptRichText(True)
#         self.setReadOnly(False)  # allow keyboard input
#         self.setCursorWidth(10)  # thick insertion cursor
#         self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

#         # We'll append HTML fragments instead of raw text for basic color support.
#         self.setHtml('')  # start empty

#         # Use QSocketNotifier to watch the PTY fd for read events
#         self.notifier = QSocketNotifier(self.pty_fd, QSocketNotifier.Type.Read)
#         self.notifier.activated.connect(self.on_pty_ready)

#         # Buffer accumulation & timed flush to avoid UI thrash
#         self._pending_html = []
#         self._flush_timer = QTimer(self)
#         self._flush_timer.setInterval(16)  # ~60FPS batching
#         self._flush_timer.timeout.connect(self._flush_pending)
#         self._flush_timer.start()

#     def on_pty_ready(self):
#         # Read bytes from PTY and append to view
#         try:
#             data = os.read(self.pty_fd, 4096)
#         except OSError as e:
#             # PTY closed or other error
#             self.appendPlainText(f"\n[PTY read error: {e}]\n")
#             self.notifier.setEnabled(False)
#             return

#         if not data:
#             # EOF
#             self.appendPlainText("\n[EOF]\n")
#             self.notifier.setEnabled(False)
#             return

#         try:
#             text = data.decode('utf-8', errors='replace')
#         except Exception:
#             text = data.decode('latin1', errors='replace')

#         # Convert SGR to HTML and queue append
#         html_fragment = sgr_to_html(text)
#         # preserve trailing newline behaviour by using <br/> where necessary
#         self._pending_html.append(html_fragment)

#     def _flush_pending(self):
#         if not self._pending_html:
#             return
#         combined = ''.join(self._pending_html)
#         self._pending_html.clear()

#         # Append HTML at the end and scroll
#         cursor = self.textCursor()
#         cursor.movePosition(QTextCursor.MoveOperation.End)
#         # Using insertHtml keeps formatting applied
#         cursor.insertHtml(combined)
#         cursor.movePosition(QTextCursor.MoveOperation.End)
#         self.setTextCursor(cursor)
#         self.ensureCursorVisible()

#     # Key handling - forward keystrokes to PTY
#     def keyPressEvent(self, ev):
#         # If the user holds modifiers, handle some combos locally (copy/paste)
#         ctrl = ev.modifiers() & Qt.KeyboardModifier.ControlModifier
#         meta = ev.modifiers() & Qt.KeyboardModifier.MetaModifier
#         if (meta or ctrl) and ev.key() == Qt.Key.Key_C:
#             self.copy()
#             return
#         if (meta or ctrl) and ev.key() == Qt.Key.Key_V:
#             self.paste()
#             return

#         text = ev.text()
#         # for normal printable keys, send text bytes
#         if text:
#             os.write(self.pty_fd, text.encode())
#             return

#         # handle special keys
#         k = ev.key()
#         seq = None
#         if k == Qt.Key.Key_Return:
#             seq = '\r'
#         elif k == Qt.Key.Key_Backspace:
#             seq = '\x7f'  # DEL
#         elif k == Qt.Key.Key_Tab:
#             seq = '\t'
#         elif k == Qt.Key.Key_Escape:
#             seq = '\x1b'
#         elif k == Qt.Key.Key_Left:
#             seq = '\x1b[D'
#         elif k == Qt.Key.Key_Right:
#             seq = '\x1b[C'
#         elif k == Qt.Key.Key_Up:
#             seq = '\x1b[A'
#         elif k == Qt.Key.Key_Down:
#             seq = '\x1b[B'
#         elif Qt.Key.Key_F1 <= k <= Qt.Key.Key_F35:
#             # map Fx to CSI 11~ etc: basic mapping for F1-F4
#             fno = k - Qt.Key.Key_F1 + 1
#             seq = '\x1bOP' if fno == 1 else '\x1bOQ' if fno == 2 else '\x1bOR' if fno == 3 else '\x1bOS' if fno == 4 else ''
#         else:
#             seq = ''

#         if seq is not None:
#             if seq:
#                 os.write(self.pty_fd, seq.encode())
#             return

#         # fallback to default behavior (copy/paste etc.)
#         super().keyPressEvent(ev)

#     def resizeEvent(self, ev):
#         super().resizeEvent(ev)
#         # Compute rows/cols from widget size and font metrics
#         fm = self.fontMetrics()
#         # char dimensions
#         cw = fm.averageCharWidth()
#         ch = fm.height()
#         # content rect (approx)
#         rect = self.viewport().contentsRect()
#         cols = max(20, rect.width() // max(1, cw))
#         rows = max(5, rect.height() // max(1, ch))
#         try:
#             set_pty_winsize(self.pty_fd, rows, cols)
#         except Exception as e:
#             print("Could not set winsize:", e)


# # -------------------------
# # Launch PTY + spawn shell
# # -------------------------
# def spawn_shell_in_pty():
#     # Use forkpty to create a child process connected to a PTY
#     pid, fd = pty.fork()
#     if pid == 0:
#         # Child process: execute zsh
#         # Make shell a login shell? leave as default for now.
#         shell = "/bin/zsh"
#         try:
#             os.execvp(shell, [shell])
#         except Exception as e:
#             print("exec failed:", e)
#             os._exit(1)
#     else:
#         # Parent: return master fd
#         return pid, fd

# # -------------------------
# # Main Window
# # -------------------------
# class MainWindow(QMainWindow):
#     def __init__(self, pty_fd, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("NeoVoid")
#         self.setMinimumSize(700, 400)

#         # container
#         w = QWidget()
#         layout = QVBoxLayout()
#         w.setLayout(layout)
#         self.setCentralWidget(w)

#         self.terminal = TerminalWidget(pty_fd)
#         layout.addWidget(self.terminal)

#     def closeEvent(self, ev):
#         # optional: cleanup
#         super().closeEvent(ev)


# # -------------------------
# # Entrypoint
# # -------------------------
# def main():
#     pid_fd = spawn_shell_in_pty()
#     if pid_fd is None:
#         print("Failed to spawn shell")
#         sys.exit(1)
#     pid, fd = pid_fd

#     app = QApplication(sys.argv)
#     win = MainWindow(fd)
#     win.show()
#     try:
#         rv = app.exec()
#         # when GUI exits, optionally wait for child (or kill)
#     finally:
#         try:
#             os.close(fd)
#         except Exception:
#             pass
#     sys.exit(0)

# if __name__ == '__main__':
#     main()


import os
import pty
import select
import subprocess
import threading
import pyte
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import QApplication, QTextEdit, QMainWindow
import sys

BANNER = r"""
                        ______________
                       |              |
                       | Hello World. |
       _..._           | _____________|
      .'     '.      _ //
     /    .-""-\   _/ \                 
   .-|   /:.   |  |   |
   |  \  |:.   /.-'-./
   | .-'-;:__.'    =/                   /$$   /$$                     /$$    /$$          /$$       /$$
   .'=  *=|     _.='                   | $$$ | $$                    | $$   | $$         |__/      | $$
  /   _.  |    ;                       | $$$$| $$  /$$$$$$   /$$$$$$ | $$   | $$ /$$$$$$  /$$  /$$$$$$$
 ;-.-'|    \   |                       | $$ $$ $$ /$$__  $$ /$$__  $$|  $$ / $$//$$__  $$| $$ /$$__  $$
/   | \    _\  _\                      | $$  $$$$| $$$$$$$$| $$  \ $$ \  $$ $$/| $$  \ $$| $$| $$  | $$
\__/'._;.  ==' ==\                     | $$\  $$$| $$_____/| $$  | $$  \  $$$/ | $$  | $$| $$| $$  | $$
         \    \   |                    | $$ \  $$|  $$$$$$$|  $$$$$$/   \  $/  |  $$$$$$/| $$|  $$$$$$$
         /    /   /                    |__/  \__/ \_______/ \______/     \_/    \______/ |__/ \_______/
         /-._/-._/
         \   `\  \
          `-._/._/
"""

class NeoVoidTerminal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeoVoid Terminal")
        self.resize(1000, 600)

        # Text widget setup
        self.text = QTextEdit(self)
        self.text.setReadOnly(True)
        self.text.setFont(QFont("Menlo", 12))
        self.text.setStyleSheet("background-color: black; color: white;")
        self.setCentralWidget(self.text)

        # Display banner
        self.text.append(BANNER + "\n")

        # PTY setup
        self.master_fd, self.slave_fd = pty.openpty()
        self.process = subprocess.Popen(
            ["/bin/zsh"],
            preexec_fn=os.setsid,
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            universal_newlines=False,
            bufsize=0,
        )

        # pyte virtual terminal
        self.screen = pyte.Screen(120, 40)
        self.stream = pyte.Stream(self.screen)

        # Data buffer
        self.buffer_lines = []

        # Reader thread
        self.running = True
        threading.Thread(target=self.read_from_pty, daemon=True).start()

        # Timer for UI updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(60)

    def read_from_pty(self):
        while self.running:
            r, _, _ = select.select([self.master_fd], [], [], 0.05)
            if self.master_fd in r:
                try:
                    data = os.read(self.master_fd, 1024).decode(errors="ignore")
                    self.stream.feed(data)
                except OSError:
                    break

    def update_display(self):
        text = "\n".join(self.screen.display)
        # Append new lines instead of replacing everything
        lines = text.splitlines()
        self.buffer_lines = lines[-5000:]  # Keep last 5000 lines
        new_text = "\n".join(self.buffer_lines)

        # Check if user is at bottom
        scrollbar = self.text.verticalScrollBar()
        at_bottom = scrollbar.value() == scrollbar.maximum()

        # Only refresh if text changed
        if new_text != self.text.toPlainText():
            self.text.setPlainText(f"{BANNER}\n{new_text}")

        # Auto-scroll only if user was at bottom
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def keyPressEvent(self, event):
        key = event.text()
        if key:
            os.write(self.master_fd, key.encode())

    def closeEvent(self, event):
        self.running = False
        try:
            os.close(self.master_fd)
        except:
            pass
        self.process.terminate()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    term = NeoVoidTerminal()
    term.show()
    sys.exit(app.exec())


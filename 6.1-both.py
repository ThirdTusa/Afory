
# Made by Tuseloryy
# My social: https://tuseloryy.card.co
# Python 3.10
# For 2026.6.1

import sys
import pygame
import os
import json
import getpass
import subprocess
import random
import platform
import webbrowser
import yt_dlp
from pynput import keyboard
from mutagen.mp3 import MP3
from multiprocessing import Process, Queue
from PyQt5 import QtCore, QtGui, QtWidgets

def qt_message_handler(mode, context, message):
    if mode == QtCore.QtDebugMsg:
        prefix = "[DEBUG]"
    elif mode == QtCore.QtWarningMsg:
        prefix = "[WARNING]"
    elif mode == QtCore.QtCriticalMsg:
        prefix = "[CRITICAL]"
    elif mode == QtCore.QtFatalMsg:
        prefix = "[FATAL]"
    else:
        prefix = "[INFO]"

    sys.stderr.write(f"{prefix} {message}\n")

QtCore.qInstallMessageHandler(qt_message_handler)

def resource_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, filename)

def ytdlp_download_process(url, ydl_opts, result_queue, log_queue):
    """Отдельный процесс для загрузки с yt_dlp"""
    try:
        def hook(d):
            if d.get("status") == "downloading":
                downloaded = d.get("_percent_str", "0%").strip()
                log_queue.put(("progress", downloaded))

        opts = dict(ydl_opts)
        opts["progress_hooks"] = [hook]

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            final_path = os.path.splitext(file_path)[0] + ".mp3"

        result_queue.put(("success", final_path, url))

    except Exception as e:
        result_queue.put(("error", str(e)))
    finally:
        log_queue.put(("done", None))

class ConsoleRedirect(QtCore.QObject):
    text_written = QtCore.pyqtSignal(str)

    def __init__(self, original_stream):
        super().__init__()
        self.original_stream = original_stream if (original_stream and hasattr(original_stream, 'write')) else None

    def write(self, text):
        if self.original_stream:
            try:
                self.original_stream.write(text)
                self.original_stream.flush()
            except Exception:
                pass

        try:
            self.text_written.emit(text)
        except Exception:
            pass

    def flush(self):
        if self.original_stream and hasattr(self.original_stream, 'flush'):
            try:
                self.original_stream.flush()
            except Exception:
                pass

    def fileno(self):
        if self.original_stream and hasattr(self.original_stream, 'fileno'):
            try:
                return self.original_stream.fileno()
            except Exception:
                pass
        return -1

    def isatty(self):
        if self.original_stream and hasattr(self.original_stream, 'isatty'):
            try:
                return self.original_stream.isatty()
            except Exception:
                pass
        return False

    def writable(self):
        return True

    @property
    def encoding(self):
        if self.original_stream and hasattr(self.original_stream, 'encoding'):
            return self.original_stream.encoding
        return 'utf-8'

class QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

class YTDLPWorker(QtCore.QObject):
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(str, str)
    error = QtCore.pyqtSignal(str)
    log = QtCore.pyqtSignal(str)

    def __init__(self, url, ydl_opts, downloading_t):
        super().__init__()
        self.url = url
        self.ydl_opts = ydl_opts
        self.download_t = downloading_t
        self.process = None
        self.result_queue = Queue()
        self.log_queue = Queue()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_queue)

    def run(self):
        self.process = Process(
            target=ytdlp_download_process,
            args=(self.url, self.ydl_opts, self.result_queue, self.log_queue)
        )
        self.process.start()
        self.timer.start(100)

    def check_queue(self):
        """Проверяем результаты из очереди"""
        try:
            while not self.log_queue.empty():
                msg_type, data = self.log_queue.get_nowait()
                if msg_type == "progress":
                    self.log.emit(f"{self.download_t} {data}")
                elif msg_type == "done":
                    pass
                    
            if not self.result_queue.empty():
                result = self.result_queue.get_nowait()

                if result[0] == "success":
                    final_path, url = result[1], result[2]
                    self.finished.emit(final_path, url)
                elif result[0] == "error":
                    error_msg = result[1]
                    self.error.emit(error_msg)

                self.stop()

        except Exception as e:
            self.error.emit(str(e))
            self.stop()

    def stop(self):
        self.timer.stop()
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.kill()

class DownloadManager(QtCore.QObject):
    queue_changed = QtCore.pyqtSignal()
    active_changed = QtCore.pyqtSignal(str)

    def __init__(self, max_threads=2):
        super().__init__()
        self.queue = []
        self.active_threads = []
        self.max_threads = max_threads

    def add(self, url, ydl_opts, downloading_t, callbacks):
        task = {
            "url": url,
            "opts": ydl_opts,
            "downloading_t": downloading_t,
            "callbacks": callbacks
        }

        self.queue.append(task)
        self.queue_changed.emit()
        self._try_start_next()

    def _try_start_next(self):
        if len(self.active_threads) >= self.max_threads:
            return

        if not self.queue:
            return

        task = self.queue.pop(0)

        thread = QtCore.QThread()
        worker = YTDLPWorker(task["url"], task["opts"], task["downloading_t"])
        worker.moveToThread(thread)

        thread.started.connect(worker.run)

        worker.finished.connect(task["callbacks"]["finished"])
        worker.error.connect(task["callbacks"]["error"])
        worker.log.connect(task["callbacks"]["log"])

        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)

        thread.finished.connect(lambda: self._on_thread_finished(thread, worker))

        self.active_threads.append(thread)

        thread.start()

    def _on_thread_finished(self, thread, worker):
        if thread in self.active_threads:
            self.active_threads.remove(thread)

        worker.deleteLater()
        thread.deleteLater()

        self._try_start_next()

    def clear(self):
        self.queue.clear()

class SeekSlider(QtWidgets.QSlider):

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

        self.track_length_ms = 0

        self.setMouseTracking(True)

    def format_time(self, seconds):
        minutes = int(seconds) // 60
        seconds = int(seconds) % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_hover_time(self, x):
        ratio = x / max(1, self.width())

        value = ratio * self.track_length_ms

        return value / 1000

    def mousePressEvent(self, event):

        if event.button() == QtCore.Qt.LeftButton:

            val = QtWidgets.QStyle.sliderValueFromPosition(
                self.minimum(),
                self.maximum(),
                event.x(),
                self.width()
            )

            self.setValue(val)

            self.sliderMoved.emit(val)

            self.sliderReleased.emit()

            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):

        hover_seconds = self.get_hover_time(event.x())

        text = self.format_time(hover_seconds)

        QtWidgets.QToolTip.showText(
            event.globalPos(),
            text,
            self
        )

        super().mouseMoveEvent(event)

class InfoWindow(QtWidgets.QDialog):
    def __init__(self, url, track_url_t, source_url_t, open_in_browser_t, copy_t, copy_callback, parent=None):
        super().__init__(parent)

        self.url = url
        self.copy_callback = copy_callback

        self.setWindowTitle(track_url_t)
        self.setFixedSize(450, 180)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(source_url_t)
        font = QtGui.QFont("Arial", 14, QtGui.QFont.Bold)
        label.setFont(font)
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label)

        self.url_entry = QtWidgets.QLineEdit()
        self.url_entry.setText(url)
        self.url_entry.setReadOnly(True)
        self.url_entry.setFixedWidth(380)
        layout.addWidget(self.url_entry, alignment=QtCore.Qt.AlignCenter)

        btn_frame = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        open_btn = QtWidgets.QPushButton(open_in_browser_t)
        open_btn.setFixedWidth(150)
        open_btn.clicked.connect(lambda: webbrowser.open(url))
        open_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        copy_btn = QtWidgets.QPushButton(copy_t)
        copy_btn.setFixedWidth(100)
        copy_btn.setStyleSheet("QPushButton {\n"
                               "   background-color: #7d7d7d;\n"
                               "   color: white;\n"
                               "}"
                               "QPushButton:hover {\n"
                               "   background-color: #595959\n"
                               "}")
        copy_btn.clicked.connect(self.copy_link)
        copy_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(copy_btn)

        layout.addWidget(btn_frame, alignment=QtCore.Qt.AlignCenter)

        self.setStyleSheet("""
            QDialog {
                background-color: #1d1f28;
                color: white;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #2b2f45;
                color: white;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton {
                background-color: #32323c;
                color: white;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #444452;
            }
        """)

    def copy_link(self):
        self.copy_callback(self.url)

class DragButton(QtWidgets.QPushButton):
    def __init__(self, path, parent_window):
        super().__init__()
        self.path = path
        self.parent_window = parent_window
        self.drag_start_position = QtCore.QPoint()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_start_position = event.pos()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & QtCore.Qt.LeftButton):
            return

        if (
            event.pos() - self.drag_start_position
        ).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            return

        drag = QtGui.QDrag(self)

        mime_data = QtCore.QMimeData()
        mime_data.setText(os.path.basename(self.path))

        drag.setMimeData(mime_data)

        drag.exec_(QtCore.Qt.MoveAction)

class Mainwindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        if build_os == "Darwin":
            self.save_file = f"/Users/{username}/Afory/playlists_data.json"
            self.settings_file = f"/Users/{username}/Afory/settings_data.json"
            self.link_file = f"/Users/{username}/Afory/links_data.json"
        else:
            self.save_file = f"C:/Users/{username}/Afory/playlists_data.json"
            self.settings_file = f"C:/Users/{username}/Afory/settings_data.json"
            self.link_file = f"C:/Users/{username}/Afory/links_data.json"

        pygame.mixer.init()

        hotkeys = keyboard.GlobalHotKeys({
            '<alt>+<space>': self.toggle_play_pause,
            '<alt>+<right>': self.set_next,
            '<alt>+<left>': self.set_previous,
            '<alt>+<up>': lambda: self.adjust_volume_step(0.1),
            '<alt>+<down>': lambda: self.adjust_volume_step(-0.1)
        })

        hotkeys.start()

        self.stdout_redirect = ConsoleRedirect(sys.stdout)
        self.stderr_redirect = ConsoleRedirect(sys.stderr)
        self.stdin_redirect = ConsoleRedirect(sys.stdin)
        self.stdout_redirect.text_written.connect(self.append_console)
        self.stderr_redirect.text_written.connect(self.append_console_error)
        self.stdin_redirect.text_written.connect(self.append_console_in)
        sys.stdout = self.stdout_redirect
        sys.stderr = self.stderr_redirect

        self.links = self.load_links()
        self.playlists = self.load_data()
        self.download_manager = DownloadManager(max_threads=1)
        self.settings = self.load_settings()
        self.console_buffer = []
        self.current_playlist_name = "All"
        self.current_track_path = None
        self.current_track_name = None
        self.length = 1
        self.console = None
        self.current_music_num = 0
        self.current_view_length = 0
        self.loop = False
        self.is_played = False
        self.is_stopped = True
        self.is_repeat = False
        self.is_paused = False
        self.current_playlist = None
        self.setObjectName("Mainwindow")

        if build_os == "Darwin":
            self.main_font = QtGui.QFont()
            self.main_font.setFamily("Comic Sans MS")
            self.main_font.setPointSize(12)
        else:
            self.main_font = QtGui.QFont()
            self.main_font.setFamily("Comic Sans MS")
            self.main_font.setPointSize(10)

        if self.settings.get("font"):
            self.main_font.setFamily(self.settings.get("font", "Comic Sans MS"))

        if build_os == "Windows":
            self.setWindowIcon(QtGui.QIcon(resource_path("assets/icon.ico")))

        self.setFixedSize(825, 590)
        pygame.mixer.music.set_volume(self.settings.get("volume", 0.7))

        self.space_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Space"), self)
        self.space_shortcut.activated.connect(self.toggle_play_pause)

        self.left_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Left"), self)
        self.left_shortcut.activated.connect(self.set_previous)

        self.right_shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Right"), self)
        self.right_shortcut.activated.connect(self.set_next)

        # These prints for testing stdout, skip them.

        print("pygame 2.6.1 (SDL 2.28.4, Python 3.10.11)")
        print("Hello from the pygame community. https://www.pygame.org/contribute.html")

        self.playlists_t = "Playlists"
        self.new_playlist = "New Playlist"
        self.del_playlist = "Delete playlist"
        self.select_playlist_t = "Select playlist"
        self.add_mp3 = "Add MP3"
        self.download_from_YT = "Web download"
        self.del_from_list = "Delete track"
        self.track_not_selected = "Track not selected"
        self.settings_t = "Settings"
        self.select_playlist_and_track = "Select playlist and track to start"
        self.new_playlist_nop = "New playlist"
        self.enter_playlist_name = "Enter playlist name:"
        self.warning = "Warning"
        self.playlist_already_exists = "This playlist already exists"
        self.error = "Error"
        self.cant_delete_main = "Cant delete main list"
        self.deleting = "Deleting"
        self.delete_playlist_t = "Delete playlist"
        self.file_not_found = "File not found (possibly deleted from disk)"
        self.track_deleted = "Track deleted"
        self.file_no_longer_exists = "The file no longer exists at the specified path."
        self.select_track = "Select track"
        self.playback = "Playback:"
        self.playback_on_pause = "Playback on pause:"
        self.playlist_ended = "Playlist ended"
        self.playback_stopped = "Playback stopped"
        self.settings_op = "Settings"
        self.design_theme = "Design theme:"
        self.volum = "Volume"
        self.open_download_folder = "Open downloads folder"
        self.tutorial = "Tutorial"
        self.developerss = "Developers:"
        self.tutorial_does_not_exists = "Tutorial does not currently exist."
        self.supported_links = "Supported Links: YT, Newgrounds, Soundcloud"
        self.track_loading = "Track loading..."
        self.done = "✅ Done"
        self.lang = "Language:"
        self.click_stop_then_select = "Click stop, then select new track to play"
        self.shuffle_text = "Shuffle"
        self.stop_loading = "Stop download"
        self.loading_stopped = "Loading stopped"
        self.loop_text = "Repeat"
        self.del_loop_then_select = "Turn off repeat, then select new track"
        self.dont_repeat = "Dont repeat"
        self.show_tooltip_text = "Show slider tip"
        self.are_you_sure_delete_track = "Are you sure want to delete this track?"
        self.rename_text= "Rename"
        self.renaming_text = "Renaming"
        self.new_name = "New name:"
        self.track_url_t = "Track URL"
        self.source_url_t = "Source (URL):"
        self.open_in_browser_t = "Open in Browser"
        self.copy_t = "Copy"
        self.copied_t = "Copied!"
        self.enter_new_name_for_t = "Enter new name for"
        self.renaming_playlist_t = "Rename playlist"
        self.see_keybinds_t = "See keybinds"
        self.keybinds_t = "Keybinds"
        self.first_keybind_t = "alt + arrow right/left: next/previous track"
        self.second_keybind_t = "alt + space: play/pause"
        self.third_keybind_t = "alt + arrow up/down: adjust volume"
        self.works_even_not_in_app_t = "These keybinds works even if you are not in app"
        self.keybinds_note = "You need to access app the accessibility"
        self.current_index_t = "Current index: "
        self.enter_new_index_t = "Enter new index "
        self.track_index_done_t = "Track index is set to "
        self.add_playlist_tooltip = "Creates new playlist"
        self.delete_playlist_tooltip = "Deletes playlist"
        self.settings_tooltip = "Settings..."
        self.add_mp3_tooltip = "Adds audio from hard disk to playlist"
        self.web_download_tooltip = "Downloading from link"
        self.shuffle_tooltip = "Shuffles current playlist"
        self.repeat_tooltip = "Repeats current track"
        self.play_pause_tooltip = "Play / pause"
        self.prev_track_tooltip = "Previous track"
        self.next_track_tooltip = "Next track"
        self.playlist_select_tooltip = "Select this playlist"
        self.nothing_to_display = "Nothing to display"
        self.select_track_tooltip = "Select this track"
        self.link_tooltip = "Shows used link"
        self.delete_track_tooltip = "Delete..."
        self.rename_tooltip = "Rename..."
        self.move_tooltip = "Move..."
        self.application_font = "Application font: "
        self.cant_rename_when_use = "Error: Cant rename track while in use. Please deselect this track."
        self.cant_delete_when_use = "Error: Cant delete track while in use. Please deselect this track."
        self.console_t = "Console"
        self.open_console_t = "Open console"
        self.console_already_opened = "Console already opened"

        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowCloseButtonHint |
            QtCore.Qt.WindowMinimizeButtonHint
        )
        self.setupUi()
        self.setupQSS()
        self.setupText()
        self.setupIcons()
        self.setupTooltip()
        self.update_playlist_menu()
        self.refresh_tracks_display()
        self.loop_timer = QtCore.QTimer()
        self.loop_timer.timeout.connect(self.start_loop)
        self.loop_timer.start(90)
        self.apply_lang()
        self.show()

    def adjust_volume_step(self, step):
        current_vol = self.settings.get("volume")
        new_vol = current_vol + step
        if new_vol >= 1.0:
            new_vol = 1.0
        elif new_vol <= 0.0:
            new_vol = 0.0
        print(new_vol)
        self.settings["volume"] = new_vol
        self.volume_slider.setValue(int(new_vol * 1000))
        self.volume_percentage.setText(f"{int(new_vol) * 100} %")
        pygame.mixer.music.set_volume(new_vol)
        self.save_settings()

    def setupUi(self):
        self.setStyleSheet(
                "QMainWindow {"
                "background-color: #1d1f28;"
                "}"
                "#btn{\n"
                "    border-radius: 5px;\n"
                "    background-color: transparent;\n"
                "    color: white;\n"
                "    text-align: left\n"
                "}\n"
                "#btn:hover{\n"
                "    background-color: #444452;\n"
                "}\n"
                "#move_btn{\n"
                "    border-radius: 5px;\n"
                "    background-color: transparent;\n"
                "    color: white;\n"
                "}\n"
                "#move_btn:hover {\n"
                "    background-color: #444452;\n"
                "}\n"
                "#ren_btn{\n"
                "    border-radius: 5px;\n"
                "    background-color: transparent;\n"
                "    color: white;\n"
                "}\n"
                "#ren_btn:hover {\n"
                "    background-color: #444452;\n"
                "}\n"
                "#del_btn{\n"
                "    border-radius: 5px;\n"
                "    background-color: transparent;\n"
                "    color: white;\n"
                "}\n"
                "#del_btn:hover {\n"
                "    background-color: #444452;\n"
                "}\n"
                "#link_btn{\n"
                "    border-radius: 5px;\n"
                "    background-color: transparent;\n"
                "    color: white;\n"
                "}\n"
                "#link_btn:hover {\n"
                "    background-color: #444452;\n"
                "}\n"
                """
                #track_row{
                            background-color: "#2b2f45";
                            border-radius: 5px;
                        }
                """
        )
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QtGui.QColor(0, 0, 0, 90))
        self.sidebar = QtWidgets.QFrame(self)
        self.sidebar.setGeometry(QtCore.QRect(0, 0, 201, 590))
        self.sidebar.setAutoFillBackground(False)
        self.sidebar.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.sidebar.setFrameShadow(QtWidgets.QFrame.Raised)
        self.sidebar.setObjectName("sidebar")
        self.add_playlist_btn = QtWidgets.QPushButton(self.sidebar)
        self.add_playlist_btn.setGeometry(QtCore.QRect(10, 50, 181, 31))
        self.add_playlist_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.add_playlist_btn.setToolTip(self.add_playlist_tooltip)
        self.add_playlist_btn.setObjectName("add_playlist_btn")
        self.add_playlist_btn.setGraphicsEffect(shadow)
        self.add_playlist_btn.clicked.connect(self.add_playlist)
        self.add_playlist_btn.setFont(self.main_font)
        self.afory_label = QtWidgets.QLabel(self.sidebar)
        self.afory_label.setGeometry(QtCore.QRect(25, 10, 150, 31))
        self.afory_label.setAlignment(QtCore.Qt.AlignCenter)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.afory_label.setFont(font)
        self.afory_label.setObjectName("afory_label")
        self.delete_playlist_btn = QtWidgets.QPushButton(self.sidebar)
        self.delete_playlist_btn.setGeometry(QtCore.QRect(10, 90, 181, 31))
        self.delete_playlist_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.delete_playlist_btn.setToolTip(self.delete_playlist_tooltip)
        self.delete_playlist_btn.setObjectName("delete_playlist_btn")
        self.delete_playlist_btn.clicked.connect(self.delete_playlist)
        shadow2 = QtWidgets.QGraphicsDropShadowEffect()
        self.delete_playlist_btn.setFont(self.main_font)
        shadow2.setBlurRadius(20)
        shadow2.setXOffset(0)
        shadow2.setYOffset(0)
        shadow2.setColor(QtGui.QColor(0, 0, 0, 90))
        self.delete_playlist_btn.setGraphicsEffect(shadow2)
        self.playlists_frame = QtWidgets.QScrollArea(self.sidebar)
        self.playlists_frame.setStyleSheet("""
            background-color: transparent;
            border-radius: 5px;""")
        self.playlists_frame.setWidgetResizable(True)
        self.playlists_frame.setGeometry(QtCore.QRect(10, 130, 181, 400))
        self.playlist_container = QtWidgets.QWidget()
        self.playlist_layout = QtWidgets.QVBoxLayout(self.playlist_container)
        self.playlist_layout.setSpacing(2)
        self.playlist_layout.setContentsMargins(0, 0, 0, 0)
        self.playlists_frame.setWidget(self.playlist_container)
        self.playlists_frame.setWidget(self.playlist_container)
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 181, 381))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.playlist_btns_frame = QtWidgets.QFrame(self.scrollAreaWidgetContents)
        self.playlist_btns_frame.setGeometry(QtCore.QRect(10, 10, 161, 31))
        self.playlist_btns_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.playlist_btns_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.playlist_btns_frame.setObjectName("playlist_btns_frame")
        self.playlist = QtWidgets.QPushButton(self.playlist_btns_frame)
        self.playlist.setGeometry(QtCore.QRect(0, 0, 121, 32))
        self.playlist.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.playlist.setObjectName("playlist")
        self.rename_p_btn = QtWidgets.QPushButton(self.playlist_btns_frame)
        self.rename_p_btn.setGeometry(QtCore.QRect(130, 0, 31, 32))
        self.rename_p_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.rename_p_btn.setObjectName("rename_p_btn")
        shadow3 = QtWidgets.QGraphicsDropShadowEffect()
        shadow3.setBlurRadius(35)
        shadow3.setXOffset(0)
        shadow3.setYOffset(8)
        shadow3.setColor(QtGui.QColor(0, 0, 0, 90))
        self.settings_btn = QtWidgets.QPushButton(self.sidebar)
        self.settings_btn.setGeometry(QtCore.QRect(10, 540, 181, 31))
        self.settings_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.settings_btn.setToolTip(self.settings_tooltip)
        self.settings_btn.setObjectName("settings_btn")
        self.settings_btn.setGraphicsEffect(shadow3)
        self.settings_btn.clicked.connect(self.settings_open)
        self.settings_btn.setFont(self.main_font)
        self.Tracks_frame = QtWidgets.QScrollArea(self)
        self.Tracks_frame.setStyleSheet("""
            background-color: transparent;
            border-radius: 5px;""")
        self.Tracks_frame.setGeometry(QtCore.QRect(230, 50, 571, 331))
        self.Tracks_frame.setWidgetResizable(True)
        self.tracks_container = QtWidgets.QWidget()

        self.tracks_layout = QtWidgets.QVBoxLayout(self.tracks_container)
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        self.tracks_layout.setSpacing(2)
        self.Tracks_frame.setWidget(self.tracks_container)
        self.label_current_playlist = QtWidgets.QLabel(self)
        self.label_current_playlist.setGeometry(QtCore.QRect(230, 10, 571, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(20)
        font.setBold(True)
        font.setWeight(75)
        self.label_current_playlist.setFont(font)
        self.label_current_playlist.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_current_playlist.setStyleSheet("color: white;")
        self.label_current_playlist.setAlignment(QtCore.Qt.AlignCenter)
        self.label_current_playlist.setObjectName("label_current_playlist")

        shadow4 = QtWidgets.QGraphicsDropShadowEffect()
        shadow4.setBlurRadius(20)
        shadow4.setXOffset(0)
        shadow4.setYOffset(0)
        shadow4.setColor(QtGui.QColor(0, 0, 0, 180))

        self.add_mp3_btn = QtWidgets.QPushButton(self)
        self.add_mp3_btn.setGeometry(QtCore.QRect(230, 390, 131, 31))
        self.add_mp3_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.add_mp3_btn.setToolTip(self.add_mp3_tooltip)
        self.add_mp3_btn.setObjectName("add_mp3_btn")
        self.add_mp3_btn.clicked.connect(self.add_local_file)
        self.add_mp3_btn.setGraphicsEffect(shadow4)
        self.add_mp3_btn.setFont(self.main_font)

        shadow5 = QtWidgets.QGraphicsDropShadowEffect()
        shadow5.setBlurRadius(20)
        shadow5.setXOffset(0)
        shadow5.setYOffset(0)
        shadow5.setColor(QtGui.QColor(0, 0, 0, 180))

        self.web_download_btn = QtWidgets.QPushButton(self)
        self.web_download_btn.setGeometry(QtCore.QRect(370, 390, 131, 31))
        self.web_download_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.web_download_btn.setToolTip(self.web_download_tooltip)
        self.web_download_btn.setObjectName("web_download_btn")
        self.web_download_btn.clicked.connect(self.download_youtube)
        self.web_download_btn.setGraphicsEffect(shadow5)
        self.web_download_btn.setFont(self.main_font)

        shadow6 = QtWidgets.QGraphicsDropShadowEffect()
        shadow6.setBlurRadius(20)
        shadow6.setXOffset(0)
        shadow6.setYOffset(0)
        shadow6.setColor(QtGui.QColor(0, 0, 0, 180))

        self.shuffle_btn = QtWidgets.QPushButton(self)
        self.shuffle_btn.setGeometry(QtCore.QRect(530, 390, 131, 31))
        self.shuffle_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.shuffle_btn.setToolTip(self.shuffle_tooltip)
        self.shuffle_btn.setObjectName("shuffle_btn")
        self.shuffle_btn.clicked.connect(self.shuffle_current_playlist)
        self.shuffle_btn.setGraphicsEffect(shadow6)
        self.shuffle_btn.setFont(self.main_font)

        shadow7 = QtWidgets.QGraphicsDropShadowEffect()
        shadow7.setBlurRadius(20)
        shadow7.setXOffset(0)
        shadow7.setYOffset(0)
        shadow7.setColor(QtGui.QColor(0, 0, 0, 180))

        self.repeat_btn = QtWidgets.QPushButton(self)
        self.repeat_btn.setGeometry(QtCore.QRect(670, 390, 131, 31))
        self.repeat_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.repeat_btn.setToolTip(self.repeat_tooltip)
        self.repeat_btn.setObjectName("repeat_btn")
        self.repeat_btn.clicked.connect(self.set_track_loop)
        self.repeat_btn.setGraphicsEffect(shadow7)
        self.repeat_btn.setFont(self.main_font)

        self.current_track_label = QtWidgets.QLabel(self)
        self.current_track_label.setGeometry(QtCore.QRect(230, 430, 571, 20))
        self.current_track_label.setAlignment(QtCore.Qt.AlignCenter)
        self.current_track_label.setObjectName("current_track_label")
        self.current_track_label.setFont(self.main_font)

        self.play_pause_btn = QtWidgets.QPushButton(self)
        self.play_pause_btn.setGeometry(QtCore.QRect(480, 460, 71, 71))
        self.play_pause_btn.setObjectName("play_pause_btn")
        self.play_pause_btn.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.prev_track_btn = QtWidgets.QPushButton(self)
        self.prev_track_btn.setGeometry(QtCore.QRect(420, 470, 51, 51))
        self.prev_track_btn.setObjectName("prev_track_btn")
        self.prev_track_btn.clicked.connect(self.set_previous)
        self.next_track_btn = QtWidgets.QPushButton(self)
        self.next_track_btn.setGeometry(QtCore.QRect(560, 470, 51, 51))
        self.next_track_btn.setObjectName("next_track_btn")
        self.next_track_btn.clicked.connect(self.set_next)
        self.volume_lab = QtWidgets.QLabel(self)
        self.volume_lab.setGeometry(640, 477, 25, 25)
        self.volume_percentage = QtWidgets.QLabel(self)
        self.volume_percentage.setGeometry(670, 477, 50, 25)
        self.volume_percentage.setText("100 %")
        self.volume_percentage.setStyleSheet("color: white")
        self.volume_percentage.setFont(self.main_font)

        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.volume_slider.setGeometry(710, 480, 101, 23)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(1000)
        self.volume_slider.setValue(int(self.settings.get("volume", 0.7) * 1000))
        self.volume_slider.setCursor((QtGui.QCursor(QtCore.Qt.PointingHandCursor)))
        self.volume_slider.setStyleSheet("""
        QSlider::groove:horizontal {
            background: #444;

            height: 4px;

            border-radius: 2px;
        }

        QSlider::sub-page:horizontal {
            background: #aab0b4;

            border-radius: 2px;
        }

        QSlider::add-page:horizontal {
            background: #444;

            border-radius: 2px;
        }

        QSlider::handle:horizontal {
            background: white;

            width: 14px;

            margin: -5px 0;

            border-radius: 7px;
        }

        QSlider::handle:horizontal:hover {
            background: #bfbfbf;
        }
        """)
        self.seekbar = SeekSlider(QtCore.Qt.Horizontal, self)
        self.seekbar.setGeometry(230, 540, 571, 5)
        self.seekbar.setMinimum(0)
        self.seekbar.setMaximum(1000)
        self.seekbar.setValue(0)
        self.seekbar.setFixedHeight(20)
        self.seekbar.sliderMoved.connect(self.set_music_to_current_slide_pos)
        self.seekbar.setStyleSheet("""
        QSlider::groove:horizontal {
            background: #444;

            height: 4px;

            border-radius: 2px;
        }

        QSlider::sub-page:horizontal {
            background: #aab0b4;

            border-radius: 2px;
        }

        QSlider::add-page:horizontal {
            background: #444;

            border-radius: 2px;
        }

        QSlider::handle:horizontal {
            background: white;

            width: 14px;

            margin: -5px 0;

            border-radius: 7px;
        }

        QSlider::handle:horizontal:hover {
            background: #bfbfbf;
        }
        """)

        self.seekbar.setCursor((QtGui.QCursor(QtCore.Qt.PointingHandCursor)))
        self.current_track_label_2 = QtWidgets.QLabel(self)
        self.current_track_label_2.setGeometry(QtCore.QRect(230, 560, 571, 20))
        self.current_track_label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.current_track_label_2.setObjectName("current_track_label_2")
        self.current_track_label_2.setFont(self.main_font)

        QtCore.QMetaObject.connectSlotsByName(self)
        self.play_pause_btn.setCursor((QtGui.QCursor(QtCore.Qt.PointingHandCursor)))
        self.next_track_btn.setCursor((QtGui.QCursor(QtCore.Qt.PointingHandCursor)))
        self.prev_track_btn.setCursor((QtGui.QCursor(QtCore.Qt.PointingHandCursor)))

    def setupQSS(self):
        self.afory_label.setStyleSheet("color: white;")
        self.sidebar.setStyleSheet("background-color: #292934;\n"
                            "border-color: #454444;\n"
                            "border-width: 50px;")
        self.add_playlist_btn.setStyleSheet("QPushButton{\n"
                                "    border-radius: 15px;\n"
                                "    background-color: #32323c;\n"
                                "    color: white;\n"
                                "    border-color: #7476a0;\n"
                                "    color: white;\n"
                                "    border: 2px solid #7476a0;\n"
                                "}\n"
                                "QPushButton:hover {\n"
                                "    background-color: #444452;\n"
                                "}\n"
                                            "QToolTip {\n"
                                            "    background-color: #222;\n"
                                            "    color: white;\n"
                                            "    border: 1px solid #444;\n"
                                            "    padding: 4px;\n"
                                            "    border-radius: 6px;\n"
                                            "}"
                                            )
        self.delete_playlist_btn.setStyleSheet("QPushButton{\n"
                                    "    border-radius: 15px;\n"
                                    "    background-color: #32323c;\n"
                                    "    color: white;\n"
                                    "    border-color: #7476a0;\n"
                                    "    color: white;\n"
                                    "    border: 2px solid #7476a0;\n"
                                    "}\n"
                                    "QPushButton:hover {\n"
                                    "    background-color: #444452;\n"
                                    "}\n"
                                               "QToolTip {\n"
                                               "    background-color: #222;\n"
                                               "    color: white;\n"
                                               "    border: 1px solid #444;\n"
                                               "    padding: 4px;\n"
                                               "    border-radius: 6px;\n"
                                               "}"
                                               )
        self.playlist_btns_frame.setStyleSheet("background-color: #323242;")
        self.delete_playlist_btn.setStyleSheet("QPushButton{\n"
                                    "    border-radius: 15px;\n"
                                    "    background-color: #32323c;\n"
                                    "    color: white;\n"
                                    "    border-color: #7476a0;\n"
                                    "    color: white;\n"
                                    "    border: 2px solid #7476a0;\n"
                                    "}\n"
                                    "QPushButton:hover {\n"
                                    "    background-color: #444452;\n"
                                    "}\n"
                                               "QToolTip {\n"
                                               "    background-color: #222;\n"
                                               "    color: white;\n"
                                               "    border: 1px solid #444;\n"
                                               "    padding: 4px;\n"
                                               "    border-radius: 6px;\n"
                                               "}"
                                               )
        self.playlist.setStyleSheet("QPushButton{\n"
                            "    border-radius: 5px;\n"
                            "    background-color: transparent;\n"
                            "    color: white;\n"
                            "}\n"
                            "QPushButton:hover {\n"
                            "    background-color: #444452;\n"
                            "}\n")
        self.rename_p_btn.setStyleSheet("QPushButton{\n"
                                "    border-radius: 5px;\n"
                                "    background-color: transparent;\n"
                                "    color: white;\n"
                                "}\n"
                                "QPushButton:hover {\n"
                                "    background-color: #444452;\n"
                                "}\n"
                                        "QToolTip {\n"
                                        "    background-color: #222;\n"
                                        "    color: white;\n"
                                        "    border: 1px solid #444;\n"
                                        "    padding: 4px;\n"
                                        "    border-radius: 6px;\n"
                                        "}"
                                        )
        self.settings_btn.setStyleSheet("QPushButton{\n"
                                "    border-radius: 15px;\n"
                                "    background-color: #32323c;\n"
                                "    color: white;\n"
                                "    border-color: #7476a0;\n"
                                "    color: white;\n"
                                "    border: 2px solid #7476a0;\n"
                                "}\n"
                                "QPushButton:hover {\n"
                                "    background-color: #444452;\n"
                                "}\n"
                                        "QToolTip {\n"
                                        "    background-color: #222;\n"
                                        "    color: white;\n"
                                        "    border: 1px solid #444;\n"
                                        "    padding: 4px;\n"
                                        "    border-radius: 6px;\n"
                                        "}"
                                        )
        self.add_mp3_btn.setStyleSheet("QPushButton{\n"
                            "    border-radius: 15px;\n"
                            "    background-color: #32323c;\n"
                            "    color: white;\n"
                            "    border-color: #7476a0;\n"
                            "    color: white;\n"
                            "    border: 2px solid #7476a0;\n"
                            "}\n"
                            "QPushButton:hover {\n"
                            "    background-color: #444452;\n"
                            "}\n"
                                       "QToolTip {\n"
                                       "    background-color: #222;\n"
                                       "    color: white;\n"
                                       "    border: 1px solid #444;\n"
                                       "    padding: 4px;\n"
                                       "    border-radius: 6px;\n"
                                       "}"
                                       )
        self.web_download_btn.setStyleSheet("QPushButton{\n"
                                "    border-radius: 15px;\n"
                                "    background-color: #32323c;\n"
                                "    color: white;\n"
                                "    border-color: #7476a0;\n"
                                "    color: white;\n"
                                "    border: 2px solid #7476a0;\n"
                                "}\n"
                                "QPushButton:hover {\n"
                                "    background-color: #444452;\n"
                                "}\n"
                                            "QToolTip {\n"
                                            "    background-color: #222;\n"
                                            "    color: white;\n"
                                            "    border: 1px solid #444;\n"
                                            "    padding: 4px;\n"
                                            "    border-radius: 6px;\n"
                                            "}"
                                            )
        self.shuffle_btn.setStyleSheet("QPushButton{\n"
                                "    border-radius: 15px;\n"
                                "    background-color: #32323c;\n"
                                "    color: white;\n"
                                "    border-color: #7476a0;\n"
                                "    color: white;\n"
                                "    border: 2px solid #7476a0;\n"
                                "}\n"
                                "QPushButton:hover {\n"
                                "    background-color: #444452;\n"
                                "}\n"
                                       "QToolTip {\n"
                                       "    background-color: #222;\n"
                                       "    color: white;\n"
                                       "    border: 1px solid #444;\n"
                                       "    padding: 4px;\n"
                                       "    border-radius: 6px;\n"
                                       "}"
                                       )
        self.repeat_btn.setStyleSheet("QPushButton{\n"
                                "    border-radius: 15px;\n"
                                "    background-color: #32323c;\n"
                                "    color: white;\n"
                                "    border-color: #7476a0;\n"
                                "    color: white;\n"
                                "    border: 2px solid #7476a0;\n"
                                "}\n"
                                "QPushButton:hover {\n"
                                "    background-color: #444452;\n"
                                "}\n"
                                      "QToolTip {\n"
                                      "    background-color: #222;\n"
                                      "    color: white;\n"
                                      "    border: 1px solid #444;\n"
                                      "    padding: 4px;\n"
                                      "    border-radius: 6px;\n"
                                      "}"
                                      )
        self.current_track_label.setStyleSheet("color: white;")
        self.play_pause_btn.setStyleSheet("QPushButton{\n"
                                "    border-radius: 35px;\n"
                                "    background-color: #2b2f45;\n"
                                "    color: white;\n"
                                "}\n"
                                "QPushButton:hover {\n"
                                "    background-color: #444452;\n"
                                "}\n"
                                          "QToolTip {\n"
                                          "    background-color: #222;\n"
                                          "    color: white;\n"
                                          "    border: 1px solid #444;\n"
                                          "    padding: 4px;\n"
                                          "    border-radius: 6px;\n"
                                          "}"
                                          )
        self.prev_track_btn.setStyleSheet("QPushButton{\n"
                                "    border-radius: 25px;\n"
                                "    background-color: #2b2f45;\n"
                                "    color: white;\n"
                                "}\n"
                                "QPushButton:hover {\n"
                                "    background-color: #444452;\n"
                                "}\n"
                                          "QToolTip {\n"
                                          "    background-color: #222;\n"
                                          "    color: white;\n"
                                          "    border: 1px solid #444;\n"
                                          "    padding: 4px;\n"
                                          "    border-radius: 6px;\n"
                                          "}"
                                          )
        self.next_track_btn.setStyleSheet("QPushButton{\n"
                                "    border-radius: 25px;\n"
                                "    background-color: #2b2f45;\n"
                                "    color: white;\n"
                                "}\n"
                                "QPushButton:hover {\n"
                                "    background-color: #444452;\n"
                                "}\n"
                                          "QToolTip {\n"
                                          "    background-color: #222;\n"
                                          "    color: white;\n"
                                          "    border: 1px solid #444;\n"
                                          "    padding: 4px;\n"
                                          "    border-radius: 6px;\n"
                                          "}"
                                          )
        self.current_track_label_2.setStyleSheet("color: white;")

    def setupText(self):
        self.setWindowTitle("Afory")
        self.add_playlist_btn.setText(f" {self.new_playlist}")
        self.afory_label.setText(self.playlists_t)
        self.delete_playlist_btn.setText(f" {self.delete_playlist_t}")
        self.settings_btn.setText(f" {self.settings_t}")
        self.label_current_playlist.setText("All")
        self.add_mp3_btn.setText(f" {self.add_mp3}")

        if len(self.download_from_YT) > 12:
            self.download_from_YT = self.download_from_YT[:12] + "..."
        self.web_download_btn.setText(f" {self.download_from_YT}")

        self.shuffle_btn.setText(f" {self.shuffle_text}")
        self.repeat_btn.setText(f" {self.loop_text}")
        self.current_track_label.setText(self.track_not_selected)
        self.play_pause_btn.setToolTip(self.play_pause_tooltip)
        self.prev_track_btn.setToolTip(self.prev_track_tooltip)
        self.next_track_btn.setToolTip(self.next_track_tooltip)
        self.current_track_label_2.setText(self.select_playlist_and_track)

    def setupTooltip(self):
        self.add_playlist_btn.setToolTip(self.add_playlist_tooltip)
        self.delete_playlist_btn.setToolTip(self.delete_playlist_tooltip)
        self.settings_btn.setToolTip(self.settings_tooltip)
        self.add_mp3_btn.setToolTip(self.add_mp3_tooltip)
        self.web_download_btn.setToolTip(self.web_download_tooltip)
        self.shuffle_btn.setToolTip(self.shuffle_tooltip)
        self.repeat_btn.setToolTip(self.repeat_tooltip)
        self.play_pause_btn.setToolTip(self.play_pause_tooltip)
        self.prev_track_btn.setToolTip(self.prev_track_tooltip)
        self.next_track_btn.setToolTip(self.next_track_tooltip)

    def setupIcons(self):
        self.add_playlist_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/plus-symbol.png")))
        self.add_playlist_btn.setIconSize(QtCore.QSize(16, 16))
        self.delete_playlist_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/bin.png")))
        self.add_mp3_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/plus-symbol.png")))
        self.add_mp3_btn.setIconSize(QtCore.QSize(16, 16))
        self.web_download_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/web.png")))
        self.web_download_btn.setIconSize(QtCore.QSize(16, 16))
        self.shuffle_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/shuffle.png")))
        self.shuffle_btn.setIconSize(QtCore.QSize(22, 22))
        self.repeat_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/repeat.png")))
        self.repeat_btn.setIconSize(QtCore.QSize(20, 20))
        self.prev_track_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/previous.png")))
        self.next_track_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/next.png")))
        self.prev_track_btn.setIconSize(QtCore.QSize(30, 30))
        self.next_track_btn.setIconSize(QtCore.QSize(30, 30))
        self.play_pause_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/play-button.png")))
        self.play_pause_btn.setIconSize(QtCore.QSize(30, 30))
        self.settings_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/settings.png")))
        pixmap = QtGui.QPixmap(resource_path("assets/icons/volume.png"))
        pixmap = pixmap.scaled(
            25,
            25,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.volume_lab.setPixmap(pixmap)

    def change_volume(self, value):
        self.volume_percentage.setText(f"{value // 10} %")
        pygame.mixer.music.set_volume(value / 1000)
        self.settings["volume"] = value / 1000
        self.save_settings()

    def save_data(self):
        try:
            with open(self.save_file, "w", encoding="utf-8") as f:
                json.dump(self.playlists, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Save error: {e}")

    def load_data(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"All": []}
        return {"All": []}

    def load_links(self):
        if os.path.exists(self.link_file):
            try:
                with open(self.link_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_links(self):
        with open(self.link_file, "w", encoding="utf-8") as f:
            json.dump(self.links, f, ensure_ascii=False, indent=4)

    def save_settings(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=4)

    def load_settings(self):
        default_settings = {"volume": 0.7, "font": "Comic Sans MS", "language": "English"}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    return settings
            except:
                return default_settings
        return default_settings

    def load_language(self, lang_code):
        file_path = resource_path(f"assets/localization/{lang_code}.json")

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, value in data.items():
                    setattr(self, key, value)

    def apply_lang(self):
        self.current_lang = self.settings.get("language")
        print(self.current_lang)
        if self.current_lang == "Русский":
            self.load_language("ru")
        elif self.current_lang == "English":
            self.load_language("en")
        elif self.current_lang == "Deutsch":
            self.load_language("de")
        elif self.current_lang == "ქართული":
            self.load_language("ka")
        elif self.current_lang == "español":
            self.load_language("es")
        elif self.current_lang == "Українська":
            self.load_language("uk")
        elif self.current_lang == "Қазақ":
            self.load_language("kk")
        elif self.current_lang == "Polski":
            self.load_language("pl")
        elif self.current_lang == "Français":
            self.load_language("fr")
        elif self.current_lang == "日本語":  # japan
            self.load_language("ja")
        elif self.current_lang == "中國人":  # chinese
            self.load_language("zh")
        elif self.current_lang == "Italiano":
            self.load_language("it")
        elif self.current_lang == "Azərbaycan dili":  # azerba
            self.load_language("az")
        elif self.current_lang == "беларуская":
            self.load_language("by")
        elif self.current_lang == "Türkçe":
            self.load_language("tr")
        elif self.current_lang == "Татар (кириллица)":
            self.load_language("ta")
        elif self.current_lang == "हिंदी":  # hindi
            self.load_language("in")
        elif self.current_lang == "한국인":  # korean
            self.load_language("kr")
        elif self.current_lang == "ελληνικά":  # greek
            self.load_language("gr")
        elif self.current_lang == "عربي":  # arabic
            self.load_language("sa")
        elif self.current_lang == "Кыргызча":
            self.load_language("kg")
        elif self.current_lang == "नेवा":  # Newari
            self.load_language("ne")
        elif self.current_lang == "ʻŌlelo Hawaiʻi":  # hawai
            self.load_language("ha")
        elif self.current_lang == "Pilipino":
            self.load_language("ph")
        elif self.current_lang == "Nederlands":
            self.load_language("nl")
        elif self.current_lang == "norsk":
            self.load_language("no")
        elif self.current_lang == "հայ":  # Armenian
            self.load_language("am")
        elif self.current_lang == "Română":
            self.load_language("ro")
        elif self.current_lang == "Tiếng Việt":  # Vietnam
            self.load_language("vn")
        elif self.current_lang == "hrvatski":
            self.load_language("hr")
        self.setupText()
        self.setupTooltip()
        self.update_playlist_menu()
        self.refresh_tracks_display()

    def append_console(self, text):
        self.console_buffer.append(text)
        if self.console:
            self.console.moveCursor(self.console.textCursor().End)
            self.console.insertPlainText(text)
            self.console.ensureCursorVisible()

    def append_console_error(self, text):
        self.console_buffer.append(text)
        if self.console:
            self.console.moveCursor(self.console.textCursor().End)
            self.console.insertPlainText(text)
            self.console.ensureCursorVisible()

    def append_console_in(self, text):
        self.console_buffer.append(text)
        if self.console:
            self.console.moveCursor(self.console.textCursor().End)
            self.console.insertPlainText(text)
            self.console.ensureCursorVisible()

    def update_playlist_menu(self):
        self.Tracks_frame.setUpdatesEnabled(False)

        while self.playlist_layout.count():
            item = self.playlist_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        for name in self.playlists.keys():
            is_active = (name == self.current_playlist_name)
            pl_frame = QtWidgets.QFrame()
            pl_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {"#1f538d" if is_active else "#323242"};
                    border-radius: 5px;
                }}
            """)
            pl_frame.setFixedHeight(30)
            pl_frame.setFixedWidth(179)

            frame_layout = QtWidgets.QHBoxLayout(pl_frame)
            frame_layout.setContentsMargins(0, 0, 10, 0)
            frame_layout.setSpacing(2)

            btn = QtWidgets.QPushButton(name)
            btn.setStyleSheet("QPushButton{\n"
                            "    border-radius: 5px;\n"
                            "    background-color: transparent;\n"
                            "    color: white;\n"
                            "    text-align: left;\n"
                            "    padding: 10px;"  
                            "}\n"
                            "QPushButton:hover {\n"
                            "    background-color: transparent;\n"
                            "}\n"
                            "QToolTip {\n"
                            "    background-color: #222;\n"
                            "    color: white;\n"
                            "    border: 1px solid #444;\n"
                            "    padding: 4px;\n"
                            "    border-radius: 6px;\n"
                            "}"
                              )
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            btn.setToolTip(self.playlist_select_tooltip)
            btn.setFixedHeight(30)
            btn.setFont(self.main_font)
            btn.clicked.connect(
                lambda checked, n=name: self.select_playlist(n)
            )

            frame_layout.addWidget(btn)
            rename_btn = QtWidgets.QPushButton()
            rename_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/pen.png")))
            rename_btn.setFixedWidth(30)
            rename_btn.setIconSize(QtCore.QSize(20, 20))
            rename_btn.setStyleSheet("QPushButton{\n"
                            "    border-radius: 5px;\n"
                            "    background-color: transparent;\n"
                            "    color: white;\n"
                            "}\n"
                            "QPushButton:hover {\n"
                            "    background-color: #444452;\n"
                            "}\n"
                            "QToolTip {\n"
                            "    background-color: #222;\n"
                            "    color: white;\n"
                            "    border: 1px solid #444;\n"
                            "    padding: 4px;\n"
                            "    border-radius: 6px;\n"
                            "}"
                                     )
            rename_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            rename_btn.setFixedHeight(30)
            rename_btn.setToolTip(self.rename_tooltip)
            rename_btn.clicked.connect(
                lambda checked, n=name: self.rename_playlist_dialog(n)
            )

            frame_layout.addWidget(rename_btn)
            self.playlist_layout.addWidget(pl_frame)
        self.playlist_layout.addStretch()

    def refresh_tracks_display(self):
        self.Tracks_frame.setUpdatesEnabled(False)
        self.tracks_layout.setEnabled(False)

        while self.tracks_layout.count():
            item = self.tracks_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        playlist = self.playlists.get(self.current_playlist_name, [])
        self.tracks_layout.setEnabled(True)

        if not playlist:
            track_row = QtWidgets.QFrame()
            track_row.setStyleSheet(f"""
                QFrame {{
                    background-color: transparent;
                    border-radius: 5px;
                }}
            """)
            track_row.setFixedHeight(30)

            row_layout = QtWidgets.QHBoxLayout(track_row)
            row_layout.setContentsMargins(10, 0, 10, 0)

            label = QtWidgets.QLabel(self.nothing_to_display)
            label.setFont(QtGui.QFont("Arial", 16))
            label.setStyleSheet("color: white;")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setFont(self.main_font)
            row_layout.addWidget(label)
            self.tracks_layout.addWidget(track_row)
            self.Tracks_frame.setUpdatesEnabled(True)
            self.Tracks_frame.viewport().update()
            return

        for index, path in enumerate(playlist):
            print("for")
            is_active = (path == self.current_track_path)

            track_row = QtWidgets.QFrame()
            track_row.setAcceptDrops(True)
            track_row.setObjectName("track_row")

            def dragEnterEvent(event, row=track_row):
                if event.mimeData().hasText():
                    event.acceptProposedAction()

            def dropEvent(event, target_path=path):
                source_path = event.mimeData().text()

                if source_path == target_path:
                    return

                playlist = self.playlists[self.current_playlist_name]

                if build_os == "Darwin":
                    source_path = f"/Users/{username}/Afory/downloads/{source_path}"
                else:
                    source_path = f"C:/Users/{username}/Afory/downloads/{source_path}"

                old_index = playlist.index(source_path)
                new_index = playlist.index(target_path)

                track = playlist.pop(old_index)
                playlist.insert(new_index, track)

                self.save_data()
                self.refresh_tracks_display()

                event.acceptProposedAction()

            track_row.dragEnterEvent = dragEnterEvent
            track_row.dropEvent = dropEvent
            track_row.setFixedHeight(30)
            track_row.setStyleSheet(f"""QFrame {{background-color:{"#1b4f87" if is_active else "#2b2f45"};
                           border-radius: 5px;
                           }}""")

            row_layout = QtWidgets.QHBoxLayout(track_row)
            row_layout.setContentsMargins(10, 0, 10, 0)

            btn = QtWidgets.QPushButton(f"{index + 1}) {os.path.basename(path)}")
            btn.setObjectName("btn")
            btn.setToolTip(self.select_track_tooltip)
            btn.setFixedHeight(30)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            btn.setFont(self.main_font)
            btn.clicked.connect(
                lambda checked, p=path: self.set_active_track(p)
            )

            row_layout.addWidget(btn)

            url = self.links.get(path)
            if url:
                link_btn = QtWidgets.QPushButton()
                link_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/link.png")))
                link_btn.setFixedWidth(30)
                link_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                link_btn.setObjectName("link_btn")
                link_btn.setToolTip(self.link_tooltip)
                link_btn.setFixedHeight(30)
                link_btn.clicked.connect(
                    lambda checked, u=url: self.open_info_window(u)
                )

                row_layout.addWidget(link_btn)

            del_btn = QtWidgets.QPushButton()
            del_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/bin.png")))
            del_btn.setIconSize(QtCore.QSize(20, 20))
            del_btn.setFixedWidth(30)
            del_btn.setFixedHeight(30)
            del_btn.setObjectName("del_btn")
            del_btn.setToolTip(self.delete_track_tooltip)
            del_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            del_btn.clicked.connect(
                lambda checked, p=path: self.delete_current_track(p)
            )

            row_layout.addWidget(del_btn)

            ren_btn = QtWidgets.QPushButton()
            ren_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/pen.png")))
            ren_btn.setIconSize(QtCore.QSize(20, 20))
            ren_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            ren_btn.setFixedWidth(30)
            ren_btn.setFixedHeight(30)
            ren_btn.setObjectName("ren_btn")
            ren_btn.setToolTip(self.rename_tooltip)
            ren_btn.clicked.connect(
                lambda checked, p=path: self.rename_track(p)
            )

            row_layout.addWidget(ren_btn)

            move_btn = DragButton(path, self)
            move_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/menu.png")))
            move_btn.setIconSize(QtCore.QSize(20,20))
            move_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            move_btn.setFixedWidth(30)
            move_btn.setFixedHeight(30)
            move_btn.setObjectName("move_btn")
            move_btn.setToolTip(self.move_tooltip)
            row_layout.addWidget(move_btn)

            self.tracks_layout.addWidget(track_row)

        self.tracks_layout.addStretch()
        self.Tracks_frame.setUpdatesEnabled(True)
        self.Tracks_frame.viewport().update()

    def select_playlist(self, name):
        self.current_playlist_name = name
        self.label_current_playlist.setText(name)
        self.update_playlist_menu()
        self.refresh_tracks_display()

    def shuffle_current_playlist(self):
        self.stop_music()
        self.current_playlist = self.playlists[self.current_playlist_name]
        random.shuffle(self.current_playlist)
        self.refresh_tracks_display()
        self.current_track_path = None
        self.current_track_label.setText(self.track_not_selected)
        self.play_pause_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/play-button.png")))

    def rename_playlist_dialog(self, old_name):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setWindowTitle(self.renaming_text)
        dialog.setLabelText(self.new_name)

        dialog.setTextValue(old_name)

        true = dialog.exec_()
        if true:
            new_name = dialog.textValue()
        else:
            return

        if new_name and new_name != old_name:
            if new_name in self.playlists:
                QtWidgets.QMessageBox.information(self, f"{self.warning}", f"{self.playlist_already_exists}")
                return
            self.playlists[new_name] = self.playlists.pop(old_name)
            if self.current_playlist_name == old_name:
                self.current_playlist_name = new_name
            self.save_data()
            self.update_playlist_menu()

    def add_playlist(self):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setWindowTitle(self.new_playlist_nop)
        dialog.setLabelText(self.enter_playlist_name)

        true = dialog.exec_()
        if true:
            name = dialog.textValue()
        else:
            return

        if name:
            if name in self.playlists:
                QtWidgets.QMessageBox.information(self, f"{self.warning}", f"{self.playlist_already_exists}")
            else:
                self.playlists[name] = []
                self.save_data()
                self.update_playlist_menu()

    def delete_playlist(self):
        if self.current_playlist_name == "All":
            QtWidgets.QMessageBox.information(self, self.error, self.cant_delete_main)
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            self.deleting,
            f"{self.delete_playlist_t} '{self.current_playlist_name}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            del self.playlists[self.current_playlist_name]
            self.current_playlist_name = "All"
            self.save_data()
            self.update_playlist_menu()
            self.select_playlist("All")

    def open_info_window(self, url):
        self.info_window = InfoWindow(
            url=url,
            track_url_t=self.track_url_t,
            source_url_t=self.source_url_t,
            open_in_browser_t=self.open_in_browser_t,
            copy_t=self.copy_t,
            copy_callback=self.copy_to_clipboard,
            parent=self
        )
        self.info_window.show()

    def copy_to_clipboard(self, text):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(text)

    def rename_track(self, old_path):
        if old_path == self.current_track_path:
            QtWidgets.QMessageBox.information(self, self.error, self.cant_rename_when_use)
            return

        old_name = os.path.basename(old_path)

        dialog = QtWidgets.QInputDialog(self)
        dialog.setWindowTitle(self.renaming_text)
        dialog.setLabelText(self.new_name)

        dialog.setTextValue(old_name)

        true = dialog.exec_()
        if true:
            new_name = dialog.textValue()
        else:
            return

        if new_name and new_name != old_name:
            if not new_name.lower().endswith(".mp3"):
                new_name += ".mp3"
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                os.rename(old_path, new_path)
                if old_path in self.links:
                    self.links[new_path] = self.links.pop(old_path)
                    self.save_links()
                for pl_name in self.playlists:
                    self.playlists[pl_name] = [
                        new_path if track == old_path else track
                        for track in self.playlists[pl_name]
                    ]

                self.current_track_path = new_path
                self.save_data()
                self.refresh_tracks_display()

            except OSError as e:
                QtWidgets.QMessageBox.information(self, f"{self.error}", f"Error while renaming: {e}")

    def set_active_track(self, path):
        if self.is_played or self.is_paused:
            self.stop_music()

            QtCore.QTimer.singleShot(
                100,
                lambda: self._continue_set_active_track(path)
            )

            return

        self._continue_set_active_track(path)

    def _continue_set_active_track(self, path):
        self.play_pause_btn.setIcon(
            QtGui.QIcon(
                resource_path("assets/icons/pause-button.png")
            )
        )
        self.current_track_path = path
        if not os.path.exists(path):
            self.current_track_path = None
            return
        try:
            audio = MP3(path)
            self.length = int(audio.info.length) * 1000
            self.seekbar.track_length_ms = self.length
            self.view_length = self.length // 1000
            self.current_track_name = os.path.basename(path)
            self.current_playlist = self.playlists.get(
                self.current_playlist_name,
                []
            )
            self.current_index = self.current_playlist.index(
                self.current_track_path
            )
            self.current_track_label.setText(
                self.current_track_name
            )
        except Exception as e:
            print(e)
            return
        self.play_music()
        self.refresh_tracks_display()

    def toggle_play_pause(self):
        if self.current_track_path:
            if pygame.mixer.music.get_busy() and not self.is_paused:
                self.play_pause_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/play-button.png")))
                self.play_pause_btn.setIconSize(QtCore.QSize(30, 30))
                self.pause_music()
            else:
                self.play_pause_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/pause-button.png")))
                self.play_pause_btn.setIconSize(QtCore.QSize(30, 30))
                self.play_music()

    def add_local_file(self):
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Select mp3",
            "",
            "MP3 Files (*.mp3);;All Files (*)"
        )
        if paths:
            for p in paths:
                if p.lower().endswith(".mp3"):
                    self.playlists[self.current_playlist_name].append(p)
            self.save_data()
            self.refresh_tracks_display()

    def delete_current_track(self, path):
        if path == self.current_track_path:
            QtWidgets.QMessageBox.information(self, self.error, self.cant_delete_when_use)
            return
        current_track = os.path.basename(path)
        if not path in self.playlists[self.current_playlist_name]:
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            self.deleting,
            f"{self.are_you_sure_delete_track} '{current_track}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            try:
                self.playlists[self.current_playlist_name].remove(path)
                os.remove(path)
                self.current_track_path = None
                self.save_data()
                self.refresh_tracks_display()
                self.current_track_label.setText(self.track_deleted)
                QtCore.QTimer.singleShot(1500, lambda: self.current_track_label.setText(self.track_not_selected))

            except Exception as e:
                QtWidgets.QMessageBox.information(self, "Error", f"ERROR: {e}")

    def set_previous(self):
        if not self.current_playlist: return
        self.next_track = self.current_playlist[self.current_index - 1]
        self.set_active_track(self.next_track)
        self.play_music()

    def set_next(self):
        if not self.current_playlist: return
        self.next_track = self.current_playlist[self.current_index + 1]
        self.set_active_track(self.next_track)
        self.play_music()

    def set_track_loop(self):
        if not self.current_track_path: return
        self.loop = True
        self.repeat_btn.clicked.connect(self.del_track_loop)
        self.repeat_btn.setText(f" {self.dont_repeat}")

    def del_track_loop(self):
        self.loop = False
        self.is_repeat = False
        self.repeat_btn.clicked.connect(self.set_track_loop)
        self.repeat_btn.setText(f" {self.loop_text}")

    def play_music(self):
        if not self.is_paused:
            if self.current_track_path:
                pygame.mixer.music.load(self.current_track_path)
                pygame.mixer.music.play()
                self.is_played = True
                self.is_stopped = False
        elif self.is_paused:
            self.is_played = True
            self.is_stopped = False
            pygame.mixer.music.unpause()
            self.is_paused = False

    def start_loop(self):
            self.current_length = pygame.mixer.music.get_pos() + self.current_music_num
            self.current_view_length = self.current_length // 1000
            self.seekbar.setValue(
                int(self.current_length / self.length * 1000)
            )

            if self.is_stopped:
                self.is_played = False
            elif self.is_paused:
                self.current_track_label_2.setText(f"{self.playback_on_pause} {int(self.current_view_length) // 60:02d}:{int(self.current_view_length) % 60:02d} / {self.view_length // 60:02d}:{self.view_length % 60:02d}")
            elif not pygame.mixer.music.get_busy():
                self.current_track_label_2.setText(f"{self.playback} {int(self.current_view_length) // 60:02d}:{int(self.current_view_length) % 60:02d} / {self.view_length // 60:02d}:{self.view_length % 60:02d}")
                print("next play")
                self.play_next_track()
            elif not self.current_length == self.length:
                self.current_track_label_2.setText(f"{self.playback} {int(self.current_view_length) // 60:02d}:{int(self.current_view_length) % 60:02d} / {self.view_length // 60:02d}:{self.view_length % 60:02d}")

    def set_music_to_current_slide_pos(self, value):
        if self.is_stopped:
            return
        elif self.is_paused:
            return
        else:
            self.one_unit_length = (self.length / 100)
            self.current_music_num = value / 1000 * self.length
            pygame.mixer.music.play(start=self.current_music_num // 1000)

    def play_next_track(self):
            if not self.current_playlist:
                return
            if self.loop:
                next_track = self.current_playlist[self.current_index]
                self.current_music_num = 0
                self.current_length = 0
                self.set_active_track(next_track)
                return

            max_index = len(self.current_playlist)

            if self.current_index + 1 >= max_index:
                self.end_playlist_ui()
            else:
                next_track = self.current_playlist[self.current_index + 1]
                self.current_music_num = 0
                self.current_length = 0
                self.set_active_track(next_track)

    def end_playlist_ui(self):
        self.current_track_label_2.setText(self.playlist_ended)
        self.current_track_label.setText(self.track_not_selected)
        self.play_pause_btn.setIcon(QtGui.QIcon(resource_path("assets/icons/play-button.png")))
        self.is_stopped = True
        self.current_music_num = 0
        self.current_length = 0
        self.current_track_path = None
        self.refresh_tracks_display()

    def stop_music(self):
        self.is_stopped = True
        pygame.mixer.music.stop()
        self.current_track_label_2.setText(self.playback_stopped)
        self.current_length = 0
        self.current_music_num = 0
        print("stop")

    def pause_music(self):
        pygame.mixer.music.pause()
        self.is_paused = True
        print("pause")

    def download_youtube(self):
        dialog = QtWidgets.QInputDialog(self)
        dialog.setWindowTitle("Web")
        dialog.setLabelText(self.supported_links)

        if not dialog.exec_():
            return

        url = dialog.textValue()
        self.current_track_label.setText(f"{self.track_loading} 0 %")
        self.download_youtube_main(url)

    def download_youtube_main(self, url):
        print("download_main")

        if not self.build_ydl_opts():
            QtWidgets.QMessageBox.information(self, "Warning", "WARNING: ydlopts.txt file not found.\n"
                                                               "If you deleted this file by accident, please download it here:\n"
                                                               "MacOS: https://github.com/ThirdTusa/Afory/blob/main/ydlopts.txt\n"
                                                               "Windows: https://github.com/ThirdTusa/Afory/blob/main/ydlopts_win.txt\n"
                                                               "And store it exactly here: \n"
                                                               f"MacOS: /Applications/Afory.app/Contents/MacOS/assets/ydlopts.txt\n"
                                                               f"Windows: C:/Users/{username}/Appdata/local/AforyApp/assets/ydlopts_win.txt\n")

            self.current_track_label.setText(self.track_not_selected)
            return

        opts = self.build_ydl_opts()

        self.current_track_label.setText(f"{self.track_loading} 0 %")

        self.download_manager.add(
            url,
            opts,
            self.track_loading,
            callbacks={
                "finished": self.on_download_finished,
                "error": self.on_download_error,
                "log": self.on_download_log
            }
        )

    def on_download_error(self, err):
        QtWidgets.QMessageBox.critical(self, "Download error", err)
        self.current_track_label.setText(self.track_not_selected)

    def on_download_log(self, msg):
        self.current_track_label.setText(msg)

    def build_ydl_opts(self):
        if not os.path.exists(resource_path("assets/ydlopts.txt")) and build_os == "Darwin":
            return None
        if not os.path.exists(resource_path("assets/ydlopts_win.txt")) and not build_os == "Darwin":
            return None
        if build_os == "Darwin":
            file = resource_path("assets/ydlopts.txt")
        else:
            file = resource_path("assets/ydlopts_win.txt")

        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        config = eval(content)
        return config

    def on_download_finished(self, final_mp3, url):
        self.playlists[self.current_playlist_name].append(final_mp3)
        self.links[final_mp3] = url

        self.save_data()
        self.save_links()
        self.refresh_tracks_display()

        self.current_track_label.setText(self.track_not_selected)

    def on_progress(self, percent):
        self.current_track_label.setText(f"{self.track_loading} {percent} %")

    def settings_open(self):
        self.settings_win = QtWidgets.QDialog(self)
        self.settings_win.setWindowTitle(self.settings_op)
        self.settings_win.setObjectName("Settings")
        self.settings_win.resize(450, 560)
        self.settings_win.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.settings_win.setModal(True)
        self.settings_win.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowCloseButtonHint |
            QtCore.Qt.WindowMinimizeButtonHint
        )
        self.settings_win.setStyleSheet("QPushButton{\n"
                                "    border-radius: 15px;\n"
                                "    background-color: #32323c;\n"
                                "    color: white;\n"
                                "}\n"
                                "QPushButton:hover {\n"
                                "    background-color: #444452;\n"
                                "}\n"
                                "QToolTip {\n"
                                "    background-color: #222;\n"
                                "    color: white;\n"
                                "    border: 1px solid #444;\n"
                                "    padding: 4px;\n"
                                "    border-radius: 6px;\n"
                                "}"
                                "QDialog {"
                                "    background-color: #1d1f28"
                                "}"
                                            )
        self.setup_settings_ui()
        self.settings_win.show()

    def setup_settings_ui(self):
        self.theme_menu = QtWidgets.QComboBox(self.settings_win)
        self.theme_menu.setGeometry(QtCore.QRect(130, 40, 181, 31))
        self.theme_menu.setStyleSheet("")
        self.theme_menu.setCurrentText("")
        self.theme_menu.setObjectName("theme_menu")
        self.theme_menu.addItems(QtGui.QFontDatabase().families())
        self.theme_menu.setCurrentText(self.settings.get("font"))
        self.theme_menu.currentTextChanged.connect(self.change_font)
        self.theme_menu.setView(QtWidgets.QListView())
        self.theme_menu.view().setSpacing(6)
        self.theme_menu.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.theme_menu.setStyleSheet("""QComboBox {
    border: 2px solid #3d3d3d;
    border-radius: 6px;
    padding: 5px 10px;
    min-width: 6em;
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: "Segoe UI", sans-serif;
    font-size: 14px;
}

QComboBox:hover {
    border: 2px solid #007acc;
    background-color: #333333;
}

QComboBox:on { 
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
    border: 2px solid #007acc;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left-width: 0px;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QComboBox::down-arrow {
    image: none;
    color: #aaaaaa;
    font-weight: bold;
    font-size: 10px;
    content: "▼"; 
}

QComboBox::down-arrow:on {
    color: #007acc;
}

QComboBox QAbstractItemView {
    border: 2px solid #007acc;
    border-top-width: 0px;
    border-bottom-left-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: #2b2b2b;
    color: #ffffff;
    selection-background-color: #007acc;
    selection-color: #ffffff;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 8px 10px;
    background-color: transparent;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #3d3d3d;
    color: #ffffff;
    
QComboBox QAbstractItemView::item:selected {
    background-color: #007acc;
    color: #ffffff;
}
        """)

        self.theme_label = QtWidgets.QLabel(self.settings_win)
        self.theme_label.setGeometry(QtCore.QRect(10, 10, 421, 20))
        self.theme_label.setStyleSheet("color: white")
        self.theme_label.setAlignment(QtCore.Qt.AlignCenter)
        self.theme_label.setObjectName("theme_label")
        self.theme_label.setFont(self.main_font)

        self.open_downloads_btn = QtWidgets.QPushButton(self.settings_win)
        self.open_downloads_btn.setGeometry(QtCore.QRect(120, 85, 201, 32))
        self.open_downloads_btn.setObjectName("open_downloads_btn")
        self.open_downloads_btn.setFont(self.main_font)
        self.open_downloads_btn.setStyleSheet("""
                                border-color: #7476a0;
                                color: white;
                                border: 2px solid #7476a0;""")

        self.open_stdout_btn = QtWidgets.QPushButton(self.settings_win)
        self.open_stdout_btn.setGeometry(QtCore.QRect(120, 125, 201, 32))
        self.open_stdout_btn.setObjectName("open_stdout_btn")
        self.open_stdout_btn.setFont(self.main_font)
        self.open_stdout_btn.setStyleSheet("""
                                border-color: #7476a0;
                                color: white;
                                border: 2px solid #7476a0;""")
        self.open_keybinds_btn = QtWidgets.QPushButton(self.settings_win)
        self.open_keybinds_btn.setGeometry(QtCore.QRect(120, 165, 201, 32))
        self.open_keybinds_btn.setObjectName("open_keybinds_btn")
        self.open_keybinds_btn.setFont(self.main_font)
        self.open_keybinds_btn.setStyleSheet("""
                                border-color: #7476a0;
                                color: white;
                                border: 2px solid #7476a0;""")
        self.tutorial_btn = QtWidgets.QPushButton(self.settings_win)
        self.tutorial_btn.setGeometry(QtCore.QRect(120, 205, 201, 32))
        self.tutorial_btn.setObjectName("tutorial_btn")
        self.tutorial_btn.setFont(self.main_font)
        self.tutorial_btn.setStyleSheet("""
                                border-color: #7476a0;
                                color: white;
                                border: 2px solid #7476a0;""")
        self.language_label = QtWidgets.QLabel(self.settings_win)
        self.language_label.setGeometry(QtCore.QRect(10, 245, 421, 20))
        self.language_label.setStyleSheet("color: white")
        self.language_label.setAlignment(QtCore.Qt.AlignCenter)
        self.language_label.setObjectName("language_label")
        self.language_label.setFont(self.main_font)
        self.language_label_icon = QtWidgets.QLabel(self.settings_win)
        self.language_label_icon.setGeometry(QtCore.QRect(90, 277, 51, 31))
        self.language_label_icon.setStyleSheet("color: white;")
        pixmap = QtGui.QPixmap(resource_path("assets/icons/language.png"))
        pixmap = pixmap.scaled(
            25,
            25,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.language_label_icon.setPixmap(pixmap)
        self.lang_menu = QtWidgets.QComboBox(self.settings_win)
        self.lang_menu.setGeometry(QtCore.QRect(130, 275, 181, 31))
        self.lang_menu.setStyleSheet("")
        self.lang_menu.setCurrentText("")
        self.lang_menu.setObjectName("lang_menu")
        self.lang_menu.setView(QtWidgets.QListView())
        self.lang_menu.view().setSpacing(6)
        self.lang_menu.setStyleSheet("""QComboBox {
    border: 2px solid #3d3d3d;
    border-radius: 6px;
    padding: 5px 10px;
    min-width: 6em;
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: "Segoe UI", sans-serif;
    font-size: 14px;
}

QComboBox:hover {
    border: 2px solid #007acc;
    background-color: #333333;
}

QComboBox:on { 
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
    border: 2px solid #007acc;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left-width: 0px;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

QComboBox::down-arrow {
    image: none;
    color: #aaaaaa;
    font-weight: bold;
    font-size: 10px;
    content: "▼"; 
}

QComboBox::down-arrow:on {
    color: #007acc;
}

QComboBox QAbstractItemView {
    border: 2px solid #007acc;
    border-top-width: 0px;
    border-bottom-left-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: #2b2b2b;
    color: #ffffff;
    selection-background-color: #007acc;
    selection-color: #ffffff;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 8px 10px;
    background-color: transparent;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #3d3d3d;
    color: #ffffff;
    
QComboBox QAbstractItemView::item:selected {
    background-color: #007acc;
    color: #ffffff;
}
        """)
        self.lang_menu.addItems(["English", "Русский", "Deutsch", "ქართული", "español", "Українська", "Қазақ", "Polski", "Français", "日本語", "中國人", "Italiano", "Azərbaycan dili", "беларуская", "Türkçe", "Татар (кириллица)", "हिंदी", "한국인", "ελληνικά", "عربي", "Кыргызча", "नेवा", "ʻŌlelo Hawaiʻi", "Pilipino", "Nederlands", "norsk", "հայ", "Română", "Tiếng Việt", "hrvatski"])
        self.lang_menu.setCurrentText(self.settings.get("language"))
        self.lang_menu.currentTextChanged.connect(self.change_lang)
        self.dev_label = QtWidgets.QLabel(self.settings_win)
        self.dev_label.setGeometry(QtCore.QRect(10, 315, 421, 20))
        self.dev_label.setStyleSheet("color: white")
        self.dev_label.setAlignment(QtCore.Qt.AlignCenter)
        self.dev_label.setObjectName("dev_label")
        self.dev_label.setFont(self.main_font)
        self.mady_by_label = QtWidgets.QLabel(self.settings_win)
        self.mady_by_label.setGeometry(QtCore.QRect(10, 345, 421, 20))
        self.mady_by_label.setStyleSheet("color: white")
        self.mady_by_label.setAlignment(QtCore.Qt.AlignCenter)
        self.mady_by_label.setObjectName("mady_by_label")
        self.mady_by_label.setFont(self.main_font)
        self.github_btn = QtWidgets.QPushButton(self.settings_win)
        self.github_btn.setGeometry(QtCore.QRect(120, 375, 201, 32))
        self.github_btn.setObjectName("github_btn")
        self.github_btn.setFont(self.main_font)
        self.github_btn.setStyleSheet("""
                                border-color: #7476a0;
                                color: white;
                                border: 2px solid #7476a0;""")
        self.tiktok_btn = QtWidgets.QPushButton(self.settings_win)
        self.tiktok_btn.setGeometry(QtCore.QRect(120, 415, 201, 32))
        self.tiktok_btn.setObjectName("tiktok_btn")
        self.tiktok_btn.setFont(self.main_font)
        self.tiktok_btn.setStyleSheet("""
                                border-color: #7476a0;
                                color: white;
                                border: 2px solid #7476a0;""")
        self.version_label = QtWidgets.QLabel(self.settings_win)
        self.version_label.setGeometry(QtCore.QRect(10, 495, 421, 20))
        self.version_label.setStyleSheet("color: white")
        self.version_label.setAlignment(QtCore.Qt.AlignCenter)
        self.version_label.setObjectName("version_label")
        self.version_label.setFont(self.main_font)
        self.icon_creators_btn = QtWidgets.QPushButton(self.settings_win)
        self.icon_creators_btn.setGeometry(QtCore.QRect(120, 455, 201, 32))
        self.icon_creators_btn.setObjectName("icon_creators_btn")
        self.icon_creators_btn.setFont(self.main_font)
        self.icon_creators_btn.setStyleSheet("""
                                border-color: #7476a0;
                                color: white;
                                border: 2px solid #7476a0;""")
        QtCore.QMetaObject.connectSlotsByName(self.settings_win)
        self.open_downloads_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.open_keybinds_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.open_stdout_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.tutorial_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.github_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.tiktok_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.icon_creators_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.open_stdout_btn.clicked.connect(self.open_stdout_window)
        self.open_downloads_btn.clicked.connect(self.open_downloads_folder)
        self.open_keybinds_btn.clicked.connect(self.show_keybinds)
        self.tutorial_btn.clicked.connect(self.open_tutorial)
        self.github_btn.clicked.connect(self.open_github_dev1)
        self.tiktok_btn.clicked.connect(self.open_tt_dev1)
        self.icon_creators_btn.clicked.connect(self.open_icons_creator_window)
        self.setup_settings_text()

    def setup_settings_text(self):
        self.theme_label.setText(self.application_font)
        self.open_downloads_btn.setText(self.open_download_folder)
        self.open_stdout_btn.setText(self.open_console_t)
        self.open_keybinds_btn.setText(self.see_keybinds_t)
        self.tutorial_btn.setText(self.tutorial)
        self.language_label.setText(self.lang)
        self.dev_label.setText(self.developerss)
        self.mady_by_label.setText("Made by Tuseloryy")
        self.github_btn.setText("Github")
        self.tiktok_btn.setText("Tiktok")
        self.version_label.setText("Version: 2026.6.1")
        self.icon_creators_btn.setText("Icon creators")

    def open_stdout_window(self):
        if self.console:
            QtWidgets.QMessageBox.information(None, self.error, self.console_already_opened)
            return
        self.console_win = QtWidgets.QDialog(self.settings_win)
        self.console_win.setWindowTitle(self.console_t)
        self.console_win.resize(500, 500)

        layout = QtWidgets.QVBoxLayout(self.console_win)

        self.console = QtWidgets.QTextEdit()
        self.console.setReadOnly(True)
        self.console.setGeometry(QtCore.QRect(0, 0, 500, 500))
        self.console.setStyleSheet("""
        color: white;
        background-color: black;
        """)

        layout.addWidget(self.console)

        self.console.setPlainText("".join(self.console_buffer))
        self.console.moveCursor(QtGui.QTextCursor.End)
        self.console_win.closeEvent = self.console_closed

        self.console_win.show()

    def console_closed(self, event):
        self.console = None
        event.accept()

    def open_downloads_folder(self):
        if build_os == "Darwin":
            subprocess.run(["open", f"/Users/{username}/Afory"])
        else:
            os.startfile(f"C:/Users/{username}/Afory")

    def change_font(self, new_font):
        self.settings_win.destroy()
        self.settings["font"] = new_font
        self.save_settings()
        self.main_font.setFamily(new_font)
        self.apply_font()
        self.settings_open()

    def change_lang(self, new_lang):
        self.settings_win.destroy()
        self.settings["language"] = new_lang
        self.save_settings()
        self.apply_lang()
        self.settings_open()

    def apply_font(self):
        self.update_playlist_menu()
        self.add_playlist_btn.setFont(self.main_font)
        self.delete_playlist_btn.setFont(self.main_font)
        self.settings_btn.setFont(self.main_font)
        self.add_mp3_btn.setFont(self.main_font)
        self.web_download_btn.setFont(self.main_font)
        self.shuffle_btn.setFont(self.main_font)
        self.repeat_btn.setFont(self.main_font)
        self.volume_percentage.setFont(self.main_font)
        self.current_track_label.setFont(self.main_font)
        self.current_track_label_2.setFont(self.main_font)
        self.refresh_tracks_display()

    def show_keybinds(self):
        QtWidgets.QMessageBox.information(self, f"{self.keybinds_t}", f"{self.first_keybind_t}\n"
                                   f"{self.second_keybind_t}\n"
                                   f"{self.third_keybind_t}\n"
                                   f"{self.works_even_not_in_app_t}\n"
                                   f"{self.keybinds_note}")

    def open_tutorial(self):
        QtWidgets.QMessageBox.information(self, f"{self.error}", f"{self.tutorial_does_not_exists}")

    def open_github_dev1(self):
        webbrowser.open("https://github.com/ThirdTusa")

    def open_tt_dev1(self):
        webbrowser.open("https://www.tiktok.com/@tuselmark")

    def open_icons_creator_window(self):
        QtWidgets.QMessageBox.information(self, "Icon creators", "Pencil icon created by alkhalifi design - Flaticon\n"
                                "Link icon, trash icon, settings icon, language icon and plus icon created by Freepik - Flaticon\n"
                                "Play button icon created by NajmunNahar - Flaticon\n"
                                "Pause button icon created by Slidicon - Flaticon\n"
                                "Arrow up icon and down icon created by Dave Gandy - Flaticon\n"
                                "Previous icon created by abdul allib - Flaticon\n"
                                "Next icon created by Ferdinand - Flaticon\n"
                                "Swap icon created by Tanah Basah - Flaticon\n"
                                "Three lines icon created by See Icons - Flaticon\n"
                                "Web planet icon created by Shah Rukh Qureshi - Flaticon\n"
                                "Repeat button icon created by revolutionizzed_1 - Flaticon")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    build_os = platform.system().strip()

    try:
        username = getpass.getuser()
    except Exception as e:
        dialog = QtWidgets.QInputDialog(None)
        dialog.setWindowTitle("Warning")
        dialog.setLabelText(f"Program tried to get your username, but failed with error:\n'{e}'\n"
                                     f"We need your username to create folders and store your playlists and tracks.\n"
                                     f"Please, provide username below\n"
                                     f"(you can see your username by typing whoami in terminal)")
        if dialog.exec_():
            username = dialog.textValue()
        else:
            quit()

    try:
        if build_os == "Darwin":
            if os.path.exists(f"/Users/{username}/Afory"):
                print("Afory exists")
            else:
                os.mkdir(f"/Users/{username}/Afory")
                print("Afory created")

            if os.path.exists(f"/Users/{username}/Afory/downloads"):
                print("downloads exists")
            else:
                os.mkdir(f"/Users/{username}/Afory/downloads")
                print("downloads created")

            if os.path.exists(f"/Users/{username}/Afory/warning.txt"):
                print("warning.txt exists")
            elif not os.path.exists(f"/Users/{username}/Afory/warning.txt"):
                warning_txt = os.path.join(f"/Users/{username}/Afory", "warning.txt")
                with open(warning_txt, "w", encoding="utf-8") as f:
                    f.write("WARNING:\n This folder is used by Afory.\n If you try to delete or add files in this folder, you can lose your created playlists and tracks.\n Please, use this folder correctly.")
                print("warning.txt created")

        else:
            if os.path.exists(f"C:/Users/{username}/Afory"):
                print("Afory exists")
            else:
                os.mkdir(f"C:/Users/{username}/Afory")
                print("Afory created")

            if os.path.exists(f"C:/Users/{username}/Afory/downloads"):
                print("downloads exists")
            else:
                os.mkdir(f"C:/Users/{username}/Afory/downloads")
                print("downloads created")

            if os.path.exists(f"C:/Users/{username}/Afory/warning.txt"):
                print("warning.txt exists")
            elif not os.path.exists(f"C:/Users/{username}/Afory/warning.txt"):
                warning_txt = os.path.join(f"C:/Users/{username}/Afory", "warning.txt")
                with open(warning_txt, "w", encoding="utf-8") as f:
                    f.write(
                        "WARNING:\n This folder is used by Afory.\n If you try to delete or add files in this folder, you can lose your created playlists and tracks.\n Please, use this folder correctly.")
                print("warning.txt created")

    except Exception as e:
        QtWidgets.QMessageBox.information(None, "Error", f"Program got error while creating folders: {e} \n"
                           f"Please, fix this error or create folders by yourself.")
        quit()

    window = Mainwindow()
    window.show()
    sys.exit(app.exec_())


# Made by Tuseloryy
# My social: https://tuseloryy.card.co
# Python 3.12
# SOURCE CODE:

import sys
import io
console_out = io.StringIO()
sys.stdout = console_out
import tkinter as tk
import customtkinter as ctk
import pygame
import yt_dlp
import os
import threading
import json
import getpass
import subprocess
import webbrowser
import time
import random
from mutagen.mp3 import MP3
from tkinter import filedialog, messagebox, simpledialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def resource_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, filename)

class SliderTooltip:
    def __init__(self, slider):
        self.slider = slider
        self.tip_window = None

    def show_tip(self, text, x, y):
        if self.tip_window:
            return
        self.tip_window = tk.Toplevel(self.slider)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.resizable(width=False, height=False)
        self.tip_window.attributes("-alpha", 0.8)
        self.tip_window.attributes("-topmost", True)

        self.container = ctk.CTkFrame(self.tip_window, corner_radius=8, fg_color="#2B2B2B", border_width=1, border_color="#3F3F3F")
        self.container.pack()

        self.label = ctk.CTkLabel(self.container, text=text, font=("Arial", 13), text_color="#FFFFFF", padx=8, pady=2)
        self.label.pack()

        self.update_pos(x, y)

    def update_pos(self, x, y):
        if self.tip_window:
            self.tip_window.update_idletasks()
            width = self.tip_window.winfo_width()
            self.tip_window.geometry(f"+{int(x - width / 2)}+{y - 40}")

    def hide_tip(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class Main(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Afory")
        self.geometry("1150x680")
        self.resizable(False, False)

        pygame.mixer.init()

        self.save_file = f"/Users/{username}/Afory/playlists_data.json"
        self.settings_file = f"/Users/{username}/Afory/settings_data.json"
        self.link_file = f"/Users/{username}/Afory/links_data.json"
        self.links = self.load_links()
        self.old_content = ""
        self.bind("<space>", self.toggle_play_pause)
        self.playlists = self.load_data()
        self.settings = self.load_settings()
        self.current_playlist_name = "All"
        ctk.set_appearance_mode(self.settings.get("theme", "Dark"))
        self.tip_win_on = self.settings.get("tooltip", True)
        self.current_track_path = None
        self.length = 1
        self.current_music_num = 0
        self.current_view_length = 0
        self.is_dragging = False
        self.run = True
        self.loop = False
        self.stop_event = threading.Event()
        self.is_played = False
        self.is_stopped = True
        self.is_repeat = False
        self.start_update = True
        self.current_length = (pygame.mixer.music.get_pos() // 1000)
        self.value = 0
        pygame.mixer.music.set_volume(self.settings.get("volume", 0.7))

        self.playlists_t = "Playlists"
        self.new_playlist = "+ New Playlist"
        self.del_playlist = "🗑 Delete playlist"
        self.select_playlist_t = "Select playlist"
        self.add_mp3 = "Add MP3"
        self.download_from_YT = "Download from YT"
        self.del_from_list = "Delete track"
        self.track_not_selected = "Track not selected"
        self.settings_t = "⚙️ Settings"
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
        self.volum = "🔊 Volume"
        self.open_download_folder = "Open downloads folder"
        self.tutorial = "Tutorial"
        self.developerss = "Developers:"
        self.tutorial_does_not_exists = "Tutorial does not currently exist."
        self.supported_links = "Supported Links: YT, Newgrounds, Soundcloud"
        self.track_loading = "⏳ Track loading..."
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

        self.save_links()
        self.setup_ui()
        self.apply_lang()
        self.select_playlist(self.current_playlist_name)

    def setup_ui(self):
        self.is_paused = False

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="transparent")
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.lbl_logo = ctk.CTkLabel(self.sidebar, text=self.playlists_t, font=("Arial", 22, "bold"))
        self.lbl_logo.pack(pady=20)

        self.btn_new_playlist = ctk.CTkButton(self.sidebar, text=self.new_playlist, command=self.add_playlist)
        self.btn_new_playlist.pack(padx=10, pady=5)

        self.btn_del_playlist = ctk.CTkButton(self.sidebar, text=self.del_playlist,
                                              fg_color="#721c24", hover_color="#af233a",
                                              command=self.delete_playlist)
        self.btn_del_playlist.pack(padx=10, pady=5)

        self.playlist_frame = ctk.CTkScrollableFrame(self.sidebar, label_text=self.playlists_t)
        self.playlist_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.update_playlist_menu()

        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.lbl_pl_name = ctk.CTkLabel(self.main_view, text=self.select_playlist_t, font=("Arial", 26, "bold"))
        self.lbl_pl_name.pack(pady=10)

        self.content_box = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.content_box.pack(fill="both", expand=True)

        self.tracks_listbox = ctk.CTkScrollableFrame(self.content_box, height=300)
        self.tracks_listbox.pack(padx=10, expand=True, fill="x", side="left")

        self.reorder_btns = ctk.CTkFrame(self.content_box, width=40, fg_color="transparent")
        self.reorder_btns.pack(side="right")

        self.btn_move_up = ctk.CTkButton(self.reorder_btns, text="⬆", font=("Arial", 16, "bold"), width=45, height=45, command=lambda: self.move_track(-1))
        self.btn_move_up.pack(pady=5)

        self.btn_move_down = ctk.CTkButton(self.reorder_btns, text="⬇", font=("Arial", 16, "bold"), width=45, height=45, command=lambda: self.move_track(+1))
        self.btn_move_down.pack(pady=5)

        self.toolbar = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.toolbar.pack(pady=10)

        self.btn_add_local = ctk.CTkButton(self.toolbar, text=self.add_mp3, command=self.add_local_file)
        self.btn_add_local.pack(padx=2, side="left")

        self.btn_add_yt = ctk.CTkButton(self.toolbar, text=self.download_from_YT, command=self.download_youtube,
                                        fg_color="#cc0000")
        self.btn_add_yt.pack(padx=2, side="left")

        self.btn_shuffle = ctk.CTkButton(self.toolbar, text=self.shuffle_text, command=self.shuffle_current_playlist)
        self.btn_shuffle.pack(padx=2, side="left")

        self.btn_set_loop = ctk.CTkButton(self.toolbar, text=self.loop_text, command=self.set_track_loop)
        self.btn_set_loop.pack(padx=2, side="left")

        self.player_controls = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.player_controls.pack(fill="x", pady=10, side="bottom")

        self.info_label = ctk.CTkLabel(self.player_controls, text=self.track_not_selected, font=("Arial", 17))
        self.info_label.pack(pady=5)

        self.playback_btns = ctk.CTkFrame(self.player_controls, fg_color="transparent")
        self.playback_btns.pack(pady=10)

        self.btn_previous = ctk.CTkButton(self.playback_btns, text="<<", font=("Arial", 16, "bold"), width=45, height=45, command=self.set_previous)
        self.btn_previous.grid(row=0, column=1, padx=10)

        self.btn_play = ctk.CTkButton(self.playback_btns, text="▶", font=("Arial", 16, "bold"),
                                      width=150, height=45, command=self.play_music)
        self.btn_play.grid(row=0, column=2, padx=10)

        self.btn_pause = ctk.CTkButton(self.playback_btns, text="▐▐", font=("Arial", 16, "bold"), fg_color="#444444", hover_color="#222222", width=150, height=45, state="disabled", command=self.pause_music)
        self.btn_pause.grid(row=0, column=3, padx=10)

        self.btn_stop = ctk.CTkButton(self.playback_btns, text="⬜", font=("Arial", 16, "bold"),
                                      fg_color="#444444", hover_color="#222222",
                                      width=150, height=45, command=self.stop_music, state="disabled")
        self.btn_stop.grid(row=0, column=4, padx=10)

        self.btn_next = ctk.CTkButton(self.playback_btns, text=">>", font=("Arial", 16, "bold"), width=45, height=45, command=self.set_next)
        self.btn_next.grid(row=0, column=5, padx=10)

        self.seekbar = ctk.CTkSlider(self.player_controls, from_=0, to=100, command=self.set_music_to_current_slide_pos)
        self.seekbar.pack(padx=20, fill="x", expand=True)
        self.seekbar.set(0)

        self.tooltip = SliderTooltip(self.seekbar)

        if self.settings.get("tooltip", True) == False:
            self.seekbar.unbind("<Motion>")
            self.seekbar.unbind("<Leave>")
        else:
            self.seekbar.bind("<Motion>", self.on_slider_hover)
            self.seekbar.bind("<Leave>", lambda e: self.tooltip.hide_tip())

        self.settings_btn = ctk.CTkButton(self.sidebar, text=self.settings_t, font=("Arial", 14), command=self.settings_open)
        self.settings_btn.pack(pady=10)

        self.status_bar = ctk.CTkLabel(self.player_controls, text=self.select_playlist_and_track, font=("Arial", 16))
        self.status_bar.pack()

        threading.Thread(target=self.start_loop, daemon=True).start()

    def update_console_output(self):
        new_content = console_out.getvalue()

        if new_content:
            self.console_textbox.configure(state="normal")
            self.console_textbox.delete("1.0", "end")
            self.console_textbox.insert("1.0", new_content)
            self.console_textbox.see("end")
            self.console_textbox.configure(state="disabled")
        self.after(1000, self.update_console_output)

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
        default_settings = {"volume": 0.7, "theme": "Dark", "language": "English", "tooltip": True}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)

                    if "theme" not in settings:
                        settings["theme"] = "Dark"
                    return settings
            except:
                return default_settings
        return default_settings

    def apply_lang(self):
        self.current_lang = self.settings.get("language")
        print(self.current_lang)
        if self.current_lang == "Русский":
            self.playlists_t = "Плейлисты"
            self.new_playlist = "+ Новый плейлист"
            self.del_playlist = "🗑 Удалить плейлист"
            self.select_playlist_t = "Выберете плейлист"
            self.add_mp3 = "Добавить MP3"
            self.download_from_YT = "Скачать из интернета"
            self.del_from_list = "Удалить трек"
            self.track_not_selected = "Трек не выбран"
            self.settings_t = "⚙️ Настройки"
            self.select_playlist_and_track = "Выберите плейлист и трек чтобы начать"
            self.new_playlist_nop = "Новый плейлист"
            self.enter_playlist_name = "Название плейлиста:"
            self.warning = "Внимание"
            self.playlist_already_exists = "Такой плейлист уже есть"
            self.error = "Ошибка"
            self.cant_delete_main = "Нельзя удалить основной список"
            self.deleting = "Удаление"
            self.delete_playlist_t = "Удалисть плейлист"
            self.file_not_found = "Файл не найден (возможно, удален с диска)"
            self.track_deleted = "Трек удален"
            self.file_no_longer_exists = "Файл больше не существует по указанному пути"
            self.select_track = "Выберете трек"
            self.playback = "Воспроизведение:"
            self.playback_on_pause = "Воспроизведение на паузе:"
            self.playlist_ended = "Плейлист кончился"
            self.playback_stopped = "Воспроизведение остановлено"
            self.settings_op = "Настройки"
            self.design_theme = "Тема оформления:"
            self.volum = "🔊 Громкость:"
            self.open_download_folder = "Открыть папку сохранений..."
            self.tutorial = "Справка"
            self.developerss = "Разработчики:"
            self.tutorial_does_not_exists = "Справка в данный момент не существует."
            self.supported_links = "Поддерживаемые ссылки: YouTube, Soundcloud, Newgrounds"
            self.track_loading = "⏳ Загрузка трека..."
            self.done = "✅  Готово"
            self.lang = "Язык:"
            self.click_stop_then_select = "Нажмите кнопку «Стоп», затем выберите новый трек для воспроизведения."
            self.shuffle_text = "Перемешать"
            self.stop_loading = "Остановить загрузку"
            self.loading_stopped = "Загрузка остановлена"
            self.loop_text = "Повторять"
            self.del_loop_then_select = "Выключите повтор, потом выберете другой трек"
            self.dont_repeat = "Не повторять"
            self.show_tooltip_text = "Показать подсказку ползунка"
            self.are_you_sure_delete_track = "Вы уверены что хотите удалить этот трек?"
            self.rename_text = "Переименновать"
            self.renaming_text = "Переименнование"
            self.new_name = "Новое имя:"
            self.track_url_t = "URL трека"
            self.source_url_t = "Источник (URL):"
            self.open_in_browser_t = "Окрыть в браузере"
            self.copy_t = "Скопировать"
            self.copied_t = "Скопировано!"
        elif self.current_lang == "English":
            self.playlists_t = "Playlists"
            self.new_playlist = "+ New Playlist"
            self.del_playlist = "🗑 Delete playlist"
            self.select_playlist_t = "Select playlist"
            self.add_mp3 = "Add MP3"
            self.download_from_YT = "Download from Web"
            self.del_from_list = "Delete track"
            self.track_not_selected = "Track not selected"
            self.settings_t = "⚙️ Settings"
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
            self.volum = "🔊 Volume:"
            self.open_download_folder = "Open downloads folder"
            self.tutorial = "Tutorial"
            self.developerss = "Developers:"
            self.tutorial_does_not_exists = "Tutorial does not currently exist."
            self.supported_links = "Supported Links: YT, Newgrounds, Soundcloud"
            self.track_loading = "⏳ Track loading..."
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
            self.rename_text = "Rename"
            self.renaming_text = "Renaming"
            self.new_name = "New name:"
            self.track_url_t = "Track URL"
            self.source_url_t = "Source (URL):"
            self.open_in_browser_t = "Open in Browser"
            self.copy_t = "Copy"
            self.copied_t = "Copied!"
        elif self.current_lang == "Deutsch":
            self.playlists_t = "Wiedergabelisten"
            self.new_playlist = "+ Neue Playlist"
            self.del_playlist = "🗑 Wiedergabeliste löschen"
            self.select_playlist_t = "Playlist auswählen"
            self.add_mp3 = "MP3 hinzufügen"
            self.download_from_YT = "Aus dem Web herunterladen"
            self.del_from_list = "Spur löschen"
            self.track_not_selected = "Track nicht ausgewählt"
            self.settings_t = "⚙️ Einstellungen"
            self.select_playlist_and_track = "Playlist und Titel auswählen, um zu starten"
            self.new_playlist_nop = "Neue Playlist"
            self.enter_playlist_name = "Geben Sie den Namen der Wiedergabeliste ein:"
            self.warning = "Warnung"
            self.playlist_already_exists = "Diese Playlist existiert bereits."
            self.error = "Fehler"
            self.cant_delete_main = "Hauptliste kann nicht gelöscht werden"
            self.deleting = "Löschen"
            self.delete_playlist_t = "Wiedergabeliste löschen"
            self.file_not_found = "Datei nicht gefunden (möglicherweise von der Festplatte gelöscht)"
            self.track_deleted = "Spur gelöscht"
            self.file_no_longer_exists = "Die Datei existiert unter dem angegebenen Pfad nicht mehr."
            self.select_track = "Track auswählen"
            self.playback = "Wiedergabe:"
            self.playback_on_pause = "Wiedergabe pausiert:"
            self.playlist_ended = "Playlist beendet"
            self.playback_stopped = "Wiedergabe gestoppt"
            self.settings_op = "Einstellungen"
            self.design_theme = "Designthema:"
            self.volum = "🔊 Volumen: "
            self.open_download_folder = "Download-Ordner öffnen"
            self.tutorial = "Tutorial"
            self.developerss = "Entwickler:"
            self.tutorial_does_not_exists = "Ein Tutorial existiert derzeit nicht."
            self.supported_links = "Unterstützte Links: YT, Newgrounds, Soundcloud"
            self.track_loading = "⏳ Sendung wird geladen..."
            self.done = "✅ Erledigt"
            self.lang = "Sprache:"
            self.click_stop_then_select = "Klicken Sie auf Stopp und wählen Sie dann einen neuen Titel zum Abspielen aus."
            self.shuffle_text = "Shuffle"
            self.stop_loading = "Download stoppen"
            self.loading_stopped = "Ladevorgang gestoppt"
            self.loop_text = "Wiederholen"
            self.del_loop_then_select = "Schalten Sie die Wiederholung aus und wählen Sie dann einen neuen Titel."
            self.loop_text = "Wiederholen"
            self.dont_repeat = "Wiederhole es nicht"
            self.show_tooltip_text = "Schieberegler-Tipp anzeigen"
            self.are_you_sure_delete_track = "Möchten Sie diesen Titel wirklich löschen?"
            self.rename_text = "Umbenennen"
            self.renaming_text = "Umbenennung"
            self.new_name = "Neuer Name:"
            self.track_url_t = "Track-URL"
            self.source_url_t = "Quelle (URL):"
            self.open_in_browser_t = "Im Browser öffnen"
            self.copy_t = "Kopieren"
            self.copied_t = "Kopiert!"
        elif self.current_lang == "ქართული":
            self.playlists_t = "დასაკრავი სიები"
            self.new_playlist = "+ ახალი დასაკრავი სია"
            self.del_playlist = "🗑 დასაკრავი სიის წაშლა"
            self.select_playlist_t = "დასაკრავი სიის არჩევა - აირჩიეთ დასაკრავი სია."
            self.add_mp3 = "MP3-ის დამატება"
            self.download_from_YT = "ჩამოტვირთვა ვებგვერდიდან"
            self.del_from_list = "ტრეკის წაშლა"
            self.track_not_selected = "ტრეკი არჩეული არ არის"
            self.settings_t = "⚙️ პარამეტრები"
            self.select_playlist_and_track = "დასაწყებად აირჩიეთ დასაკრავი სია და ტრეკი."
            self.new_playlist_nop = "ახალი დასაკრავი სია"
            self.enter_playlist_name = "შეიყვანეთ დასაკრავი სიის სახელი:"
            self.warning = "გაფრთხილება"
            self.playlist_already_exists = "ეს დასაკრავი სია უკვე არსებობს."
            self.error = "შეცდომა"
            self.cant_delete_main = "მთავარი სიის წაშლა შეუძლებელია"
            self.deleting = "წაშლა"
            self.delete_playlist_t = "დასაკრავი სიის წაშლა"
            self.file_not_found = "ფაილი ვერ მოიძებნა (შესაძლოა წაშლილია დისკიდან)"
            self.track_deleted = "ტრეკი წაშლილია"
            self.file_no_longer_exists = "ფაილი მითითებულ გზაზე აღარ არსებობს."
            self.select_track = "აირჩიეთ ჩანაწერი"
            self.playback = "დაკვრა:"
            self.playback_on_pause = "დაკვრა პაუზის დროს:"
            self.playlist_ended = "დასაკრავი სია დასრულდა"
            self.playback_stopped = "დაკვრა შეჩერდა"
            self.settings_op = "პარამეტრები"
            self.design_theme = "დიზაინის თემა:"
            self.volum = "🔊 მოცულობა:"
            self.open_download_folder = "ჩამოტვირთვების საქაღალდის გახსნა"
            self.tutorial = "სახელმძღვანელო"
            self.developerss = "დეველოპერები:"
            self.tutorial_does_not_exists = "სახელმძღვანელო ამჟამად არ არსებობს."
            self.supported_links = "მხარდაჭერილი ბმულები: YT, Newgrounds, Soundcloud"
            self.track_loading = "⏳ ტრეკის ჩატვირთვა..."
            self.done = "✅ დასრულებულია"
            self.lang = "ენა:"
            self.click_stop_then_select = "დააჭირეთ გაჩერებას, შემდეგ აირჩიეთ ახალი ჩანაწერი დასაკრავად"
            self.shuffle_text = "არევა"
            self.stop_loading = "ჩამოტვირთვის შეჩერება"
            self.loading_stopped = "ჩატვირთვა შეჩერდა"
            self.loop_text = "გამეორება"
            self.del_loop_then_select = "გამორთეთ გამეორება, შემდეგ აირჩიეთ ახალი ტრეკი"
            self.dont_repeat = "არ გაიმეორო"
            self.show_tooltip_text = "სლაიდერის რჩევის ჩვენება"
            self.are_you_sure_delete_track = "დარწმუნებული ხართ, რომ გსურთ ამ ტრეკის წაშლა?"
            self.rename_text = "გადარქმევა"
            self.renaming_text = "გადარქმევა"
            self.new_name = "ახალი სახელი:"
            self.track_url_t = "ტრეკის URL"
            self.source_url_t = "წყარო (URL):"
            self.open_in_browser_t = "ბრაუზერში გახსნა"
            self.copy_t = "კოპირება"
            self.copied_t = "დაკოპირებულია!"
        elif self.current_lang == "español":
            self.playlists_t = "Listas de reproducción"
            self.new_playlist = "+ Nueva lista de reproducción"
            self.del_playlist = "🗑 Eliminar lista de reproducción"
            self.select_playlist_t = "Seleccionar lista de reproducción"
            self.add_mp3 = "Añadir MP3"
            self.download_from_YT = "Descargar desde la Web"
            self.del_from_list = "Eliminar pista"
            self.track_not_selected = "Pista no seleccionada"
            self.settings_t = "⚙️ Ajustes"
            self.select_playlist_and_track = "Seleccione la lista de reproducción y la pista para comenzar"
            self.new_playlist_nop = "Nueva lista de reproducción"
            self.enter_playlist_name = "Introduzca el nombre de la lista de reproducción:"
            self.warning = "Advertencia"
            self.playlist_already_exists = "Esta lista de reproducción ya existe"
            self.error = "Error"
            self.cant_delete_main = "No se puede eliminar la lista principal"
            self.deleting = "Eliminando"
            self.delete_playlist_t = "Eliminar lista de reproducción"
            self.file_not_found = "Archivo no encontrado (posiblemente eliminado del disco)"
            self.track_deleted = "Pista eliminada"
            self.file_no_longer_exists = "El archivo ya no existe en la ruta especificada."
            self.select_track = "Seleccionar pista"
            self.playback = "Reproducción:"
            self.playback_on_pause = "Reproducción en pausa:"
            self.playlist_ended = "Lista de reproducción finalizada"
            self.playback_stopped = "La reproducción se detuvo"
            self.settings_op = "Ajustes"
            self.design_theme = "Tema de diseño:"
            self.volum = "🔊 Volumen:"
            self.open_download_folder = "Abrir carpeta de descargas"
            self.tutorial = "Tutorial"
            self.developerss = "Desarrolladores:"
            self.tutorial_does_not_exists = "El tutorial no existe actualmente."
            self.supported_links = "Enlaces compatibles: YT, Newgrounds, Soundcloud"
            self.track_loading = "⏳ Cargando pista..."
            self.done = "✅ Hecho"
            self.lang = "Idioma:"
            self.click_stop_then_select = "Haga clic en detener y luego seleccione una nueva pista para reproducir"
            self.shuffle_text = "Barajar"
            self.stop_loading = "Detener descarga"
            self.loading_stopped = "Carga detenida"
            self.loop_text = "Repetir"
            self.del_loop_then_select = "Desactiva la repetición y luego selecciona una nueva pista."
            self.dont_repeat = "No lo repitas"
            self.show_tooltip_text = "Mostrar consejo deslizante"
            self.are_you_sure_delete_track = "¿Seguro que quieres eliminar esta pista?"
            self.rename_text = "Rebautizar"
            self.renaming_text = "Cambiar el nombre"
            self.new_name = "Nuevo nombre:"
            self.track_url_t = "URL de seguimiento"
            self.source_url_t = "Fuente (URL):"
            self.open_in_browser_t = "Abrir en el navegador"
            self.copy_t = "Copiar"
            self.copied_t = "¡Copiado!"
        elif self.current_lang == "Українська":
            self.playlists_t = "Плейлисти"
            self.new_playlist = "+ Новий плейлист"
            self.del_playlist = "🗑 Видалити плейлист"
            self.select_playlist_t = "Виберіть плейлист"
            self.add_mp3 = "Додати MP3"
            self.download_from_YT = "Завантажити з інтернету"
            self.del_from_list = "Видалити трек"
            self.track_not_selected = "Трек не вибрано"
            self.settings_t = "⚙️ Налаштування"
            self.select_playlist_and_track = "Виберіть плейлист і трек для початку"
            self.new_playlist_nop = "Новий плейлист"
            self.enter_playlist_name = "Введіть назву плейлиста:"
            self.warning = "Попередження"
            self.playlist_already_exists = "Цей плейлист уже існує"
            self.error = "Помилка"
            self.cant_delete_main = "Неможливо видалити основний список"
            self.deleting = "Видалення"
            self.delete_playlist_t = "Видалити плейлист"
            self.file_not_found = "Файл не знайдено (можливо видалений з диска)"
            self.track_deleted = "Трек видалено"
            self.file_no_longer_exists = "Файл більше не існує за вказаним шляхом."
            self.select_track = "Виберіть трек"
            self.playback = "Відтворення:"
            self.playback_on_pause = "Відтворення на паузі:"
            self.playlist_ended = "Плейлист завершено"
            self.playback_stopped = "Відтворення зупинено"
            self.settings_op = "Налаштування"
            self.design_theme = "Тема оформлення:"
            self.volum = "🔊 Гучність:"
            self.open_download_folder = "Відкрити папку завантажень"
            self.tutorial = "Посібник"
            self.developerss = "Розробники:"
            self.tutorial_does_not_exists = "Посібник наразі не існує."
            self.supported_links = "Підтримувані посилання: YT, Newgrounds, SoundCloud"
            self.track_loading = "⏳ Завантаження треку..."
            self.done = "✅ Готово"
            self.lang = "Мова:"
            self.click_stop_then_select = "Натисніть кнопку зупинки, а потім виберіть новий трек для відтворення"
            self.shuffle_text = "Перемішати"
            self.stop_loading = "Зупинити завантаження"
            self.loading_stopped = "Завантаження зупинено"
            self.loop_text = "Повторити"
            self.del_loop_then_select = "Вимкніть повтор, а потім виберіть новий трек"
            self.dont_repeat = "Не повторюй"
            self.show_tooltip_text = "Показати підказку слайдера"
            self.are_you_sure_delete_track = "Ви впевнені, що хочете видалити цей трек?"
            self.rename_text = "Перейменувати"
            self.renaming_text = "Перейменування"
            self.new_name = "Нове ім'я:"
            self.track_url_t = "URL треку"
            self.source_url_t = "Джерело (URL):"
            self.open_in_browser_t = "Відкрити в браузері"
            self.copy_t = "Копіювати"
            self.copied_t = "Скопійовано!"
        elif self.current_lang == "Қазақ":
            self.playlists_t = "Плейлисттер"
            self.new_playlist = "+ Жаңа плейлист"
            self.del_playlist = "🗑 Плейлистті жою"
            self.select_playlist_t = "Плейлистті таңдаңыз"
            self.add_mp3 = "MP3 қосу"
            self.download_from_YT = "Интернеттен жүктеу"
            self.del_from_list = "Тректі жою"
            self.track_not_selected = "Трек таңдалмады"
            self.settings_t = "⚙️ Баптаулар"
            self.select_playlist_and_track = "Бастау үшін плейлист пен тректі таңдаңыз"
            self.new_playlist_nop = "Жаңа плейлист"
            self.enter_playlist_name = "Плейлист атауын енгізіңіз:"
            self.warning = "Ескерту"
            self.playlist_already_exists = "Бұл плейлист бұрыннан бар"
            self.error = "Қате"
            self.cant_delete_main = "Негізгі тізімді жою мүмкін емес"
            self.deleting = "Жойылуда"
            self.delete_playlist_t = "Плейлистті жою"
            self.file_not_found = "Файл табылмады (мүмкін дискіден жойылған)"
            self.track_deleted = "Трек жойылды"
            self.file_no_longer_exists = "Файл көрсетілген жолда енді жоқ."
            self.select_track = "Тректі таңдаңыз"
            self.playback = "Ойнату:"
            self.playback_on_pause = "Паузада ойнату:"
            self.playlist_ended = "Плейлист аяқталды"
            self.playback_stopped = "Ойнату тоқтатылды"
            self.settings_op = "Баптаулар"
            self.design_theme = "Дизайн тақырыбы:"
            self.volum = "🔊 Дыбыс деңгейі:"
            self.open_download_folder = "Жүктеулер қалтасын ашу"
            self.tutorial = "Нұсқаулық"
            self.developerss = "Әзірлеушілер:"
            self.tutorial_does_not_exists = "Нұсқаулық әзірге жоқ."
            self.supported_links = "Қолдау көрсетілетін сілтемелер: YT, Newgrounds, SoundCloud"
            self.track_loading = "⏳ Трек жүктелуде..."
            self.done = "✅ Дайын"
            self.lang = "Тіл:"
            self.click_stop_then_select = "«Тоқтату» түймесін басыңыз, содан кейін ойнатылатын жаңа тректі таңдаңыз"
            self.shuffle_text = "Араластыру"
            self.stop_loading = "Жүктеуді тоқтату"
            self.loading_stopped = "Жүктеу тоқтатылды"
            self.loop_text = "Қайталау"
            self.del_loop_then_select = "Қайталауды өшіріп, жаңа тректі таңдаңыз"
            self.dont_repeat = "Қайталама"
            self.show_tooltip_text = "Слайдер ұшын көрсету"
            self.are_you_sure_delete_track = "Бұл тректі жойғыңыз келе ме?"
            self.rename_text = "Атын өзгерту"
            self.renaming_text = "Атын өзгерту"
            self.new_name = "Жаңа атау:"
            self.track_url_t = "Трек URL"
            self.source_url_t = "Дереккөз (URL):"
            self.open_in_browser_t = "Браузерде ашу"
            self.copy_t = "Көшіру"
            self.copied_t = "Көшірілді!"
        elif self.current_lang == "Polski":
            self.playlists_t = "Playlisty"
            self.new_playlist = "+ Nowa playlista"
            self.del_playlist = "🗑 Usuń playlistę"
            self.select_playlist_t = "Wybierz playlistę"
            self.add_mp3 = "Dodaj MP3"
            self.download_from_YT = "Pobierz z internetu"
            self.del_from_list = "Usuń utwór"
            self.track_not_selected = "Nie wybrano utworu"
            self.settings_t = "⚙️ Ustawienia"
            self.select_playlist_and_track = "Wybierz playlistę i utwór, aby rozpocząć"
            self.new_playlist_nop = "Nowa playlista"
            self.enter_playlist_name = "Wprowadź nazwę playlisty:"
            self.warning = "Ostrzeżenie"
            self.playlist_already_exists = "Ta playlista już istnieje"
            self.error = "Błąd"
            self.cant_delete_main = "Nie można usunąć głównej listy"
            self.deleting = "Usuwanie"
            self.delete_playlist_t = "Usuń playlistę"
            self.file_not_found = "Nie znaleziono pliku (może został usunięty z dysku)"
            self.track_deleted = "Utwór usunięty"
            self.file_no_longer_exists = "Plik nie istnieje już w podanej ścieżce."
            self.select_track = "Wybierz utwór"
            self.playback = "Odtwarzanie:"
            self.playback_on_pause = "Odtwarzanie na pauzie:"
            self.playlist_ended = "Playlista zakończona"
            self.playback_stopped = "Odtwarzanie zatrzymane"
            self.settings_op = "Ustawienia"
            self.design_theme = "Motyw wyglądu:"
            self.volum = "🔊 Głośność:"
            self.open_download_folder = "Otwórz folder pobrań"
            self.tutorial = "Instrukcja"
            self.developerss = "Twórcy:"
            self.tutorial_does_not_exists = "Instrukcja obecnie nie istnieje."
            self.supported_links = "Obsługiwane linki: YT, Newgrounds, SoundCloud"
            self.track_loading = "⏳ Ładowanie utworu..."
            self.done = "✅ Gotowe"
            self.lang = "Język:"
            self.click_stop_then_select = "Kliknij „Zatrzymaj”, a następnie wybierz nowy utwór do odtworzenia"
            self.shuffle_text = "Człapać"
            self.stop_loading = "Zatrzymaj pobieranie"
            self.loading_stopped = "Ładowanie zatrzymane"
            self.loop_text = "Powtarzać"
            self.del_loop_then_select = "Wyłącz powtarzanie, a następnie wybierz nowy utwór"
            self.dont_repeat = "Nie powtarzaj"
            self.show_tooltip_text = "Pokaż wskazówkę suwaka"
            self.are_you_sure_delete_track = "Czy na pewno chcesz usunąć ten utwór?"
            self.rename_text = "Przemianować"
            self.renaming_text = "Zmiana nazwy"
            self.new_name = "Nowa nazwa:"
            self.track_url_t = "URL utworu"
            self.source_url_t = "Źródło (URL):"
            self.open_in_browser_t = "Otwórz w przeglądarce"
            self.copy_t = "Kopiuj"
            self.copied_t = "Skopiowano!"
        elif self.current_lang == "Français":
            self.playlists_t = "Playlists"
            self.new_playlist = "+ Nouvelle playlist"
            self.del_playlist = "🗑 Supprimer la playlist"
            self.select_playlist_t = "Sélectionnez une playlist"
            self.add_mp3 = "Ajouter MP3"
            self.download_from_YT = "Télécharger depuis le web"
            self.del_from_list = "Supprimer la piste"
            self.track_not_selected = "Aucune piste sélectionnée"
            self.settings_t = "⚙️ Paramètres"
            self.select_playlist_and_track = "Sélectionnez une playlist et une piste pour commencer"
            self.new_playlist_nop = "Nouvelle playlist"
            self.enter_playlist_name = "Entrez le nom de la playlist :"
            self.warning = "Avertissement"
            self.playlist_already_exists = "Cette playlist existe déjà"
            self.error = "Erreur"
            self.cant_delete_main = "Impossible de supprimer la liste principale"
            self.deleting = "Suppression"
            self.delete_playlist_t = "Supprimer la playlist"
            self.file_not_found = "Fichier introuvable (peut-être supprimé du disque)"
            self.track_deleted = "Piste supprimée"
            self.file_no_longer_exists = "Le fichier n'existe plus à l'emplacement spécifié."
            self.select_track = "Sélectionnez une piste"
            self.playback = "Lecture :"
            self.playback_on_pause = "Lecture en pause :"
            self.playlist_ended = "Playlist terminée"
            self.playback_stopped = "Lecture arrêtée"
            self.settings_op = "Paramètres"
            self.design_theme = "Thème de design :"
            self.volum = "🔊 Volume :"
            self.open_download_folder = "Ouvrir le dossier des téléchargements"
            self.tutorial = "Tutoriel"
            self.developerss = "Développeurs :"
            self.tutorial_does_not_exists = "Le tutoriel n'existe pas actuellement."
            self.supported_links = "Liens pris en charge : YT, Newgrounds, SoundCloud"
            self.track_loading = "⏳ Chargement de la piste..."
            self.done = "✅ Terminé"
            self.lang = "Langue :"
            self.click_stop_then_select = "Cliquez sur Arrêter, puis sélectionnez un nouveau morceau à lire."
            self.shuffle_text = "Mélanger"
            self.stop_loading = "Arrêter le téléchargement"
            self.loading_stopped = "Chargement arrêté"
            self.loop_text = "Répéter"
            self.del_loop_then_select = "Désactivez la répétition, puis sélectionnez une nouvelle piste."
            self.dont_repeat = "Ne pas répéter"
            self.show_tooltip_text = "Afficher le conseil du curseur"
            self.are_you_sure_delete_track = "Êtes-vous sûr de vouloir supprimer ce morceau ?"
            self.rename_text = "Rebaptiser"
            self.renaming_text = "Renommer"
            self.new_name = "Nouveau nom :"
            self.track_url_t = "URL de piste"
            self.source_url_t = "Source (URL) :"
            self.open_in_browser_t = "Ouvrir dans le navigateur"
            self.copy_t = "Copier"
            self.copied_t = "Copié !"
        elif self.current_lang == "日本語":  # japan
            self.playlists_t = "プレイリスト"
            self.new_playlist = "+ 新しいプレイリスト"
            self.del_playlist = "🗑 プレイリストを削除"
            self.select_playlist_t = "プレイリストを選択"
            self.add_mp3 = "MP3を追加"
            self.download_from_YT = "ウェブからダウンロード"
            self.del_from_list = "トラックを削除"
            self.track_not_selected = "トラックが選択されていません"
            self.settings_t = "⚙️ 設定"
            self.select_playlist_and_track = "開始するにはプレイリストとトラックを選択してください"
            self.new_playlist_nop = "新しいプレイリスト"
            self.enter_playlist_name = "プレイリスト名を入力してください:"
            self.warning = "警告"
            self.playlist_already_exists = "このプレイリストは既に存在します"
            self.error = "エラー"
            self.cant_delete_main = "メインリストは削除できません"
            self.deleting = "削除中"
            self.delete_playlist_t = "プレイリストを削除"
            self.file_not_found = "ファイルが見つかりません（ディスクから削除された可能性があります）"
            self.track_deleted = "トラックが削除されました"
            self.file_no_longer_exists = "指定されたパスにファイルはもう存在しません。"
            self.select_track = "トラックを選択"
            self.playback = "再生:"
            self.playback_on_pause = "一時停止中の再生:"
            self.playlist_ended = "プレイリストが終了しました"
            self.playback_stopped = "再生が停止しました"
            self.settings_op = "設定"
            self.design_theme = "デザインテーマ:"
            self.volum = "🔊 音量:"
            self.open_download_folder = "ダウンロードフォルダを開く"
            self.tutorial = "チュートリアル"
            self.developerss = "開発者:"
            self.tutorial_does_not_exists = "チュートリアルは現在存在しません。"
            self.supported_links = "対応リンク: YT, Newgrounds, SoundCloud"
            self.track_loading = "⏳ トラックを読み込み中..."
            self.done = "✅ 完了"
            self.lang = "言語:"
            self.click_stop_then_select = "停止をクリックし、再生する新しいトラックを選択します"
            self.shuffle_text = "シャッフル"
            self.stop_loading = "ダウンロードを停止"
            self.loading_stopped = "読み込みが停止しました"
            self.loop_text = "繰り返す"
            self.del_loop_then_select = "リピートをオフにしてから、新しいトラックを選択してください。"
            self.dont_repeat = "繰り返さないで"
            self.show_tooltip_text = "スライダーのヒントを表示"
            self.are_you_sure_delete_track = "このトラックを削除してもよろしいですか？"
            self.rename_text = "名前を変更する"
            self.renaming_text = "名前変更"
            self.new_name = "新しい名前:"
            self.track_url_t = "トラックURL"
            self.source_url_t = "ソース（URL）："
            self.open_in_browser_t = "ブラウザで開く"
            self.copy_t = "コピー"
            self.copied_t = "コピーしました！"
        elif self.current_lang == "中國人":  # chinese
            self.playlists_t = "播放列表"
            self.new_playlist = "+ 新建播放列表"
            self.del_playlist = "🗑 删除播放列表"
            self.select_playlist_t = "选择播放列表"
            self.add_mp3 = "添加 MP3"
            self.download_from_YT = "从网络下载"
            self.del_from_list = "刪除曲目"
            self.track_not_selected = "未选择曲目"
            self.settings_t = "⚙️ 设置"
            self.select_playlist_and_track = "选择播放列表和曲目以开始"
            self.new_playlist_nop = "新建播放列表"
            self.enter_playlist_name = "输入播放列表名称:"
            self.warning = "警告"
            self.playlist_already_exists = "该播放列表已存在"
            self.error = "错误"
            self.cant_delete_main = "无法删除主列表"
            self.deleting = "正在删除"
            self.delete_playlist_t = "删除播放列表"
            self.file_not_found = "未找到文件（可能已从磁盘删除）"
            self.track_deleted = "曲目已删除"
            self.file_no_longer_exists = "该文件在指定路径中已不存在。"
            self.select_track = "选择曲目"
            self.playback = "播放:"
            self.playback_on_pause = "暂停时播放:"
            self.playlist_ended = "播放列表已结束"
            self.playback_stopped = "播放已停止"
            self.settings_op = "设置"
            self.design_theme = "设计主题:"
            self.volum = "🔊 音量:"
            self.open_download_folder = "打开下载文件夹"
            self.tutorial = "教程"
            self.developerss = "开发者:"
            self.tutorial_does_not_exists = "当前没有教程。"
            self.supported_links = "支持的链接: YT, Newgrounds, SoundCloud"
            self.track_loading = "⏳ 曲目加载中..."
            self.done = "✅ 完成"
            self.lang = "语言:"
            self.click_stop_then_select = "點擊停止，然後選擇要播放的新曲目"
            self.shuffle_text = "洗牌"
            self.stop_loading = "停止下載"
            self.loading_stopped = "載入已停止"
            self.loop_text = "重複"
            self.del_loop_then_select = "關閉重複播放，然後選擇新曲目"
            self.dont_repeat = "不要重複"
            self.show_tooltip_text = "顯示滑桿提示"
            self.are_you_sure_delete_track = "您確定要刪除此曲目嗎？"
            self.rename_text = "重新命名"
            self.renaming_text = "重新命名"
            self.new_name = "新名稱："
            self.track_url_t = "曲目 URL"
            self.source_url_t = "来源（URL）："
            self.open_in_browser_t = "在浏览器中打开"
            self.copy_t = "复制"
            self.copied_t = "已复制！"
        elif self.current_lang == "Italiano":
            self.playlists_t = "Playlist"
            self.new_playlist = "+ Nuova playlist"
            self.del_playlist = "🗑 Elimina playlist"
            self.select_playlist_t = "Seleziona playlist"
            self.add_mp3 = "Aggiungi MP3"
            self.download_from_YT = "Scarica dal web"
            self.del_from_list = "Elimina traccia"
            self.track_not_selected = "Nessuna traccia selezionata"
            self.settings_t = "⚙️ Impostazioni"
            self.select_playlist_and_track = "Seleziona playlist e traccia per iniziare"
            self.new_playlist_nop = "Nuova playlist"
            self.enter_playlist_name = "Inserisci il nome della playlist:"
            self.warning = "Avviso"
            self.playlist_already_exists = "Questa playlist esiste già"
            self.error = "Errore"
            self.cant_delete_main = "Impossibile eliminare la lista principale"
            self.deleting = "Eliminazione"
            self.delete_playlist_t = "Elimina playlist"
            self.file_not_found = "File non trovato (forse eliminato dal disco)"
            self.track_deleted = "Traccia eliminata"
            self.file_no_longer_exists = "Il file non esiste più nel percorso specificato."
            self.select_track = "Seleziona traccia"
            self.playback = "Riproduzione:"
            self.playback_on_pause = "Riproduzione in pausa:"
            self.playlist_ended = "Playlist terminata"
            self.playback_stopped = "Riproduzione interrotta"
            self.settings_op = "Impostazioni"
            self.design_theme = "Tema del design:"
            self.volum = "🔊 Volume:"
            self.open_download_folder = "Apri cartella dei download"
            self.tutorial = "Tutorial"
            self.developerss = "Sviluppatori:"
            self.tutorial_does_not_exists = "Il tutorial non esiste al momento."
            self.supported_links = "Link supportati: YT, Newgrounds, SoundCloud"
            self.track_loading = "⏳ Caricamento traccia..."
            self.done = "✅ Fatto"
            self.lang = "Lingua:"
            self.click_stop_then_select = "Fare clic su Stop, quindi selezionare la nuova traccia da riprodurre"
            self.shuffle_text = "Mescola"
            self.stop_loading = "Interrompi il download"
            self.loading_stopped = "Caricamento interrotto"
            self.loop_text = "Ripetere"
            self.del_loop_then_select = "Disattiva la ripetizione, quindi seleziona un nuovo brano."
            self.dont_repeat = "Non ripetere"
            self.show_tooltip_text = "Mostra suggerimento del cursore"
            self.are_you_sure_delete_track = "Sei sicuro di voler eliminare questa traccia?"
            self.rename_text = "Rinominare"
            self.renaming_text = "Rinominare"
            self.new_name = "Nuovo nome:"
            self.track_url_t = "URL traccia"
            self.source_url_t = "Fonte (URL):"
            self.open_in_browser_t = "Apri nel browser"
            self.copy_t = "Copia"
            self.copied_t = "Copiato!"
        elif self.current_lang == "Azərbaycan dili": # azerba
            self.playlists_t = "Pleylistlər"
            self.new_playlist = "+ Yeni pleylist"
            self.del_playlist = "🗑 Pleylisti sil"
            self.select_playlist_t = "Pleylist seç"
            self.add_mp3 = "MP3 əlavə et"
            self.download_from_YT = "Vebdən yüklə"
            self.del_from_list = "Treki sil"
            self.track_not_selected = "Trek seçilməyib"
            self.settings_t = "⚙️ Parametrlər"
            self.select_playlist_and_track = "Başlamaq üçün pleylist və trek seçin"
            self.new_playlist_nop = "Yeni pleylist"
            self.enter_playlist_name = "Pleylist adını daxil edin:"
            self.warning = "Xəbərdarlıq"
            self.playlist_already_exists = "Bu pleylist artıq mövcuddur"
            self.error = "Xəta"
            self.cant_delete_main = "Əsas siyahını silmək olmaz"
            self.deleting = "Silinir"
            self.delete_playlist_t = "Pleylisti sil"
            self.file_not_found = "Fayl tapılmadı (bəlkə diskdən silinib)"
            self.track_deleted = "Trek silindi"
            self.file_no_longer_exists = "Fayl artıq göstərilən yolda mövcud deyil."
            self.select_track = "Trek seç"
            self.playback = "Oxutma:"
            self.playback_on_pause = "Pauzada oxutma:"
            self.playlist_ended = "Pleylist bitdi"
            self.playback_stopped = "Oxutma dayandırıldı"
            self.settings_op = "Parametrlər"
            self.design_theme = "Dizayn mövzusu:"
            self.volum = "🔊 Səs səviyyəsi:"
            self.open_download_folder = "Yükləmələr qovluğunu aç"
            self.tutorial = "Təlimat"
            self.developerss = "Tərtibatçılar:"
            self.tutorial_does_not_exists = "Təlimat hazırda mövcud deyil."
            self.supported_links = "Dəstəklənən linklər: YT, Newgrounds, Soundcloud"
            self.track_loading = "⏳ Trek yüklənir..."
            self.done = "✅ Hazırdır"
            self.lang = "Dil:"
            self.click_stop_then_select = "Dayandır düyməsini basın, sonra yeni trek seçin"
            self.shuffle_text = "Qarışdır"
            self.stop_loading = "Yükləməni dayandır"
            self.loading_stopped = "Yükləmə dayandırıldı"
            self.loop_text = "Təkrar"
            self.del_loop_then_select = "Təkrarı söndürün, sonra yeni trek seçin"
            self.dont_repeat = "Təkrarlama"
            self.show_tooltip_text = "Sürgü ipucunu göstər"
            self.are_you_sure_delete_track = "Bu treki silmək istədiyinizə əminsiniz?"
            self.rename_text = "Adını dəyiş"
            self.renaming_text = "Ad dəyişdirilir"
            self.new_name = "Yeni ad:"
            self.track_url_t = "Track URL"
            self.source_url_t = "Mənbə (URL):"
            self.open_in_browser_t = "Brauzerdə aç"
            self.copy_t = "Kopyala"
            self.copied_t = "Kopyalandı!"
        elif self.current_lang == "беларуская":
            self.playlists_t = "Плэйлісты"
            self.new_playlist = "+ Новы плэйліст"
            self.del_playlist = "🗑 Выдаліць плэйліст"
            self.select_playlist_t = "Выберыце плэйліст"
            self.add_mp3 = "Дадаць MP3"
            self.download_from_YT = "Спампаваць з інтэрнэту"
            self.del_from_list = "Выдаліць трэк"
            self.track_not_selected = "Трэк не выбраны"
            self.settings_t = "⚙️ Налады"
            self.select_playlist_and_track = "Выберыце плэйліст і трэк для запуску"
            self.new_playlist_nop = "Новы плэйліст"
            self.enter_playlist_name = "Увядзіце назву плэйліста:"
            self.warning = "Папярэджанне"
            self.playlist_already_exists = "Гэты плэйліст ужо існуе"
            self.error = "Памылка"
            self.cant_delete_main = "Нельга выдаліць асноўны спіс"
            self.deleting = "Выдаленне"
            self.delete_playlist_t = "Выдаліць плэйліст"
            self.file_not_found = "Файл не знойдзены (магчыма, выдалены з дыска)"
            self.track_deleted = "Трэк выдалены"
            self.file_no_longer_exists = "Файл больш не існуе па ўказаным шляху."
            self.select_track = "Выберыце трэк"
            self.playback = "Прайграванне:"
            self.playback_on_pause = "Прайграванне на паўзе:"
            self.playlist_ended = "Плэйліст завершаны"
            self.playback_stopped = "Прайграванне спынена"
            self.settings_op = "Налады"
            self.design_theme = "Тэма дызайну:"
            self.volum = "🔊 Гучнасць:"
            self.open_download_folder = "Адкрыць папку загрузак"
            self.tutorial = "Кіраўніцтва"
            self.developerss = "Распрацоўшчыкі:"
            self.tutorial_does_not_exists = "Кіраўніцтва пакуль не існуе."
            self.supported_links = "Падтрымліваюцца спасылкі: YT, Newgrounds, Soundcloud"
            self.track_loading = "⏳ Трэк загружаецца..."
            self.done = "✅ Гатова"
            self.lang = "Мова:"
            self.click_stop_then_select = "Націсніце «Стоп», затым выберыце новы трэк"
            self.shuffle_text = "Перамешаць"
            self.stop_loading = "Спыніць загрузку"
            self.loading_stopped = "Загрузка спынена"
            self.loop_text = "Паўтор"
            self.del_loop_then_select = "Адключыце паўтор, затым выберыце новы трэк"
            self.dont_repeat = "Без паўтору"
            self.show_tooltip_text = "Паказваць падказку паўзунка"
            self.are_you_sure_delete_track = "Вы сапраўды хочаце выдаліць гэты трэк?"
            self.rename_text = "Перайменаваць"
            self.renaming_text = "Перайменаванне"
            self.new_name = "Новая назва:"
            self.track_url_t = "URL трэка"
            self.source_url_t = "Крыніца (URL):"
            self.open_in_browser_t = "Адкрыць у браўзеры"
            self.copy_t = "Капіяваць"
            self.copied_t = "Скапіявана!"
        elif self.current_lang == "Türkçe":
            self.playlists_t = "Çalma listeleri"
            self.new_playlist = "+ Yeni çalma listesi"
            self.del_playlist = "🗑 Çalma listesini sil"
            self.select_playlist_t = "Çalma listesi seç"
            self.add_mp3 = "MP3 ekle"
            self.download_from_YT = "Web'den indir"
            self.del_from_list = "Parçayı sil"
            self.track_not_selected = "Parça seçilmedi"
            self.settings_t = "⚙️ Ayarlar"
            self.select_playlist_and_track = "Başlatmak için çalma listesi ve parça seçin"
            self.new_playlist_nop = "Yeni çalma listesi"
            self.enter_playlist_name = "Çalma listesi adını girin:"
            self.warning = "Uyarı"
            self.playlist_already_exists = "Bu çalma listesi zaten mevcut"
            self.error = "Hata"
            self.cant_delete_main = "Ana liste silinemez"
            self.deleting = "Siliniyor"
            self.delete_playlist_t = "Çalma listesini sil"
            self.file_not_found = "Dosya bulunamadı (muhtemelen diskten silinmiş)"
            self.track_deleted = "Parça silindi"
            self.file_no_longer_exists = "Dosya belirtilen konumda artık mevcut değil."
            self.select_track = "Parça seç"
            self.playback = "Oynatma:"
            self.playback_on_pause = "Duraklatıldığında oynatma:"
            self.playlist_ended = "Çalma listesi sona erdi"
            self.playback_stopped = "Oynatma durduruldu"
            self.settings_op = "Ayarlar"
            self.design_theme = "Tasarım teması:"
            self.volum = "🔊 Ses seviyesi:"
            self.open_download_folder = "İndirilenler klasörünü aç"
            self.tutorial = "Kılavuz"
            self.developerss = "Geliştiriciler:"
            self.tutorial_does_not_exists = "Kılavuz şu anda mevcut değil."
            self.supported_links = "Desteklenen bağlantılar: YT, Newgrounds, Soundcloud"
            self.track_loading = "⏳ Parça yükleniyor..."
            self.done = "✅ Tamam"
            self.lang = "Dil:"
            self.click_stop_then_select = "Durdur'a basın, sonra yeni bir parça seçin"
            self.shuffle_text = "Karıştır"
            self.stop_loading = "İndirmeyi durdur"
            self.loading_stopped = "Yükleme durduruldu"
            self.loop_text = "Tekrar"
            self.del_loop_then_select = "Tekrarı kapatın, sonra yeni bir parça seçin"
            self.dont_repeat = "Tekrar yok"
            self.show_tooltip_text = "Kaydırıcı ipucunu göster"
            self.are_you_sure_delete_track = "Bu parçayı silmek istediğinizden emin misiniz?"
            self.rename_text = "Yeniden adlandır"
            self.renaming_text = "Yeniden adlandırılıyor"
            self.new_name = "Yeni ad:"
            self.track_url_t = "URL трэка"
            self.source_url_t = "Крыніца (URL):"
            self.open_in_browser_t = "Адкрыць у браўзеры"
            self.copy_t = "Капіяваць"
            self.copied_t = "Скапіявана!"
        elif self.current_lang == "Татар (кириллица)":
            self.playlists_t = "Плейлистлар"
            self.new_playlist = "+ Яңа плейлист"
            self.del_playlist = "🗑 Плейлистны бетерү"
            self.select_playlist_t = "Плейлист сайлагыз"
            self.add_mp3 = "MP3 өстәү"
            self.download_from_YT = "Интернеттан йөкләү"
            self.del_from_list = "Трекны бетерү"
            self.track_not_selected = "Трек сайланмаган"
            self.settings_t = "⚙️ Көйләүләр"
            self.select_playlist_and_track = "Башлау өчен плейлист һәм трек сайлагыз"
            self.new_playlist_nop = "Яңа плейлист"
            self.enter_playlist_name = "Плейлист исемен кертегез:"
            self.warning = "Кисәтү"
            self.playlist_already_exists = "Бу плейлист инде бар"
            self.error = "Хата"
            self.cant_delete_main = "Төп исемлекне бетереп булмый"
            self.deleting = "Бетерелә"
            self.delete_playlist_t = "Плейлистны бетерү"
            self.file_not_found = "Файл табылмады (бәлки дискта юк)"
            self.track_deleted = "Трек бетерелде"
            self.file_no_longer_exists = "Файл күрсәтелгән юлда инде юк."
            self.select_track = "Трек сайлагыз"
            self.playback = "Уйнату:"
            self.playback_on_pause = "Паузада уйнату:"
            self.playlist_ended = "Плейлист тәмамланды"
            self.playback_stopped = "Уйнату туктатылды"
            self.settings_op = "Көйләүләр"
            self.design_theme = "Дизайн темасы:"
            self.volum = "🔊 Тавыш дәрәҗәсе:"
            self.open_download_folder = "Йөкләүләр папкасын ачу"
            self.tutorial = "Кулланма"
            self.developerss = "Эшләүчеләр:"
            self.tutorial_does_not_exists = "Кулланма әлегә юк."
            self.supported_links = "Ярдәм ителә торган сылтамалар: YT, Newgrounds, Soundcloud"
            self.track_loading = "⏳ Трек йөкләнә..."
            self.done = "✅ Әзер"
            self.lang = "Тел:"
            self.click_stop_then_select = "Башта туктатыгыз, аннары яңа трек сайлагыз"
            self.shuffle_text = "Бутарга"
            self.stop_loading = "Йөкләүне туктату"
            self.loading_stopped = "Йөкләү туктатылды"
            self.loop_text = "Кабатлау"
            self.del_loop_then_select = "Кабатлауны сүндерегез, аннары яңа трек сайлагыз"
            self.dont_repeat = "Кабатламаска"
            self.show_tooltip_text = "Слайдер киңәшен күрсәтү"
            self.are_you_sure_delete_track = "Бу трекны бетерергә телисезме?"
            self.rename_text = "Исемен үзгәртү"
            self.renaming_text = "Исем үзгәртелә"
            self.new_name = "Яңа исем:"
            self.track_url_t = "Трек URL"
            self.source_url_t = "Чыганак (URL):"
            self.open_in_browser_t = "Браузерда ачу"
            self.copy_t = "Күчерү"
            self.copied_t = "Күчерелде!"
        elif self.current_lang == "हिंदी":  # hindi
            self.playlists_t = "प्लेलिस्ट"
            self.new_playlist = "+ नई प्लेलिस्ट"
            self.del_playlist = "🗑 प्लेलिस्ट हटाएं"
            self.select_playlist_t = "प्लेलिस्ट चुनें"
            self.add_mp3 = "MP3 जोड़ें"
            self.download_from_YT = "वेब से डाउनलोड करें"
            self.del_from_list = "ट्रैक हटाएं"
            self.track_not_selected = "कोई ट्रैक चयनित नहीं है"
            self.settings_t = "⚙️ सेटिंग्स"
            self.select_playlist_and_track = "शुरू करने के लिए प्लेलिस्ट और ट्रैक चुनें"
            self.new_playlist_nop = "नई प्लेलिस्ट"
            self.enter_playlist_name = "प्लेलिस्ट का नाम दर्ज करें:"
            self.warning = "चेतावनी"
            self.playlist_already_exists = "यह प्लेलिस्ट पहले से मौजूद है"
            self.error = "त्रुटि"
            self.cant_delete_main = "मुख्य सूची को हटाया नहीं जा सकता"
            self.deleting = "हटाया जा रहा है"
            self.delete_playlist_t = "प्लेलिस्ट हटाएं"
            self.file_not_found = "फ़ाइल नहीं मिली (संभवतः डिस्क से हटाई गई)"
            self.track_deleted = "ट्रैक हटाया गया"
            self.file_no_longer_exists = "फ़ाइल अब निर्दिष्ट पथ पर मौजूद नहीं है।"
            self.select_track = "ट्रैक चुनें"
            self.playback = "प्लेबैक:"
            self.playback_on_pause = "पॉज़ पर प्लेबैक:"
            self.playlist_ended = "प्लेलिस्ट समाप्त हो गई"
            self.playback_stopped = "प्लेबैक रोक दिया गया"
            self.settings_op = "सेटिंग्स"
            self.design_theme = "डिज़ाइन थीम:"
            self.volum = "🔊 वॉल्यूम:"
            self.open_download_folder = "डाउनलोड फ़ोल्डर खोलें"
            self.tutorial = "ट्यूटोरियल"
            self.developerss = "डेवलपर्स:"
            self.tutorial_does_not_exists = "ट्यूटोरियल वर्तमान में उपलब्ध नहीं है।"
            self.supported_links = "समर्थित लिंक: YT, Newgrounds, Soundcloud"
            self.track_loading = "⏳ ट्रैक लोड हो रहा है..."
            self.done = "✅ पूरा हुआ"
            self.lang = "भाषा:"
            self.click_stop_then_select = "स्टॉप पर क्लिक करें, फिर नया ट्रैक चुनें"
            self.shuffle_text = "शफ़ल"
            self.stop_loading = "डाउनलोड रोकें"
            self.loading_stopped = "लोडिंग रोक दी गई"
            self.loop_text = "दोहराएँ"
            self.del_loop_then_select = "दोहराना बंद करें, फिर नया ट्रैक चुनें"
            self.dont_repeat = "दोहराएँ नहीं"
            self.show_tooltip_text = "स्लाइडर टिप दिखाएं"
            self.are_you_sure_delete_track = "क्या आप वाकई इस ट्रैक को हटाना चाहते हैं?"
            self.rename_text = "नाम बदलें"
            self.renaming_text = "नाम बदला जा रहा है"
            self.new_name = "नया नाम:"
            self.track_url_t = "ट्रैक URL"
            self.source_url_t = "स्रोत (URL):"
            self.open_in_browser_t = "ब्राउज़र में खोलें"
            self.copy_t = "कॉपी करें"
            self.copied_t = "कॉपी हो गया!"
        elif self.current_lang == "한국인":  # korean
            self.playlists_t = "플레이리스트"
            self.new_playlist = "+ 새 플레이리스트"
            self.del_playlist = "🗑 플레이리스트 삭제"
            self.select_playlist_t = "플레이리스트 선택"
            self.add_mp3 = "MP3 추가"
            self.download_from_YT = "웹에서 다운로드"
            self.del_from_list = "트랙 삭제"
            self.track_not_selected = "트랙이 선택되지 않았습니다"
            self.settings_t = "⚙️ 설정"
            self.select_playlist_and_track = "재생하려면 플레이리스트와 트랙을 선택하세요"
            self.new_playlist_nop = "새 플레이리스트"
            self.enter_playlist_name = "플레이리스트 이름을 입력하세요:"
            self.warning = "경고"
            self.playlist_already_exists = "이 플레이리스트는 이미 존재합니다"
            self.error = "오류"
            self.cant_delete_main = "기본 목록은 삭제할 수 없습니다"
            self.deleting = "삭제 중"
            self.delete_playlist_t = "플레이리스트 삭제"
            self.file_not_found = "파일을 찾을 수 없습니다 (디스크에서 삭제되었을 수 있음)"
            self.track_deleted = "트랙이 삭제되었습니다"
            self.file_no_longer_exists = "파일이 지정된 경로에 더 이상 존재하지 않습니다."
            self.select_track = "트랙 선택"
            self.playback = "재생:"
            self.playback_on_pause = "일시정지 중 재생:"
            self.playlist_ended = "플레이리스트가 끝났습니다"
            self.playback_stopped = "재생이 중지되었습니다"
            self.settings_op = "설정"
            self.design_theme = "디자인 테마:"
            self.volum = "🔊 볼륨:"
            self.open_download_folder = "다운로드 폴더 열기"
            self.tutorial = "튜토리얼"
            self.developerss = "개발자:"
            self.tutorial_does_not_exists = "튜토리얼이 현재 존재하지 않습니다."
            self.supported_links = "지원 링크: YT, Newgrounds, Soundcloud"
            self.track_loading = "⏳ 트랙 로딩 중..."
            self.done = "✅ 완료"
            self.lang = "언어:"
            self.click_stop_then_select = "중지를 누른 후 새 트랙을 선택하세요"
            self.shuffle_text = "셔플"
            self.stop_loading = "다운로드 중지"
            self.loading_stopped = "로딩이 중지되었습니다"
            self.loop_text = "반복"
            self.del_loop_then_select = "반복을 끈 후 새 트랙을 선택하세요"
            self.dont_repeat = "반복 안 함"
            self.show_tooltip_text = "슬라이더 팁 표시"
            self.are_you_sure_delete_track = "이 트랙을 삭제하시겠습니까?"
            self.rename_text = "이름 변경"
            self.renaming_text = "이름 변경 중"
            self.new_name = "새 이름:"
            self.track_url_t = "트랙 URL"
            self.source_url_t = "출처 (URL):"
            self.open_in_browser_t = "브라우저에서 열기"
            self.copy_t = "복사"
            self.copied_t = "복사됨!"
        elif self.current_lang == "ελληνικά":  # greek
            self.playlists_t = "Λίστες αναπαραγωγής"
            self.new_playlist = "+ Νέα λίστα αναπαραγωγής"
            self.del_playlist = "🗑 Διαγραφή λίστας αναπαραγωγής"
            self.select_playlist_t = "Επιλογή λίστας αναπαραγωγής"
            self.add_mp3 = "Προσθήκη MP3"
            self.download_from_YT = "Λήψη από το διαδίκτυο"
            self.del_from_list = "Διαγραφή κομματιού"
            self.track_not_selected = "Δεν έχει επιλεγεί κομμάτι"
            self.settings_t = "⚙️ Ρυθμίσεις"
            self.select_playlist_and_track = "Επιλέξτε λίστα και κομμάτι για αναπαραγωγή"
            self.new_playlist_nop = "Νέα λίστα αναπαραγωγής"
            self.enter_playlist_name = "Εισάγετε όνομα λίστας:"
            self.warning = "Προειδοποίηση"
            self.playlist_already_exists = "Αυτή η λίστα υπάρχει ήδη"
            self.error = "Σφάλμα"
            self.cant_delete_main = "Δεν μπορείτε να διαγράψετε την κύρια λίστα"
            self.deleting = "Διαγράφεται"
            self.delete_playlist_t = "Διαγραφή λίστας αναπαραγωγής"
            self.file_not_found = "Το αρχείο δεν βρέθηκε (πιθανόν διαγράφηκε από τον δίσκο)"
            self.track_deleted = "Το κομμάτι διαγράφηκε"
            self.file_no_longer_exists = "Το αρχείο δεν υπάρχει πλέον στη συγκεκριμένη διαδρομή."
            self.select_track = "Επιλογή κομματιού"
            self.playback = "Αναπαραγωγή:"
            self.playback_on_pause = "Αναπαραγωγή σε παύση:"
            self.playlist_ended = "Η λίστα ολοκληρώθηκε"
            self.playback_stopped = "Η αναπαραγωγή σταμάτησε"
            self.settings_op = "Ρυθμίσεις"
            self.design_theme = "Θέμα σχεδίασης:"
            self.volum = "🔊 Ένταση:"
            self.open_download_folder = "Άνοιγμα φακέλου λήψεων"
            self.tutorial = "Οδηγός"
            self.developerss = "Προγραμματιστές:"
            self.tutorial_does_not_exists = "Ο οδηγός δεν υπάρχει προς το παρόν."
            self.supported_links = "Υποστηριζόμενοι σύνδεσμοι: YT, Newgrounds, Soundcloud"
            self.track_loading = "⏳ Φόρτωση κομματιού..."
            self.done = "✅ Ολοκληρώθηκε"
            self.lang = "Γλώσσα:"
            self.click_stop_then_select = "Πατήστε διακοπή και μετά επιλέξτε νέο κομμάτι"
            self.shuffle_text = "Τυχαία αναπαραγωγή"
            self.stop_loading = "Διακοπή λήψης"
            self.loading_stopped = "Η φόρτωση σταμάτησε"
            self.loop_text = "Επανάληψη"
            self.del_loop_then_select = "Απενεργοποιήστε την επανάληψη και επιλέξτε νέο κομμάτι"
            self.dont_repeat = "Χωρίς επανάληψη"
            self.show_tooltip_text = "Εμφάνιση συμβουλής ολισθητήρα"
            self.are_you_sure_delete_track = "Είστε σίγουροι ότι θέλετε να διαγράψετε αυτό το κομμάτι;"
            self.rename_text = "Μετονομασία"
            self.renaming_text = "Μετονομασία σε εξέλιξη"
            self.new_name = "Νέο όνομα:"
            self.track_url_t = "URL κομματιού"
            self.source_url_t = "Πηγή (URL):"
            self.open_in_browser_t = "Άνοιγμα στον browser"
            self.copy_t = "Αντιγραφή"
            self.copied_t = "Αντιγράφηκε!"
        elif self.current_lang == "عربي":  # arabic
            self.playlists_t = "قوائم التشغيل"
            self.new_playlist = "+ قائمة تشغيل جديدة"
            self.del_playlist = "🗑 حذف قائمة التشغيل"
            self.select_playlist_t = "اختر قائمة تشغيل"
            self.add_mp3 = "إضافة MP3"
            self.download_from_YT = "تنزيل من الويب"
            self.del_from_list = "حذف المقطع"
            self.track_not_selected = "لم يتم اختيار مقطع"
            self.settings_t = "⚙️ الإعدادات"
            self.select_playlist_and_track = "اختر قائمة تشغيل ومقطع للبدء"
            self.new_playlist_nop = "قائمة تشغيل جديدة"
            self.enter_playlist_name = "أدخل اسم قائمة التشغيل:"
            self.warning = "تحذير"
            self.playlist_already_exists = "قائمة التشغيل هذه موجودة بالفعل"
            self.error = "خطأ"
            self.cant_delete_main = "لا يمكن حذف القائمة الرئيسية"
            self.deleting = "جارٍ الحذف"
            self.delete_playlist_t = "حذف قائمة التشغيل"
            self.file_not_found = "لم يتم العثور على الملف (ربما تم حذفه من القرص)"
            self.track_deleted = "تم حذف المقطع"
            self.file_no_longer_exists = "الملف لم يعد موجودًا في المسار المحدد."
            self.select_track = "اختر مقطع"
            self.playback = "التشغيل:"
            self.playback_on_pause = "التشغيل أثناء الإيقاف المؤقت:"
            self.playlist_ended = "انتهت قائمة التشغيل"
            self.playback_stopped = "تم إيقاف التشغيل"
            self.settings_op = "الإعدادات"
            self.design_theme = "سمة التصميم:"
            self.volum = "🔊 مستوى الصوت:"
            self.open_download_folder = "فتح مجلد التنزيلات"
            self.tutorial = "الدليل"
            self.developerss = "المطورون:"
            self.tutorial_does_not_exists = "الدليل غير متوفر حاليًا."
            self.supported_links = "الروابط المدعومة: YT، Newgrounds، Soundcloud"
            self.track_loading = "⏳ جارٍ تحميل المقطع..."
            self.done = "✅ تم"
            self.lang = "اللغة:"
            self.click_stop_then_select = "اضغط إيقاف ثم اختر مقطعًا جديدًا"
            self.shuffle_text = "تشغيل عشوائي"
            self.stop_loading = "إيقاف التنزيل"
            self.loading_stopped = "تم إيقاف التحميل"
            self.loop_text = "تكرار"
            self.del_loop_then_select = "أوقف التكرار ثم اختر مقطعًا جديدًا"
            self.dont_repeat = "بدون تكرار"
            self.show_tooltip_text = "إظهار تلميح شريط التمرير"
            self.are_you_sure_delete_track = "هل أنت متأكد أنك تريد حذف هذا المقطع؟"
            self.rename_text = "إعادة تسمية"
            self.renaming_text = "جارٍ إعادة التسمية"
            self.new_name = "اسم جديد:"
            self.track_url_t = "رابط المسار"
            self.source_url_t = "المصدر (URL):"
            self.open_in_browser_t = "فتح في المتصفح"
            self.copy_t = "نسخ"
            self.copied_t = "تم النسخ!"
        self.update_ui()

    def update_ui(self):
        self.lbl_logo.configure(text=self.playlists_t)

        self.btn_new_playlist.configure(text=self.new_playlist)

        self.btn_del_playlist.configure(text=self.del_playlist)

        self.update_playlist_menu()

        self.lbl_pl_name.configure(text=self.select_playlist_t)

        self.btn_add_local.configure(text=self.add_mp3)

        self.btn_add_yt.configure(text=self.download_from_YT)

        self.btn_shuffle.configure(text=self.shuffle_text)

        self.btn_set_loop.configure(text=self.loop_text)

        if self.current_track_path:
            self.update_info_label()
        else:
            self.info_label.configure(text=self.track_not_selected)

        self.settings_btn.configure(text=self.settings_t)

        self.status_bar.configure(text=self.select_playlist_and_track)

    def update_settings(self):
        self.theme_label.configure(text=self.design_theme)

        self.lbl_volume.configure(text=f"{self.volum}")

        self.open_downloads_folder_btn.configure(text=self.open_download_folder)

        self.open_tutorial_btn.configure(text=self.tutorial)

        self.lang_label.configure(text=self.lang)

        self.developers.configure(text=self.developerss)

    def add_playlist(self):
        name = simpledialog.askstring(f"{self.new_playlist_nop}", f"{self.enter_playlist_name}")
        if name:
            if name in self.playlists:
                messagebox.showwarning(f"{self.warning}", f"{self.playlist_already_exists}")
            else:
                self.playlists[name] = []
                self.save_data()
                self.update_playlist_menu()

    def delete_playlist(self):
        if self.current_playlist_name == "All":
            messagebox.showerror(f"{self.error}", f"{self.cant_delete_main}")
            return

        if messagebox.askyesno(f"{self.deleting}", f"{self.delete_playlist} '{self.current_playlist_name}'?"):
            del self.playlists[self.current_playlist_name]
            self.current_playlist_name = "All"
            self.save_data()
            self.update_playlist_menu()
            self.select_playlist("All")

    def update_playlist_menu(self):
        for widget in self.playlist_frame.winfo_children():
            widget.destroy()
        for name in self.playlists.keys():
            is_active = (name == self.current_playlist_name)
            btn = ctk.CTkButton(self.playlist_frame, text=name,
                                fg_color="blue" if is_active else "transparent",
                                anchor="w", command=lambda n=name: self.select_playlist(n))
            btn.pack(fill="x", pady=2)

    def select_playlist(self, name):
        self.current_playlist_name = name
        self.lbl_pl_name.configure(text=f"{self.playlists_t}: {name}")
        self.update_playlist_menu()
        self.refresh_tracks_display()

    def refresh_tracks_display(self):
        for w in self.tracks_listbox.winfo_children(): w.destroy()

        for path in self.playlists.get(self.current_playlist_name, []):
            track_row = ctk.CTkFrame(self.tracks_listbox, fg_color="transparent")
            track_row.pack(fill="x", pady=2, padx=5)

            url = self.links.get(path)

            btn = ctk.CTkButton(
                track_row,
                text=f"🎵 {os.path.basename(path)}",
                anchor="w",
                fg_color="#333",
                command=lambda p=path: self.set_active_track(p)
            )
            btn.pack(side="left", fill="x", expand=True, padx=(0, 2))

            del_btn = ctk.CTkButton(
                track_row, text="🗑", width=30, fg_color="#333",
                hover_color="#444",
                command=lambda p=path: self.delete_current_track(p)
            )
            del_btn.pack(side="right", padx=(0, 2))

            ren_btn = ctk.CTkButton(
                track_row, text="✏️", width=30, fg_color="#333",
                hover_color="#444",
                command=lambda p=path: self.rename_track(p)
            )
            ren_btn.pack(side="right", padx=(0, 2))

            if url:
                link_btn = ctk.CTkButton(
                    track_row, text="🔗", width=30, fg_color="#333",
                    hover_color="#444",
                    command=lambda u=url: self.open_info_window(u)
                )
                link_btn.pack(side="right", padx=(0, 2))


    def open_info_window(self, url):
        self.info_window = ctk.CTkToplevel(self)
        self.info_window.title(f"{self.track_url_t}")
        self.info_window.geometry("450x180")
        self.info_window.attributes("-topmost", True)
        self.info_window.resizable(False, False)
        self.info_window.grab_set()

        ctk.CTkLabel(self.info_window, text=self.source_url_t, font=("Arial", 14, "bold")).pack(pady=(20, 5))

        self.url_entry = ctk.CTkEntry(self.info_window, width=380)
        self.url_entry.insert(0, url)
        self.url_entry.configure(state="readonly")  # Только для чтения, но можно выделить
        self.url_entry.pack(pady=10)

        self.btn_frame = ctk.CTkFrame(self.info_window, fg_color="transparent")
        self.btn_frame.pack(pady=10)

        self.open_b_btn = ctk.CTkButton(self.btn_frame, text=self.open_in_browser_t, width=150, command=lambda: webbrowser.open(url))
        self.open_b_btn.pack(side="left", padx=5)

        # Кнопка копирования
        self.copy_btn = ctk.CTkButton(self.btn_frame, text=self.copy_t, width=100, fg_color="gray", command=self.copy_link)
        self.copy_btn.pack(side="left", padx=5)

    def copy_link(self):
        self.clipboard_clear()
        self.clipboard_append(self.url_entry.get())
        self.copy_btn.configure(text=self.copied_t, state="disabled")
        self.after(2000, self.update_copy_btn)

    def update_copy_btn(self):
        self.copy_btn.configure(text=self.copy_t, state="enabled")

    def rename_track(self, old_path):
        if not old_path:
            messagebox.showwarning("Afory", f"{self.select_track}")
            return
        old_name = os.path.basename(old_path)
        new_name = simpledialog.askstring(f"{self.renaming_text}", f"{self.new_name}", initialvalue=old_name)

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
                self.info_label.configure(text=new_name)

            except OSError as e:
                messagebox.showerror(f"{self.error}", f"Error while renaming: {e}")

    def set_active_track(self, path):
        if self.is_repeat:
            self.info_label.configure(text=self.del_loop_then_select)
            self.info_label.after(2000, self.update_info_label)
        elif self.is_paused:
            self.play_music()
            time.sleep(0.1)
            self.stop_music()
            time.sleep(0.1)
            self.current_track_path = path
            if not os.path.exists(path):
                self.info_label.configure(text=self.file_not_found)
                return
            try:
                audio = MP3(path)
                self.length = int(audio.info.length) * 1000
                self.view_length = self.length // 1000
                self.current_track = os.path.basename(path)
                print(self.current_track)
                self.current_track_name = f"{os.path.basename(path)} | {self.view_length // 60:02d}:{self.view_length % 60:02d}"
                self.current_playlist = self.playlists.get(self.current_playlist_name, [])
                self.current_index = self.current_playlist.index(self.current_track_path)
                self.info_label.configure(text=self.current_track_name)
            except:
                self.info_label.configure(text=f"{os.path.basename(path)}")
            self.play_music()
        elif self.is_played:
            self.stop_music()
            time.sleep(0.1)
            self.current_track_path = path
            if not os.path.exists(path):
                self.info_label.configure(text=self.file_not_found)
                return
            try:
                audio = MP3(path)
                self.length = int(audio.info.length) * 1000
                self.view_length = self.length // 1000
                self.current_track = os.path.basename(path)
                print(self.current_track)
                self.current_track_name = f"{os.path.basename(path)} | {self.view_length // 60:02d}:{self.view_length % 60:02d}"
                self.current_playlist = self.playlists.get(self.current_playlist_name, [])
                self.current_index = self.current_playlist.index(self.current_track_path)
                self.info_label.configure(text=self.current_track_name)
            except:
                self.info_label.configure(text=f"{os.path.basename(path)}")
            self.play_music()
        elif not self.is_played:
            self.current_track_path = path
            if not os.path.exists(path):
                self.info_label.configure(text=self.file_not_found)
                return
            try:
                audio = MP3(path)
                self.length = int(audio.info.length) * 1000
                self.view_length = self.length // 1000
                self.current_track = os.path.basename(path)
                print(self.current_track)
                self.current_track_name = f"{os.path.basename(path)} | {self.view_length // 60:02d}:{self.view_length % 60:02d}"
                self.current_playlist = self.playlists.get(self.current_playlist_name, [])
                self.current_index = self.current_playlist.index(self.current_track_path)
                self.info_label.configure(text=self.current_track_name)
            except:
                self.info_label.configure(text=f"{os.path.basename(path)}")

    def toggle_play_pause(self, event=None):
        if self.current_track_path:
            if pygame.mixer.music.get_busy() and not self.is_paused:
                self.pause_music()
            else:
                self.play_music()

    def update_info_label(self):
        self.info_label.configure(text=self.current_track_name)

    def add_local_file(self):
        paths = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.mp3")])
        if paths:
            for p in paths:
                if p.lower().endswith(".mp3"):
                    self.playlists[self.current_playlist_name].append(p)
            self.save_data()
            self.refresh_tracks_display()

    def delete_current_track(self, path):
        self.current_track = os.path.basename(path)
        if path in self.playlists[self.current_playlist_name] and messagebox.askyesno(f"{self.deleting}", f"{self.are_you_sure_delete_track}\n{self.current_track}"):
            self.playlists[self.current_playlist_name].remove(path)
            os.remove(path)
            self.current_track_path = None
            self.save_data()
            self.refresh_tracks_display()
            self.info_label.configure(text=self.track_deleted)
            self.after(1500, self.update_info_label)

    def shuffle_current_playlist(self):
        if self.is_stopped:
            self.current_playlist = self.playlists[self.current_playlist_name]
            random.shuffle(self.current_playlist)
            self.refresh_tracks_display()
            self.current_track_path = None
            self.info_label.configure(text=self.track_not_selected)
        else:
            self.info_label.configure(text=self.click_stop_then_select)
            self.info_label.after(2000, self.update_info_label)

    def move_track(self, direction):
        if not self.current_track_path: return

        self.current_playlist = self.playlists[self.current_playlist_name]
        idx = self.current_playlist.index(self.current_track_path)
        new_idx = idx + direction

        if 0 <= new_idx < len(self.current_playlist):

            self.current_playlist[idx], self.current_playlist[new_idx] = self.current_playlist[new_idx], self.current_playlist[idx]
            self.save_data()
            self.refresh_tracks_display()
            self.info_label.configure(text=self.done)
            self.after(2000, self.update_info_label)

    def set_previous(self):
        def previous_task():
            try:
                self.next_track = self.current_playlist[self.current_index - 1]
                print(self.next_track)
                self.stop_music()
                time.sleep(0.1)
                self.set_active_track(self.next_track)
                time.sleep(0.1)
                self.play_music()
            except Exception as e:
                if e == "IndexError: list index out of range":
                    messagebox.showerror(f"{self.error}", f"No more tracks available")
        threading.Thread(target=previous_task, daemon=True).start()

    def set_next(self):
        def next_task():
            try:
                self.next_track = self.current_playlist[self.current_index + 1]
                print(self.next_track)
                self.stop_music()
                time.sleep(0.1)
                self.set_active_track(self.next_track)
                time.sleep(0.1)
                self.play_music()
                print("next")
            except Exception as e:
                if e == "IndexError: list index out of range":
                    messagebox.showerror(f"{self.error}", f"No more tracks available")
        threading.Thread(target=next_task, daemon=True).start()

    def set_track_loop(self):
        if self.current_track_path == None:
            messagebox.showwarning("Audos", f"{self.select_track}")
            return
        self.loop = True
        self.btn_set_loop.configure(text=self.dont_repeat, command=self.del_track_loop)

    def del_track_loop(self):
        self.loop = False
        self.is_repeat = False
        self.btn_set_loop.configure(text=self.loop_text, command=self.set_track_loop)

    def play_music(self):
        if self.is_paused == False:
            if self.current_track_path:
                if not os.path.exists(self.current_track_path):
                    messagebox.showerror(f"{self.error}", f"{self.file_no_longer_exists}")
                    return
                pygame.mixer.music.load(self.current_track_path)
                pygame.mixer.music.play()
                self.is_played = True
                self.is_stopped = False
                self.btn_play.configure(state="disabled")
                self.btn_stop.configure(state="enabled")
                self.btn_pause.configure(state="enabled")
            else:
                messagebox.showwarning("Afory", f"{self.select_track}")
        elif self.is_paused == True:
            self.is_played = True
            self.is_stopped = False
            self.btn_play.configure(state="disabled")
            self.btn_stop.configure(state="enabled")
            self.btn_pause.configure(state="enabled")
            pygame.mixer.music.unpause()
            self.is_paused = False

    def start_loop(self):
        while self.run:

            self.current_length = pygame.mixer.music.get_pos() + self.current_music_num
            self.current_view_length = self.current_length // 1000
            self.seekbar.set(self.current_length / self.length * 100)

            if self.is_stopped:
                self.is_played = False
            elif self.is_paused:
                self.status_bar.configure(
                    text=f"{self.playback_on_pause} {self.current_view_length // 60:02d}:{self.current_view_length % 60:02d} / {self.view_length // 60:02d}:{self.view_length % 60:02d}")
            elif not pygame.mixer.music.get_busy():
                self.status_bar.configure(
                    text=f"{self.playback} {self.current_view_length // 60:02d}:{self.current_view_length % 60:02d} / {self.view_length // 60:02d}:{self.view_length % 60:02d}")
                print("next play")
                self.play_next_track()
            elif not self.current_length == self.length:
                self.status_bar.configure(
                    text=f"{self.playback} {self.current_view_length // 60:02d}:{self.current_view_length % 60:02d} / {self.view_length // 60:02d}:{self.view_length % 60:02d}")
            time.sleep(0.05)

    def set_music_to_current_slide_pos(self, value):
        if self.is_stopped:
            return
        elif self.is_paused:
            return
        else:
            self.one_unit_length = (self.length / 100)
            self.current_music_num = (int(self.one_unit_length * value))
            pygame.mixer.music.play(start=self.current_music_num // 1000)

    def on_slider_hover(self, event):
        if self.view_length > 0:
            width = self.seekbar.winfo_width()
            mouse_x = event.x
            mouse_x = max(0, min(mouse_x, width))

            percent = mouse_x / width
            preview_time = percent * self.view_length
            time_str = time.strftime('%M:%S', time.gmtime(preview_time))

            abs_x = self.seekbar.winfo_rootx() + mouse_x
            abs_y = self.seekbar.winfo_rooty()

            if not self.tooltip.tip_window:
                self.tooltip.show_tip(time_str, abs_x, abs_y)
            else:
                self.tooltip.label.configure(text=time_str)
                self.tooltip.update_pos(abs_x, abs_y)

    def play_next_track(self):
        print("play-next-track")
        if not self.current_playlist: return
        if self.loop:
            next_track = self.current_playlist[self.current_index + 0]
            print(next_track)
            self.current_music_num = 0
            self.current_length = 0
            self.set_active_track(next_track)
            self.play_music()
            print("done")
        else:
            self.max_index = (len(self.current_playlist))
            print(self.current_index, self.max_index)
            if self.current_index + 1 == self.max_index:
                self.status_bar.configure(text=self.playlist_ended)
                self.btn_play.configure(state="enabled")
                self.btn_pause.configure(state="disabled")
                self.btn_stop.configure(state="disabled")
                self.info_label.configure(text=self.track_not_selected)
                self.is_stopped = True
                self.current_music_num = 0
                self.current_length = 0
                self.current_track_path = None
            else:
                next_track = self.current_playlist[self.current_index + 1]
                print(next_track)
                self.current_music_num = 0
                self.current_length = 0
                self.set_active_track(next_track)
                self.play_music()
                print("done")

    def stop_music(self):
        self.is_stopped = True
        pygame.mixer.music.stop()
        self.status_bar.configure(text=self.playback_stopped)
        self.btn_play.configure(state="enabled")
        self.btn_stop.configure(state="disabled")
        self.btn_pause.configure(state="disabled")
        self.current_length = 0
        self.current_music_num = 0
        print("stop")

    def pause_music(self):
        pygame.mixer.music.pause()
        self.btn_play.configure(state="enabled")
        self.btn_stop.configure(state="disabled")
        self.btn_pause.configure(state="disabled")
        self.is_paused = True
        print("pause")

    def settings_open(self):
        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.geometry("450x600")
        self.settings_window.title(f"{self.settings_op}")
        self.settings_window.resizable(width=False, height=False)
        self.settings_window.transient(self)
        self.settings_window.grab_set()

        self.theme_label = ctk.CTkLabel(self.settings_window, text=self.design_theme, font=("Arial", 14))
        self.theme_label.pack(padx=20, pady=(10, 5))

        self.theme_menu = ctk.CTkOptionMenu(
            self.settings_window,
            values=["Dark", "Light", "System"],
            command=self.change_theme
        )
        self.theme_menu.pack(padx=20, pady=(0, 20))

        self.theme_menu.set(self.settings.get("theme", "Dark"))

        self.volume_frame = ctk.CTkFrame(self.settings_window, fg_color="transparent")
        self.volume_frame.pack(pady=10)

        current_vol = self.settings.get("volume", 0.7)

        self.lbl_volume = ctk.CTkLabel(self.volume_frame, text=f"{self.volum} {int(current_vol * 100)}%")
        self.lbl_volume.pack(side="left", padx=10)

        self.volume_slider = ctk.CTkSlider(self.volume_frame, from_=0, to=1, command=self.change_volume)
        self.volume_slider.pack(side="left", padx=10)
        self.volume_slider.set(current_vol)
        pygame.mixer.music.set_volume(current_vol)

        self.tooltip_switch = ctk.CTkSwitch(self.settings_window, text=self.show_tooltip_text, command=self.switch_tooltip_value)
        self.tooltip_switch.pack(pady=5)

        if self.settings.get("tooltip") == True:
            self.tooltip_switch.select()
        elif self.settings.get("tooltip") == False:
            self.tooltip_switch.deselect()

        self.open_downloads_folder_btn = ctk.CTkButton(self.settings_window, text=self.open_download_folder, font=("Arial", 14), command=self.open_downloads_folder)
        self.open_downloads_folder_btn.pack(pady=5)

        self.open_stdout = ctk.CTkButton(self.settings_window, text="Open stdout", font=("Arial", 14), command=self.open_stdout_log)
        self.open_stdout.pack(pady=5)

        self.open_tutorial_btn = ctk.CTkButton(self.settings_window, text=self.tutorial, font=("Arial", 14), command=self.open_tutorial)
        self.open_tutorial_btn.pack(pady=5)

        self.lang_label = ctk.CTkLabel(self.settings_window, text=self.lang, font=("Arial", 15))
        self.lang_label.pack()

        self.lang_selecting = ctk.CTkOptionMenu(self.settings_window, values=["English", "Русский", "Deutsch", "ქართული", "español", "Українська", "Қазақ", "Polski", "Français", "日本語", "中國人", "Italiano", "Azərbaycan dili", "беларуская", "Türkçe", "Татар (кириллица)", "हिंदी", "한국인", "ελληνικά", "عربي"], command=self.change_lang)
        self.lang_selecting.pack(pady=5)

        self.lang_selecting.set(self.current_lang)

        self.developers = ctk.CTkLabel(self.settings_window, text=self.developerss, font=("Arial", 16))
        self.developers.pack(pady=10)

        self.dev1_tuseloryy = ctk.CTkLabel(self.settings_window, text="Made by Tuseloryy", font=("Arial", 13))
        self.dev1_tuseloryy.pack()

        self.dev1_github_open_btn = ctk.CTkButton(self.settings_window, text="Github", font=("Arial", 14), command=self.open_github_dev1)
        self.dev1_github_open_btn.pack(pady=5)

        self.dev1_yt_open_btn = ctk.CTkButton(self.settings_window, text="Youtube", font=("Arial", 14), command=self.open_yt_dev1, fg_color="Red")
        self.dev1_yt_open_btn.pack(pady=5)

        self.dev1_tt_open_btn = ctk.CTkButton(self.settings_window, text="TikTok", font=("Arial", 14), command=self.open_tt_dev1, fg_color="Black")
        self.dev1_tt_open_btn.pack(pady=5)

        self.verison = ctk.CTkLabel(self.settings_window, text="Version: 2026.5.1", font=("Arial", 16))
        self.verison.pack(pady=10)

    def change_theme(self, new_theme):
        ctk.set_appearance_mode(new_theme)
        self.settings["theme"] = new_theme
        self.save_settings()

    def change_volume(self, value):
        pygame.mixer.music.set_volume(value)
        self.lbl_volume.configure(text=f"{self.volum} {int(value * 100)}%")
        self.settings["volume"] = value
        self.save_settings()

    def switch_tooltip_value(self):
        self.switch_value = self.tooltip_switch.get()

        if self.switch_value == 0:
            self.settings["tooltip"] = False
            self.seekbar.unbind("<Motion>")
            self.seekbar.unbind("<Leave>")
            print("off")
        if self.switch_value == 1:
            self.settings["tooltip"] = True
            self.seekbar.bind("<Motion>", self.on_slider_hover)
            self.seekbar.bind("<Leave>", lambda e: self.tooltip.hide_tip())
            print("on")
        self.save_settings()

    def change_lang(self, new_lang):
        self.settings["language"] = new_lang
        self.save_settings()
        self.apply_lang()
        self.update_settings()

    def open_downloads_folder(self):
        subprocess.run(["open", f"/Users/{username}/Afory"])

    def open_stdout_log(self):
        self.stdout_window = ctk.CTkToplevel(self)
        self.stdout_window.geometry("500x500")
        self.stdout_window.title("stdout")

        self.console_textbox = ctk.CTkTextbox(self.stdout_window, height=460, width=480, font=("Arial", 13))
        self.console_textbox.pack(padx=20, pady=10)
        self.console_textbox.configure(state="disabled")

        if self.old_content:
            self.console_textbox.insert("1.0", self.old_content)

        if self.start_update == True:
            self.update_console_output()
            self.start_update = False

    def open_tutorial(self):
        messagebox.showerror(f"{self.error}", f"{self.tutorial_does_not_exists}")

    def open_github_dev1(self):
        webbrowser.open("https://github.com/Tuseloryy")

    def open_yt_dev1(self):
        webbrowser.open("https://www.youtube.com/@Tuseloryy")

    def open_tt_dev1(self):
        webbrowser.open("https://www.tiktok.com/@tuselmark")

    def stop_loading_yt(self):
        self.stop_event.set()

        self.info_label.configure(text=self.loading_stopped)
        self.btn_add_yt.configure(
            text=self.download_from_YT,
            command=self.download_youtube
        )
        self.after(3000, self.update_info_label)

    def download_youtube(self):
        url = simpledialog.askstring("Web", f"{self.supported_links}")
        if not url:
            return

        self.stop_event.clear()

        def progress_hook(d):
            if self.stop_event.is_set():
                raise Exception("")

        def task():
            try:
                self.info_label.configure(text=self.track_loading)
                self.btn_add_yt.configure(
                    text=self.stop_loading,
                    command=self.stop_loading_yt
                )

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'ffmpeg_location': resource_path("ffmpeg/ffmpeg"),
                    'outtmpl': f'/Users/{username}/Afory/downloads/%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [progress_hook],
                    'noplaylist': True
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if self.stop_event.is_set():
                        return

                    final_mp3 = os.path.abspath(
                        ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"
                    )

                    self.playlists[self.current_playlist_name].append(final_mp3)
                    self.links[final_mp3] = url
                    self.save_data()
                    self.save_links()

                self.save_data()
                self.after(0, self.refresh_tracks_display)

                self.info_label.configure(text=self.done)

            except Exception as e:
                messagebox.showerror("Error", str(e))

            finally:
                self.btn_add_yt.configure(
                    text=self.download_from_YT,
                    command=self.download_youtube
                )
                self.info_label.after(3000, self.update_info_label)

        threading.Thread(target=task, daemon=True).start()

if __name__ == "__main__":
    try:
        username = getpass.getuser()
    except Exception as e:
        username = simpledialog.askstring("Warning", f"Program tried to get your username, but failed with error:\n'{e}'\n"
                                     f"We need your username to create folders and store your playlists and tracks.\n"
                                     f"Please, provide username below\n"
                                     f"(you can see your username by typing whoami in terminal)")
        if not username:
            quit()

    try:
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

    except Exception as e:
        messagebox.showerror("Error", f"Program got error while creating folders: {e} \n"
                           f"Please, fix this error or create folders by yourself.")
        quit()
    finally:
        app = Main()
        app.mainloop()

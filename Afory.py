
# Made by Tuseloryy
# My social: https://tuseloryy.card.co
# Python 3.12
# For 2026.5.2.1
# SOURCE CODE:

import tkinter as tk
import customtkinter as ctk
import pygame
import yt_dlp
import os
import sys
import io
import threading
import json
import getpass
import subprocess
import webbrowser
import time
import random
from pynput import keyboard
from PIL import Image
from mutagen.mp3 import MP3
from tkinter import filedialog, messagebox, simpledialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

console_out = io.StringIO()
sys.stdout = console_out

print("pygame 2.6.1 (SDL 2.28.4, Python 3.12.5)")
print("Hello from the pygame community. https://www.pygame.org/contribute.html")


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
        self.geometry("1000x650")
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

        keyboard.GlobalHotKeys({
            '<alt>+<space>': self.toggle_play_pause,
            '<alt>+<right>': lambda: self.after(0, self.set_next),
            '<alt>+<left>': lambda: self.after(0, self.set_previous),
            '<alt>+<up>': lambda: self.adjust_volume_step(0.1),
            '<alt>+<down>': lambda: self.adjust_volume_step(-0.1)
        }).start()

        self.delete_btn_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/bin.png")),
                                            dark_image=Image.open(resource_path("assets/icons/bin.png")), size=(20, 20))
        self.rename_btn_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/pen.png")),
                                            dark_image=Image.open(resource_path("assets/icons/pen.png")), size=(20, 20))
        self.link_btn_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/link.png")),
                                          dark_image=Image.open(resource_path("assets/icons/link.png")), size=(16, 16))
        self.play_btn_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/play-button.png")),
                                          dark_image=Image.open(resource_path("assets/icons/play-button.png")), size=(20, 20))
        self.pause_btn_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/pause-button.png")),
                                          dark_image=Image.open(resource_path("assets/icons/pause-button.png")), size=(25, 25))
        self.up_btn_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/arrow-up.png")),
                                          dark_image=Image.open(resource_path("assets/icons/arrow-up.png")), size=(20, 20))
        self.down_btn_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/arrow-down.png")),
                                          dark_image=Image.open(resource_path("assets/icons/arrow-down.png")), size=(20, 20))
        self.left_btn_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/left.png")),
                                          dark_image=Image.open(resource_path("assets/icons/left.png")), size=(23, 23))
        self.right_btn_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/right.png")),
                                          dark_image=Image.open(resource_path("assets/icons/right.png")), size=(23, 23))
        self.settings_btn_icon = ctk.CTkImage(light_image=Image.open(resource_path("assets/icons/settings.png")),
                                          dark_image=Image.open(resource_path("assets/icons/settings.png")), size=(20, 20))

        self.playlists_t = "Playlists"
        self.new_playlist = "+ New Playlist"
        self.del_playlist = "Delete playlist"
        self.select_playlist_t = "Select playlist"
        self.add_mp3 = "Add MP3"
        self.download_from_YT = "Download from YT"
        self.del_from_list = "Delete track"
        self.track_not_selected = "Track not selected"
        self.settings_t = "Settings"
        self.select_playlist_and_track = "Select playlist and track to start"
        self.new_playlist_nop = "New playlist"
        self.enter_playlist_name = "Enter playlist name:"
        self.warning = "Warning"
        self.playlist_already_exists = "This playlisem jlhrbjklrbt already exists"
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
        self.enter_new_name_for_t = "Enter new name for"
        self.renaming_playlist_t = "Rename playlist"
        self.see_keybinds_t = "See keybinds"
        self.keybinds_t = "Keybinds"
        self.first_keybind_t = "alt + arrow right/left: next/previous track"
        self.second_keybind_t = "alt + space: play/pause"
        self.third_keybind_t = "alt + arrow up/down: adjust volume"
        self.works_even_not_in_app_t = "These keybinds works even if you are not in app"
        self.keybinds_note = "You need to access app the accessibility"

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
                                              fg_color="#333", hover_color="#444", image=self.delete_btn_icon,
                                              command=self.delete_playlist)
        self.btn_del_playlist.pack(padx=10, pady=5)

        self.playlist_frame = ctk.CTkScrollableFrame(self.sidebar, label_text=self.playlists_t)
        self.playlist_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.update_playlist_menu()

        self.main_view = ctk.CTkFrame(self, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.lbl_pl_name = ctk.CTkLabel(self.main_view, text=self.select_playlist_t, font=("Arial", 26, "bold"))
        self.lbl_pl_name.pack(pady=10)

        self.tracks_listbox = ctk.CTkScrollableFrame(self.main_view, height=300)
        self.tracks_listbox.pack(padx=10, expand=True, fill="x")

        self.toolbar = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.toolbar.pack(pady=10)

        self.btn_add_local = ctk.CTkButton(self.toolbar, text=self.add_mp3, command=self.add_local_file, fg_color="#68689c", hover_color="#4c4c73")
        self.btn_add_local.pack(padx=2, side="left")

        self.btn_add_yt = ctk.CTkButton(self.toolbar, text=self.download_from_YT, command=self.download_youtube,
                                        fg_color="#68689c", hover_color="#4c4c73")
        self.btn_add_yt.pack(padx=2, side="left")

        self.btn_shuffle = ctk.CTkButton(self.toolbar, text=self.shuffle_text, command=self.shuffle_current_playlist, fg_color="#68689c", hover_color="#4c4c73")
        self.btn_shuffle.pack(padx=2, side="left")

        self.btn_set_loop = ctk.CTkButton(self.toolbar, text=self.loop_text, command=self.set_track_loop, fg_color="#68689c", hover_color="#4c4c73")
        self.btn_set_loop.pack(padx=(2, 20), side="left")

        self.player_controls = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.player_controls.pack(fill="x", pady=10)

        self.info_label = ctk.CTkLabel(self.player_controls, text=self.track_not_selected, font=("Arial", 17))
        self.info_label.pack(pady=5)

        self.playback_btns = ctk.CTkFrame(self.player_controls, fg_color="transparent")
        self.playback_btns.pack(pady=10)

        self.btn_previous = ctk.CTkButton(self.playback_btns, text="", font=("Arial", 16, "bold"), width=45, height=45, image=self.left_btn_icon,
                                          command=self.set_previous, fg_color="#649c99", hover_color="#456e6b",)
        self.btn_previous.grid(row=0, column=1, padx=5)

        self.btn_play_pause = ctk.CTkButton(self.playback_btns, text="", font=("Arial", 16, "bold"), fg_color="#5da858", hover_color="#447d40", image=self.play_btn_icon,
                                      width=80, height=45, command=self.toggle_play_pause)
        self.btn_play_pause.grid(row=0, column=2, padx=5)

        self.btn_next = ctk.CTkButton(self.playback_btns, text="", font=("Arial", 16, "bold"), width=45, height=45, image=self.right_btn_icon,
                                      command=self.set_next, fg_color="#649c99", hover_color="#456e6b",)
        self.btn_next.grid(row=0, column=5, padx=5)

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

        self.settings_btn = ctk.CTkButton(self.sidebar, text=self.settings_t, font=("Arial", 14), image=self.settings_btn_icon, command=self.settings_open)
        self.settings_btn.pack(pady=10)

        self.status_bar = ctk.CTkLabel(self.player_controls, text=self.select_playlist_and_track, font=("Arial", 16))
        self.status_bar.pack()

        threading.Thread(target=self.start_loop, daemon=True).start()

    def adjust_volume_step(self, step):
        current_vol = self.settings.get("volume")
        print(current_vol)
        new_vol = current_vol + step
        if new_vol >= 1.0:
            return
        elif new_vol <= 0.0:
            return
        pygame.mixer.music.set_volume(new_vol)
        self.settings["volume"] = new_vol
        self.save_settings()

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

        self.open_keybinds_btn.configure(text=self.see_keybinds_t)

        self.open_tutorial_btn.configure(text=self.tutorial)

        self.lang_label.configure(text=self.lang)

        self.developers.configure(text=self.developerss)

    def add_playlist(self):
        name = ctk.CTkInputDialog(title=self.new_playlist_nop, text=self.enter_playlist_name).get_input()
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
        for w in self.playlist_frame.winfo_children(): w.destroy()

        for name in self.playlists.keys():
            pl_frame = ctk.CTkFrame(self.playlist_frame, fg_color="transparent")
            pl_frame.pack(fill="x", pady=2)

            is_active = (name == self.current_playlist_name)
            btn = ctk.CTkButton(
                pl_frame,
                text=name,
                anchor="w",
                fg_color="#1f538d" if is_active else "#444",
                hover_color="#333",
                command=lambda n=name: self.select_playlist(n)
            )
            btn.pack(side="left", fill="x", expand=True)
            rename_btn = ctk.CTkButton(
                pl_frame, width=25, hover_color="#444",
                text="️", fg_color="#333", image=self.rename_btn_icon,
                command=lambda n=name: self.rename_playlist_dialog(n)
            )
            rename_btn.pack(side="right", padx=(2, 0))

    def rename_playlist_dialog(self, old_name):
        new_name = ctk.CTkInputDialog(text=f"{self.enter_new_name_for_t} '{old_name}':", title=self.renaming_playlist_t).get_input()

        if new_name and new_name != old_name:
            if new_name in self.playlists:
                messagebox.showerror(self.error, self.playlist_already_exists)
                return
            self.playlists[new_name] = self.playlists.pop(old_name)
            if self.current_playlist_name == old_name:
                self.current_playlist_name = new_name
            self.save_data()
            self.update_playlist_menu()
            self.info_label.configure(text=self.done)
            self.after(1500, self.update_info_label)

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

            is_active = (path == self.current_track_path)

            btn = ctk.CTkButton(
                track_row,
                text=f"🎵 {os.path.basename(path)}",
                anchor="w",
                fg_color="#1d598c" if is_active else "#333",
                command=lambda p=path: self.set_active_track(p)
            )
            btn.pack(side="left", fill="x", expand=True, padx=(1, 2))

            move_down_btn = ctk.CTkButton(
                track_row, text="", width=25, fg_color="#333",
                hover_color="#444", image=self.down_btn_icon,
                command=lambda p=path: self.move_track(+1, p)
            )
            move_down_btn.pack(side="right", padx=(0, 2))

            move_up_btn = ctk.CTkButton(
                track_row, text="", width=25, fg_color="#333",
                hover_color="#444", image=self.up_btn_icon,
                command=lambda p=path: self.move_track(-1, p)
            )
            move_up_btn.pack(side="right", padx=(0, 2))

            del_btn = ctk.CTkButton(
                track_row, text="", width=25, fg_color="#333",
                hover_color="#444", image=self.delete_btn_icon,
                command=lambda p=path: self.delete_current_track(p)
            )
            del_btn.pack(side="right", padx=(0, 2))

            ren_btn = ctk.CTkButton(
                track_row, text="", width=25, fg_color="#333",
                hover_color="#444", image=self.rename_btn_icon,
                command=lambda p=path: self.rename_track(p)
            )
            ren_btn.pack(side="right", padx=(0, 2))

            if url:
                link_btn = ctk.CTkButton(
                    track_row, text="", width=25, fg_color="#333",
                    hover_color="#444", image=self.link_btn_icon,
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
        self.url_entry.configure(state="readonly")
        self.url_entry.pack(pady=10)

        self.btn_frame = ctk.CTkFrame(self.info_window, fg_color="transparent")
        self.btn_frame.pack(pady=10)

        self.open_b_btn = ctk.CTkButton(self.btn_frame, text=self.open_in_browser_t, width=150, command=lambda: webbrowser.open(url))
        self.open_b_btn.pack(side="left", padx=5)

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
        new_name = ctk.CTkInputDialog(title=self.renaming_text, text=f"{old_name}: {self.new_name}",).get_input()

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
        if self.is_played:
            self.btn_play_pause.configure(image=self.pause_btn_icon)
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
        self.refresh_tracks_display()

    def toggle_play_pause(self, event=None):
        if self.current_track_path:
            if pygame.mixer.music.get_busy() and not self.is_paused:
                self.pause_music()
                self.btn_play_pause.configure(image=self.play_btn_icon)
            else:
                self.play_music()
                self.btn_play_pause.configure(image=self.pause_btn_icon)

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

    def move_track(self, direction, path):
        if not path: return

        self.current_playlist = self.playlists[self.current_playlist_name]
        idx = self.current_playlist.index(path)
        new_idx = idx + direction

        if 0 <= new_idx < len(self.current_playlist):

            self.current_playlist[idx], self.current_playlist[new_idx] = self.current_playlist[new_idx], self.current_playlist[idx]
            self.save_data()
            self.refresh_tracks_display()
            self.info_label.configure(text=self.done)
            if self.current_track_path:
                self.after(2000, self.update_info_label)
            else:
                self.after(2000, lambda: self.info_label.configure(text=self.track_not_selected))

    def set_previous(self):
        self.next_track = self.current_playlist[self.current_index - 1]
        self.set_active_track(self.next_track)
        self.play_music()

    def set_next(self):
        self.next_track = self.current_playlist[self.current_index + 1]
        self.set_active_track(self.next_track)
        self.play_music()

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
            else:
                messagebox.showwarning("Afory", f"{self.select_track}")
        elif self.is_paused == True:
            self.is_played = True
            self.is_stopped = False
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
        def task():

            if not self.current_playlist:
                return

            if self.loop:
                next_track = self.current_playlist[self.current_index]
                self.current_music_num = 0
                self.current_length = 0
                self.after(0, lambda: self.set_active_track(next_track))
                return

            max_index = len(self.current_playlist)

            if self.current_index + 1 >= max_index:
                self.after(0, self.end_playlist_ui)
            else:
                next_track = self.current_playlist[self.current_index + 1]
                self.current_music_num = 0
                self.current_length = 0
                self.after(0, lambda: self.set_active_track(next_track))

        threading.Thread(target=task, daemon=True).start()

    def end_playlist_ui(self):
        self.status_bar.configure(text=self.playlist_ended)
        self.info_label.configure(text=self.track_not_selected)
        self.btn_play_pause.configure(image=self.play_btn_icon)
        self.is_stopped = True
        self.current_music_num = 0
        self.current_length = 0
        self.current_track_path = None
        self.refresh_tracks_display()

    def stop_music(self):
        self.is_stopped = True
        pygame.mixer.music.stop()
        self.status_bar.configure(text=self.playback_stopped)
        self.current_length = 0
        self.current_music_num = 0
        print("stop")

    def pause_music(self):
        pygame.mixer.music.pause()
        self.is_paused = True
        print("pause")

    def settings_open(self):
        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.geometry("450x660")
        self.settings_window.title(f"{self.settings_op}")
        self.settings_window.resizable(width=False, height=False)
        self.settings_window.transient(self)
        self.settings_window.grab_set()

        self.theme_label = ctk.CTkLabel(self.settings_window, text=self.design_theme, font=("Arial", 14))
        self.theme_label.pack(padx=20, pady=(10, 5))

        self.theme_menu = ctk.CTkOptionMenu(
            self.settings_window,
            values=["Dark", "Light"],
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

        self.open_keybinds_btn = ctk.CTkButton(self.settings_window, text=self.see_keybinds_t, font=("Arial", 14), command=self.show_keybinds)
        self.open_keybinds_btn.pack(pady=5)

        self.open_tutorial_btn = ctk.CTkButton(self.settings_window, text=self.tutorial, font=("Arial", 14), command=self.open_tutorial)
        self.open_tutorial_btn.pack(pady=5)

        self.lang_label = ctk.CTkLabel(self.settings_window, text=self.lang, font=("Arial", 15))
        self.lang_label.pack()

        self.lang_selecting = ctk.CTkOptionMenu(self.settings_window, values=["English", "Русский", "Deutsch", "ქართული", "español", "Українська", "Қазақ", "Polski", "Français", "日本語", "中國人", "Italiano", "Azərbaycan dili", "беларуская", "Türkçe", "Татар (кириллица)", "हिंदी", "한국인", "ελληνικά", "عربي", "Кыргызча", "नेवा", "ʻŌlelo Hawaiʻi", "Pilipino", "Nederlands", "norsk", "հայ", "Română", "Tiếng Việt", "hrvatski"], command=self.change_lang)
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

        link_font = ctk.CTkFont(underline=True, family="Arial", size=13)

        self.attributing_label = ctk.CTkLabel(self.settings_window, text="Icons by flaticon. Click for more", text_color="#2568d5")
        self.attributing_label.pack(pady=5)

        self.attributing_label.bind("<Button-1>", self.open_icons_creator_window)

        self.verison_label = ctk.CTkLabel(self.settings_window, text="Version: 2026.5.2.1", font=("Arial", 16))
        self.verison_label.pack(pady=5)

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
        self.settings_window.destroy()
        self.settings["language"] = new_lang
        self.save_settings()
        self.apply_lang()
        self.settings_open()

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

    def show_keybinds(self):
        messagebox.showinfo(f"{self.keybinds_t}", f"{self.first_keybind_t}\n"
                                   f"{self.second_keybind_t}\n"
                                   f"{self.third_keybind_t}\n"
                                   f"{self.works_even_not_in_app_t}\n"
                                   f"{self.keybinds_note}")

    def open_tutorial(self):
        messagebox.showerror(f"{self.error}", f"{self.tutorial_does_not_exists}")

    def open_github_dev1(self):
        webbrowser.open("https://github.com/Tuseloryy")

    def open_yt_dev1(self):
        webbrowser.open("https://www.youtube.com/@Tuseloryy")

    def open_tt_dev1(self):
        webbrowser.open("https://www.tiktok.com/@tuselmark")

    def open_icons_creator_window(self, event=None):
        messagebox.showinfo("Icon creators", "Pencil icon created by alkhalifi design - Flaticon\n"
                                "Link icon, trash icon and settings icon created by Freepik - Flaticon\n"
                                "Play button icon created by NajmunNahar - Flaticon\n"
                                "Pause button icon created by Slidicon - Flaticon\n"
                                "Arrow up icon and down icon created by Dave Gandy - Flaticon\n"
                                "Arrow left icon and arrow up icon created by Roundicons - Flaticon")

    def stop_loading_yt(self):
        self.stop_event.set()

        self.info_label.configure(text=self.loading_stopped)
        self.btn_add_yt.configure(
            text=self.download_from_YT,
            command=self.download_youtube
        )
        self.after(3000, self.update_info_label)

    def download_youtube(self):
        url = ctk.CTkInputDialog(title="Web", text=f"{self.supported_links}").get_input()
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
                    'ffmpeg_location': resource_path("assets/ffmpeg/ffmpeg"),
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

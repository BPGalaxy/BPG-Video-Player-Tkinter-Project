import sys
import tkinter as tk
from tkinter.ttk import *
from tkinter import ttk
from time import sleep
from tkinter.messagebox import *
from tkinter.filedialog import *
from tkinter.simpledialog import askstring
import time
import os
import CheckPrograms
import socket
import json
import threading
import queue
import secrets
import string
import subprocess
try:
    import websocket
except Exception:
    websocket = None
import server

joined_room = False
room_id = 000000
#Use to locate icon files in exe app
def resourcePath(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller .exe"""
    if hasattr(sys, "_MEIPASS"):
        # Running in a PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

InstalledPrograms = CheckPrograms.list_installed_programs()
if "VLC media player" not in InstalledPrograms:
    showerror("VLC Not Installed", "You don't have vlc app installed")
    q = askyesno("Install VLC", "Would you like to install it? it's necessary for running this app.")
    if q is True:
        os.system('python -m webbrowser -t "https://www.videolan.org/vlc/"')
        showinfo("Hint", "Download VLC from the opened URL.\n After installing, just relaunch the program")
        os.abort()
    else:
        os.abort()
else:
    import vlc

videoPlayer = tk.Tk()
videoPlayer.geometry("800x600")
videoPlayer.minsize(800, 600)
videoPlayer.maxsize(800, 600)
videoPlayer.title("BPG Video Player")
fg_color = "orchid1"
bg_color = "gray15"
font = "arial"

player = vlc.Instance()
media_player = player.media_player_new()
videoPlayer.iconbitmap(resourcePath("BPGVideoPlayerLogo.ico"))

volumecurrent = 50
Len1 = 0

def msToCleanTime(ms):
    second = ms/1000
    minute = 0
    hour = 0
    while second>60:
        if second >60:
            second -= 60
            minute += 1
        if minute>60:
            minute -= 60
            hour += 1

    second = round(second)
    if hour<10:
        hour = "0"+str(hour)
    if minute<10:
        minute = "0"+str(minute)
    if second<10:
        second = "0"+str(second)

    return f"{hour}:{minute}:{second}"

def cleanTimeToMs(cleanTime):
    hour = int(cleanTime[0:2])
    minute = int(cleanTime[3:5])
    second = int(cleanTime[6:8])
    minute = hour * (60) + minute
    second = minute * (60) + second
    return second * 1000

def changeVolume(a):
    global volumecurrent
    if a >= 100 or a <= 0:
        return
    volumecurrent = a
    setvolume.configure(value=volumecurrent)
    media_player.audio_set_volume(volumecurrent)

muteStatus = False
media_player.audio_set_mute(False)
def toggleMute(self):
    global muteStatus
    if media_player.get_media() is None:
        return
    if muteStatus is False:
        media_player.audio_set_mute(True)
        muteStatus = not muteStatus
        muteb.configure(text="🔈")
        setvolume.configure(value=0, state="disabled")

    else:
        media_player.audio_set_mute(False)
        muteStatus = not muteStatus
        muteb.configure(text="🔊")
        setvolume.configure(value=volumecurrent,  state="active")
    
pValue = False
def pauseMovie(self):
    global pValue
    if media_player.get_media() is None:
        return
    media_player.pause()
    pValue = not pValue
    if pValue is False:
        pauseb.configure(text="❚❚")
    else:
        pauseb.configure(text="►")

dirVids = []
vidIndex = 0
def perviousVid(self):
    global media
    global dirVids
    global vidIndex
    if dirVids == [] or vidIndex == 0:
        return
    else:
        vidIndex -= 1
        videoName = os.path.basename(dirVids[vidIndex])
        media = player.media_new(dirVids[vidIndex])
        media_player.set_media(media)
        media_player.play()
        media_player.set_hwnd(vidPlayFrame.winfo_id())
        media_player.audio_set_volume(volumecurrent)
        videoPlayer.title(f"BPG Video Player | Video ---> {videoName}")
        seekbar.configure(to=movielength())
        pauseb.configure(text="❚❚")

def nextVid(self):
    global media
    global dirVids
    global vidIndex
    if dirVids == [] or vidIndex == len(dirVids) - 1:
        return
    else:
        vidIndex += 1
        videoName = os.path.basename(dirVids[vidIndex])
        media = player.media_new(dirVids[vidIndex])
        media_player.set_media(media)
        media_player.play()
        media_player.set_hwnd(vidPlayFrame.winfo_id())
        media_player.audio_set_volume(volumecurrent)
        videoPlayer.title(f"BPG Video Player | Video ---> {videoName}")
        seekbar.configure(to=movielength())
        pauseb.configure(text="❚❚")

BG_COLOR = "#222222"
ACCENT_COLOR = "#9C539C"
TEXT_COLOR = "#E0E0E0"
FONT = ("Consolas", 11)
 
 
BG_COLOR = "#222222"
ACCENT_COLOR = "#9C539C"
TEXT_COLOR = "#E0E0E0"
FONT = ("Consolas", 11)
 
 
class _GuiStdin:
    """stdin-like object: readline() blocks until the GUI supplies a line."""
 
    def __init__(self):
        self._queue = queue.Queue()
 
    def clear(self):
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
 
    def readline(self):
        return self._queue.get()  # blocks until push_line() is called
 
    def push_line(self, line):
        self._queue.put(line if line.endswith("\n") else line + "\n")
 
    def isatty(self):
        return False
 
    def flush(self):
        pass
 
 
class _GuiStdout:
    """stdout-like object that forwards writes to a callback."""
 
    def __init__(self, write_callback):
        self._write_callback = write_callback
 
    def write(self, text):
        if text:
            self._write_callback(text)
 
    def flush(self):
        pass
 
 
class _ConsoleSession:
    """
    Holds everything that needs to outlive the console window: the
    redirected streams, the worker thread, and the output log.
 
    One session per module (keyed by id(module)), shared by every
    ServerConsole pointed at that module. This is what stops you from
    accidentally spawning a second module.start() thread while the first
    one is still alive.
    """
 
    _sessions = {}
 
    @classmethod
    def get(cls, module):
        key = id(module)
        session = cls._sessions.get(key)
        if session is None:
            session = cls(module)
            cls._sessions[key] = session
        return session
 
    def __init__(self, module):
        self.module = module
        self.gui_stdin = _GuiStdin()
        self.gui_stdout = _GuiStdout(self._append_output)
        self.worker_thread = None
        self._orig_stdin = None
        self._orig_stdout = None
        self._orig_stderr = None
        self.output_log = []               # full history, replayed into reopened windows
        self.output_queue = queue.Queue()  # new output since last drain
 
    def is_running(self):
        return self.worker_thread is not None and self.worker_thread.is_alive()
 
    def _append_output(self, text):
        self.output_log.append(text)
        self.output_queue.put(text)
 
    def start(self):
        if self.is_running():
            return  # already running -> no-op, prevents double start()
 
        # Clear any stale queued input left behind by a previous stop().
        # Otherwise a blank line from the last shutdown can satisfy the
        # next input() call immediately and make the server start with the
        # default localhost host without prompting again.
        self.gui_stdin.clear()
 
        self._orig_stdin = sys.stdin
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr
        sys.stdin = self.gui_stdin
        sys.stdout = self.gui_stdout
        sys.stderr = self.gui_stdout
 
        self.worker_thread = threading.Thread(target=self._run, daemon=True)
        self.worker_thread.start()
 
    def _run(self):
        try:
            self.module.start()
        except Exception as e:
            self._append_output(f"\n[console] module.start() raised: {e!r}\n")
        finally:
            self._append_output("\n[console] module.start() returned.\n")
            self._restore_streams()
 
    def stop(self):
        print("Stopping server...\n If clients are connected to the server, it'll take more time to stop the server.")
        try:
            self.module.stop()
        except Exception as e:
            if e == "RuntimeError('no running event loop')":
                return
            self._append_output(f"\n[console] module.stop() raised: {e!r}\n")
        # Unblock any input() call that is still waiting. We intentionally
        # clear stale queued values before the next start() so the next host
        # prompt is not satisfied by an old blank line from the previous stop.
        self.gui_stdin.clear()
        self.gui_stdin.push_line("")
 
    def _restore_streams(self):
        # guard against restoring streams that a newer start() already replaced
        if sys.stdin is self.gui_stdin:
            sys.stdin = self._orig_stdin
            sys.stdout = self._orig_stdout
            sys.stderr = self._orig_stderr
 
 
class ServerConsole(tk.Toplevel):
    def __init__(self, master, module, title="Console"):
        super().__init__(master)
        self.session = _ConsoleSession.get(module)
        self.title(title)
        self.geometry("720x480")
        self.configure(bg=BG_COLOR)
        self.minsize(480, 320)
 
        self._last_running = None
        self._poll_job = None
 
        self._build_ui()
        self._replay_log()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll_job = self.after(50, self._tick)
 
    # ---------------------------------------------------------------- UI --
 
    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
 
        style.configure(
            "Console.TButton",
            background=ACCENT_COLOR,
            foreground="#FFFFFF",
            borderwidth=0,
            focusthickness=0,
            padding=6,
        )
        style.map(
            "Console.TButton",
            background=[("active", "#7A3F7A"), ("disabled", "#4A3A4A")],
        )
        self.geometry("800x600")
        top_bar = tk.Frame(self, bg=BG_COLOR)
        top_bar.pack(side="top", fill="x", padx=8, pady=8)
 
        self.start_btn = ttk.Button(
            top_bar, text="Start", style="Console.TButton", command=self._on_start
        )
        self.start_btn.pack(side="left", padx=(0, 6))
 
        self.stop_btn = ttk.Button(
            top_bar, text="Stop", style="Console.TButton", command=self._on_stop
        )
        self.stop_btn.pack(side="left")
 
        self.status_label = tk.Label(
            top_bar, text="Stopped", bg=BG_COLOR, fg=ACCENT_COLOR, font=FONT
        )
        self.status_label.pack(side="right")
 
        text_frame = tk.Frame(self, bg=BG_COLOR)
        text_frame.pack(side="top", fill="both", expand=True, padx=8, pady=(0, 8))
 
        self.output = tk.Text(
            text_frame,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            insertbackground=ACCENT_COLOR,
            font=FONT,
            wrap="word",
            state="disabled",
            relief="flat",
            highlightthickness=1,
            highlightbackground=ACCENT_COLOR,
            highlightcolor=ACCENT_COLOR,
        )
        self.output.pack(side="left", fill="both", expand=True)
 
        input_frame = tk.Frame(self, bg=BG_COLOR)
        input_frame.pack(side="bottom", fill="x", padx=8, pady=(0, 8))
 
        prompt_label = tk.Label(
            input_frame, text=">>>", bg=BG_COLOR, fg=ACCENT_COLOR, font=FONT
        )
        prompt_label.pack(side="left", padx=(0, 4))
 
        self.input_entry = tk.Entry(
            input_frame,
            bg="#2E2E2E",
            fg=TEXT_COLOR,
            insertbackground=ACCENT_COLOR,
            font=FONT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=ACCENT_COLOR,
            highlightcolor=ACCENT_COLOR,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.input_entry.bind("<Return>", self._on_submit)
 
    def _replay_log(self):
        if not self.session.output_log:
            return
        self.output.configure(state="normal")
        self.output.insert("end", "".join(self.session.output_log))
        self.output.see("end")
        self.output.configure(state="disabled")
 
    # ------------------------------------------------------------- polling --
 
    def _tick(self):
        self._drain_output_queue()
        self._sync_buttons()
        self._poll_job = self.after(50, self._tick)
 
    def _drain_output_queue(self):
        try:
            while True:
                text = self.session.output_queue.get_nowait()
                self.output.configure(state="normal")
                self.output.insert("end", text)
                self.output.see("end")
                self.output.configure(state="disabled")
        except queue.Empty:
            pass
 
    def _sync_buttons(self):
        running = self.session.is_running()
        if running == self._last_running:
            return
        self._last_running = running
        if running:
            self.start_btn.state(["disabled"])
            self.stop_btn.state(["!disabled"])
            self.input_entry.configure(state="normal")
            self.status_label.configure(text="Running", fg="#4CD964")
        else:
            self.start_btn.state(["!disabled"])
            self.stop_btn.state(["disabled"])
            self.input_entry.configure(state="disabled")
            self.status_label.configure(text="Stopped", fg=ACCENT_COLOR)
 
    # ------------------------------------------------------- input flow --
 
    def _on_submit(self, event=None):
        if not self.session.is_running():
            return
        line = self.input_entry.get()
        if line == "cls":
            self.output.configure(state="normal")
            self.output.delete("1.0", "end")
            self.output.configure(state="disabled")
            self.input_entry.delete(0, "end")
            return
        self.input_entry.delete(0, "end")
        self.session._append_output(f">>> {line}\n")
        self.session.gui_stdin.push_line(line)
 
    # ------------------------------------------------------ start / stop --
 
    def _on_start(self):
        self.session.start()
        self._sync_buttons()
 
    def _on_stop(self):
        self.session.stop()
        self._sync_buttons()
 
    # --------------------------------------------------------------- close --
 
    def _on_close(self):
        # Detach the view only. The module keeps running in the background
        # if it was running -- reopening the console will re-attach to it.
        if self._poll_job is not None:
            self.after_cancel(self._poll_job)
            self._poll_job = None
        self.destroy()

def showUi():
    buttonsFrame.pack_configure(fill="x")
    seekframe.pack_configure(fill="x", side="bottom")

def hideUi():
    buttonsFrame.pack_forget()
    seekframe.pack_forget()

uiBool = True
def uiStatus(self):
    if flValue is False:
        return
    global uiBool
    if uiBool is True:
        hideUi()
        uiBool = not uiBool
    else:
        showUi()
        uiBool = not uiBool

flValue = False
def setFullscreen(self):
    global flValue
    global uiBool
    videoPlayer.focus_force()
    if media_player.get_media() is None:
        return
    flValue = not flValue
    uiBool = not uiBool
    videoPlayer.attributes("-fullscreen", flValue)
    if flValue is False:
        showUi()
    else:
        hideUi()

vidPlayFrame = Frame(videoPlayer)
vidPlayFrame.pack(expand=True, fill="both")

def PlayVid(VideoDir, IsArgv, IsPaused=False, IsMidJoined=False):
    if IsMidJoined:
        _send_json({"action": "loaded", "room": room_id})
    videoPlayer.maxsize(10000, 10000)
    videoName = os.path.basename(VideoDir)

    if IsArgv is False:
        vidDir = os.path.dirname(VideoDir)
        dirVidsTemp = os.listdir(vidDir)
        dirVids = []
        for vid in dirVidsTemp:
            dirVids.append(vidDir +'/'+ vid)
        vidIndex = dirVids.index(VideoDir)
    
    media = player.media_new(VideoDir)
    media_player.set_media(media)
    media_player.play()
    media_player.set_hwnd(vidPlayFrame.winfo_id())
    media_player.audio_set_volume(volumecurrent)
    seekbar.configure(to=movielength())
    pauseb.configure(text="❚❚")
    videoPlayer.title(f"BPG Video Player | Video ---> {videoName}")
    timelabel.configure(text=msToCleanTime(media_player.get_length()))
    if IsMidJoined:
        while media_player.get_time() < 10:
                    continue
        if IsPaused:
            pauseMovie('self')
        seekbar.configure(to=movielength())
        timelabel.configure(text=msToCleanTime(media_player.get_length()))
        return
    if joined_room or IsPaused:
        while media_player.get_time() < 10:
            continue
        pauseMovie('self')
        seekbar.configure(to=movielength())
        timelabel.configure(text=msToCleanTime(media_player.get_length()))
        _send_json({"action": "loaded", "room": room_id})
    else:
        while media_player.get_time() < 10:
            continue
        seekbar.configure(to=movielength())
        timelabel.configure(text=msToCleanTime(media_player.get_length()))
def openFolder(self):
    global media
    global dirVids
    global vidIndex
    global videoName

    fileSelect = askopenfile(title="Select a movie", filetypes=[('All Supported media files', ('*.mp4 *.mkv *.webm *.mpg *.ogg *.avi *.mov *.flv')),('Mp4 Files', ('*.mp4')), ('Mkv Files', ('*.mkv')), ('Webm Files', ('*.webm')), ('Mpg Files', ('*.mpg')), ('Ogg Files', ('*.ogg')), ('Avi Files', ('*.avi')), ('Mov Files', ('*.mov')), ('Flv Files', ('*.flv'))])
    if fileSelect is None:
        return
    else:
        PlayVid(fileSelect.name, False)

def play_url(url, broadcast=True):
    if url is None or url.strip() == "":
        return
    url = url.strip()
    if broadcast:
        try:
            if joined_room:
                # include whether the local player is paused so clients open in the same state
                try:
                    is_paused_flag = pValue
                except NameError:
                    is_paused_flag = False
                _send_ui("open_url", {"url": url, "is_paused": is_paused_flag})
        except Exception:
            pass
    PlayVid(url, True)


def style_button(btn, primary=False, *, ACCENT="#9C539C", ACCENT_HOVER="#B26AB2", BG_LIGHT="#2c2c2c", FG="#EAEAEA"):
    """Generic button styling used by dialogs/windows."""
    base = ACCENT if primary else BG_LIGHT
    hover = ACCENT_HOVER if primary else "#3a3a3a"
    fg = "#FFFFFF" if primary else FG
    btn.configure(
        bg=base, fg=fg, activebackground=hover, activeforeground=fg,
        relief='flat', bd=0, font=("Segoe UI", 10),
        padx=14, pady=6, cursor='hand2'
    )
    btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
    btn.bind("<Leave>", lambda e: btn.configure(bg=base))

def ask_dialog(parent, title="Host", prompt="", undertext="", default="", input_width=0):
    BG = "#222222"
    BG_LIGHT = "#2c2c2c"
    ACCENT = "#9C539C"
    ACCENT_HOVER = "#B26AB2"
    FG = "#EAEAEA"
    FG_MUTED = "#9A9A9A"
    BORDER = "#3a3a3a"
    result = {"value": None}

    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.configure(bg=BG)
    dlg.resizable(False, False)
    dlg.transient(parent)
    dlg.grab_set()  # modal

    frame = tk.Frame(dlg, bg=BG)
    frame.pack(fill='both', expand=True, padx=20, pady=16)

    prompt_lbl = tk.Label(
        frame, text=prompt, bg=BG, fg=FG,
        font=("Segoe UI", 10), justify='left', wraplength=280
    )
    prompt_lbl.pack(anchor='center', pady=(0, 4))

    hint_lbl = tk.Label(
        frame, text=undertext, bg=BG, fg=FG_MUTED,
        font=("Segoe UI", 8)
    )
    hint_lbl.pack(anchor='w', pady=(0, 8))

    entry_frame = tk.Frame(frame, bg=BORDER)
    entry_frame.pack(fill='x', pady=(0, 16))
    entry = tk.Entry(
        entry_frame, bg=BG_LIGHT, fg=FG, insertbackground=ACCENT,
        relief='flat', bd=0, font=("Segoe UI", 11), justify='center', width=input_width
    )
    entry.insert(0, default)
    entry.pack(fill='x', ipady=6, padx=1, pady=1)
    entry.focus_set()
    entry.select_range(0, 'end')

    btns = tk.Frame(frame, bg=BG)
    btns.pack(pady=(0, 0))

    def on_ok(event=None):
        result["value"] = entry.get().strip()
        dlg.destroy()

    def on_cancel(event=None):
        result["value"] = None
        dlg.destroy()

    ok_btn = tk.Button(btns, text="OK", command=on_ok)
    ok_btn.pack(side='left', padx=6)
    style_button(ok_btn, primary=True)

    cancel_btn = tk.Button(btns, text="Cancel", command=on_cancel)
    cancel_btn.pack(side='left', padx=6)
    style_button(cancel_btn, primary=False)

    dlg.bind('<Return>', on_ok)
    dlg.bind('<Escape>', on_cancel)

    # center relative to parent
    dlg.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (dlg.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (dlg.winfo_height() // 2)
    dlg.geometry(f"+{x}+{y}")

    parent.wait_window(dlg)
    return result["value"]

def openUrl(self):
    # Prompt the user for a URL and play it via VLC (supports http/https/rtsp/etc.)
    url = ask_dialog(videoPlayer, title="Url", prompt="Enter a video url to play:", input_width=40)
    play_url(url)

def paste_url_from_clipboard(event=None):
    try:
        url = videoPlayer.clipboard_get()
    except Exception:
        url = ""
    play_url(url)

def info(self='self'):
    showinfo("Keybinds",
    "See other keybinds: I/ i\n"
    "Open folder: O / o\n"
    "Open URL: . (dot)\n"
    "Play / Pause: P / p\n"
    "Stop: C / c\n"
    "Previous video: Ctrl+Left\n"
    "Next video: Ctrl+Right\n"
    "Volume up: Up Arrow\n"
    "Volume down: Down Arrow\n"
    "Seek backward 3s: Left Arrow\n"
    "Seek forward 3s: Right Arrow\n"
    "Fullscreen: F11\n"
    "Toggle UI (while fullscreen): U / u\n"
    "Toggle mute: M / m\n"
    "Connect / Network UI: S / s / Ctrl+S / = / +\n"
    "Paste URL from clipboard: Ctrl+V\n"
    "Show server console: F / f\n"
    "Recync (set play time): R / r\n\n"
    "Note: Many keys are bound in both lower and upper case.\n"
    "Use the Recync option to schedule playback at a specific clock time.")

def recync(self):
    if media_player.get_media() is None:
        return showerror("Error", "Play a video first")
    
    def playTime(actime, timer, tDown, playAt, flBool):
        try:
            tDown.destroy()
        except:
            pass
        global pValue
        global timerBool

        cHour = time.localtime().tm_hour
        cMinute = time.localtime().tm_min
        cSecond = time.localtime().tm_sec

        if cHour < 10:
            cHour = "0"+str(cHour)
        if cMinute < 10:
            cMinute = "0"+str(cMinute)
        if cSecond < 10:
            cSecond = "0"+str(cSecond)
        currentTime = f"{cHour}:{cMinute}:{cSecond}"

        if actime == str(currentTime):
            ms = int(cleanTimeToMs(playAt))

            if flBool is True:
                setFullscreen("self")

            media_player.pause()
            timer.destroy()
            pValue = not pValue
            return changeTime(ms+1)

        second = cleanTimeToMs(currentTime) / 1000

        fsecond = cleanTimeToMs(actime) / 1000
        try:
            tDown = Label(timer, text=f"Video will play in {int(fsecond - second)} seconds...", font=("arial", 15))
            tDown.pack()
        except:
            pass
        videoPlayer.after(2, lambda: playTime(actime, timer, tDown, playAt, flBool))

    def values(vv_time, v_clock):
        v_time = vv_time

        def clock_check(c_time):
            nonlocal v_time
            global error
            error = False
            if c_time == '':
                    showerror('Wrong value', "Clock field can't be empty")
                    selectPage.focus_force()
                    error = True
                    pass

            else:
                T_len = 0
                num1 = 60
                num2 = 60
                num3 = 24
                try:
                    num1 = int(c_time[3:5])
                    num2 = int(c_time[6:8])
                    num3 = int(c_time[0:2])
                except:
                    showerror('Wrong value', 'Enter a valid time value')
                    selectPage.focus_force()
                    error = True
                    pass
                cHour = time.localtime().tm_hour
                cMinute = time.localtime().tm_min
                cSecond = time.localtime().tm_sec
                if num3 < cHour:
                    showerror('Wrong value', "Selected hour is behind current hour time")
                    selectPage.focus_force()
                    error = True
                    pass
                elif num3 == cHour:
                    if num1 < cMinute:
                        showerror('Wrong value', "Selected minute is behind current minute time")
                        selectPage.focus_force()
                        error = True
                        pass
                    elif num1 == cMinute:
                        if num2 < cSecond:
                            showerror('Wrong value', "Selected second is behind current second time")
                            selectPage.focus_force()
                            error = True
                            pass

                if len(c_time) == 8 and error is False:
                    for letter in c_time:
                        T_len = T_len + 1
                        if T_len == 1 or T_len == 2 or T_len == 4 or T_len == 5 or T_len == 7 or T_len == 8:
                            try:
                                int(letter)
                                continue
                            except:
                                showerror('Wrong value', 'Enter a valid time value')
                                selectPage.focus_force()
                                error = True
                                break

                        elif T_len == 3 or T_len == 6:
                            if letter == ':':
                                continue
                            else:
                                showerror('Wrong value', 'Enter a valid time value')
                                selectPage.focus_force()
                                error = True
                                break
                
                if error is False:
                    selectPage.destroy()
                    global timer
                    timer = tk.Toplevel(videoPlayer)
                    timer.configure(background="#222222")
                    tDown = Label(timer, text=f"Video will play in ... seconds...")
                    tDown.pack()
                    return playTime(str(c_time), timer, tDown, v_time, askFullscreenValue.get())
                
                else:
                    selectPage.destroy()
                    recync("self")

        error = False
        if v_time == '':
            showerror('Wrong value', "Time field can't be empty")

        
        if v_time == '00:00:00':
            return clock_check(v_clock)
        
        else:
            T_len = 0
            num1 = 60
            num2 = 60
            try:
                num1 = int(v_time[3:5])
                num2 = int(v_time[6:8])
                int(v_time[0:2])
            except:
                showerror('Wrong value', 'Enter a valid time value')
                selectPage.focus_force()
                error = True
                pass

            if num1 > 60 or num2 > 60:
                showerror('Wrong value', 'Enter a valid time value')
                selectPage.focus_force()
                error = True
                pass

            vMs = cleanTimeToMs(v_time)
            movieMs = media_player.get_length()

            if vMs > movieMs:
                showerror("Error","Selected time can't be bigger than movie time!")
                selectPage.focus_force()
                error=True

            elif len(v_time) == 8 and error is False:
                for letter in v_time:
                    global Len1
                    Len1 = Len1 + 1
                    if T_len == 1 or T_len == 2 or T_len == 4 or T_len == 5 or T_len == 7 or T_len == 8:
                        try:
                            int(letter)
                            continue
                        except:
                            error = True
                            break

                    elif T_len == 3 or T_len == 6:
                        if letter == ':':
                            continue
                        else:
                            error = True
                            break

            elif error is False:
                showerror('Wrong value', 'Enter a valid time value')
                selectPage.focus_force()
                error = True

        if error is True:
            text1.destroy()
            text3.destroy()
            e_movieTime.destroy()
            e_movieClock.destroy()
            nextbtn.destroy()
            backbtn.destroy()
            recync("self")
        
        else:
            clock_check(v_clock)

    global pValue
    global nextbtn
    global style

    global text1
    if pValue is False:
        media_player.pause()
        pValue = not pValue

    selectPage = tk.Toplevel(vidPlayFrame)
    selectPage.geometry("350x400")

    selectPage.title("Select")
    selectPage.configure(bg="#222222")

    style.configure("S.TButton",background="#9C539C", foreground="#222222")
    style.map("S.TButton", background=[("active", "#D678D6")], foreground=[("active","#222222")])

    style.configure("S.TLabel", background="#222222", foreground="#9C539C", font=("georgia", 12))
    
    text1 = Label(selectPage, text="Enter a time so the movie will play from there", style="S.TLabel")
    text1.pack(pady=10)

    e_movieTime = Entry(selectPage)
    e_movieTime.pack()
    e_movieTime.insert(tk.END , msToCleanTime(media_player.get_time()))

    text3 = Label(selectPage, text="Enter a clock to start playing the movie", style="S.TLabel")
    text3.pack(pady=(20,10))

    e_movieClock = Entry(selectPage)
    e_movieClock.pack()

    def get15Sec():
        cHour = time.localtime().tm_hour
        cMinute = time.localtime().tm_min
        cSecond = int(time.localtime().tm_sec) + 15
        if cMinute >= 60:
            cMinute = cMinute - 60
            cHour += 1

        if cSecond >= 60:
            cSecond = cSecond - 60
            cMinute += 1

        if cHour < 10:
            cHour = "0"+str(cHour)
        if cMinute < 10:
            cMinute = "0"+str(cMinute)
        if cSecond < 10:
            cSecond = "0"+str(cSecond)

        try:
            e_movieClock.delete(0, "end")
            e_movieClock.insert(tk.END, f"{cHour}:{cMinute}:{cSecond}")
        except:
            e_movieClock.insert(tk.END, f"{cHour}:{cMinute}:{cSecond}")

    setTimebtn = Button(selectPage, text="+15 seconds from now", command=get15Sec, style="S.TButton")
    setTimebtn.pack(anchor="center", pady=(10,20))
    
    tip = Label(selectPage, text="Correct time format: 00:00:00", style="S.TLabel")
    tip.pack()

    style.configure("TCheckbutton", indicatorbackground="#222222", indicatorforeground="#9C539C", font=("georgia", 12))
    style.map("TCheckbutton", background=[("active", "#222222")], indicatorforeground=[("active","#9C669C")])

    askFullscreenValue = tk.BooleanVar()
    askFullscreen = Checkbutton(selectPage, text="Set fullscreen automaticly?", variable=askFullscreenValue)
    askFullscreen.pack(pady=(0,20))
    
    nextbtn = Button(selectPage, text="Next", command= lambda: values(e_movieTime.get(), e_movieClock.get()), style="S.TButton")
    nextbtn.pack(anchor="center")
    backbtn = Button(selectPage, text="Back", command= lambda: selectPage.destroy(), style="S.TButton")
    backbtn.pack(anchor="center", pady=5)

currentTime = 0
def progress():
    global ms
    global currentTime
    if media_player.get_media() is not None:
        ms = media_player.get_time()
    else:
        ms = 1
    currentTime = ms

    second = ms/1000
    minute = 0
    hour = 0
    while second>59:
        if second >59:
            second -= 60
            minute += 1
        if minute>59:
            minute -= 60
            hour += 1

    second = round(second)
    if second < 0:
        second += 1
    if hour<10:
        hour = "0"+str(hour)
    if minute<10:
        minute = "0"+str(minute)
    if second<10:
        second = "0"+str(second)

    cleanTime = f"{hour}:{minute}:{second}"

    timelabel2.configure(text=cleanTime)
    seekbar.configure(value=ms)
    if ms >= media_player.get_length() - 500:
        pauseb.configure(text="►")
    videoPlayer.after(1, progress)

def changeTime(time):
    if time <= 0 or time >= media_player.get_length():
        return
    global currentTime
    
    currentTime = time
    media_player.set_time(time)
    ms = time
    
    timelabel2.configure(text=msToCleanTime(ms))

def stop_and_clear(self=None):
    """Stop playback, clear media from the player, and reset UI."""
    try:
        media_player.stop()
    except Exception:
        pass
    try:
        media_player.set_media(None)
    except Exception:
        pass
    # Reset window title and UI indicators
    try:
        videoPlayer.title("BPG Video Player")
    except Exception:
        pass
    try:
        seekbar.configure(value=0, to=100)
    except Exception:
        pass
    try:
        timelabel.configure(text="00:00:00")
        timelabel2.configure(text="00:00:00")
    except Exception:
        pass
    try:
        pauseb.configure(text="►")
    except Exception:
        pass
    try:
        videoPlayer.attributes("-fullscreen", False)
        showUi()
    except Exception:
        pass
    try:
        videoPlayer.configure(width=800, height=600)
        videoPlayer.geometry("800x600")
        videoPlayer.minsize(800, 600)
        videoPlayer.maxsize(800, 600)
    except Exception:
        pass

def movielength():
    sleep(1)
    ms = media_player.get_length()
    return ms   

videoPlayer.configure(bg="#222222")
style = Style()
style.theme_use("clam")

style.configure(".", background="#222222", foreground="#9C539C")
style.configure("TFrame", background="#222222")
style.configure("TLabel", background="#222222", foreground="#9C539C", justify=tk.CENTER)
style.configure("TEntry", fieldbackground="#9C539C", background="#9C539C", foreground="#222222")
style.configure("TButton", background="#242424", foreground="#9C539C", font=(font, 12),
                relief="flat", borderwidth=0, focusthickness=0)
style.map("TButton", background=[("active", "#222222")], foreground=[("active","#D678D6")])
style.map("TEntry", fieldbackground="#D678D6", background=[("active", "#D678D6")], foreground=[("active","#222222")])

style.configure("Horizontal.TScale",
    background="#222222",          # full black
    troughcolor="#333333",      # slider track
)

style.configure("Horizontal.TScale",
    sliderlength=10,
)

# edit the internal layout to control thickness
style.layout("Horizontal.TScale", [
    ('Horizontal.Scale.trough', {'sticky': 'we', 'children': [
        ('Horizontal.Scale.slider', {'side': 'left', 'sticky': ''})
    ]})
])

console_ref = {"win": None}

def show_server_console(self='self'):
    # keep a single instance instead of stacking new windows on repeat clicks
    win = console_ref["win"]
    if win is not None and win.winfo_exists():
        win.lift()
        win.focus_force()
        return
    console_ref["win"] = ServerConsole(vidPlayFrame, module=server, title="Server Console")

# thinner track height
style.configure("Horizontal.Scale.trough", thickness=4)
style.configure("Horizontal.Scale.slider", relief="flat", borderwidth=0)
style.configure(
            "Console.TButton",
            background=ACCENT_COLOR,
            foreground="#FFFFFF",
            borderwidth=0,
            focusthickness=0,
            padding=6,
        )
style.map(
            "Console.TButton",
            background=[("active", "#7A3F7A"), ("disabled", "#4A3A4A")],
        )

welcome = Label(vidPlayFrame, text="Welcome to BPG video player.\n Choose a video to play using bottom left button or pressing 'o'.\nPress 'i' for keybinds help", font=("Georgia", 15), justify=tk.CENTER)
welcome.pack(anchor="center", pady=(230,0))

server_btn = Button(vidPlayFrame, text="Open Host Server CLI", style="Console.TButton", command=show_server_console)
server_btn.pack(anchor="center", pady=(10, 0))

madeBy = Label(vidPlayFrame, text="Made By Arthur",font=("Georgia", 15))
madeBy.pack(pady=(80,0))

style.configure("ICON.TButton", background="#222222", foreground="#9C539C", font=(font, 12),
                relief="flat", borderwidth=0, focusthickness=0)
style.map("ICON.TButton", background=[("active", "#222222")], foreground=[("active","#9C539C")])

telLogo = tk.PhotoImage(file=resourcePath("TelegramLogo.png"))
telLabel= Label(image=telLogo)
telegram = Button(vidPlayFrame, image=telLogo, style="ICON.TButton", command=lambda: os.system('python -m webbrowser -t "https://t.me/BP_Galaxy"'))
telegram.place(x=325,y=450)

gitLogo = tk.PhotoImage(file=resourcePath("GitHubLogo.png"))
gitLabel = Label(image=gitLogo)
github = Button(vidPlayFrame, image=gitLogo, style="ICON.TButton", command=lambda: os.system('python -m webbrowser -t "https://github.com/BPGalaxy"'))
github.place(x=400,y=450)



seekframe = Frame(videoPlayer)
seekframe.pack(fill="x", side="bottom")

def seekBarUpdate():
    WinSize = videoPlayer.winfo_geometry()
    xlength = ""
    for letter in WinSize:
        if letter != "x":
            xlength += letter
        else:
            break
    seekbar.configure(length=int(xlength) - 100)
    videoPlayer.after(1, seekBarUpdate)

timelabel2 = Label(seekframe, text="00:00:00")
timelabel2.pack(side="left")

# wrapper helpers must be defined before buttons so bindings can reference them
def pause_and_broadcast(_=None):
    try:
        pauseMovie("self")
    except Exception:
        pass
    if joined_room:
        _send_ui("pause")

def stop_and_broadcast(_=None):
    try:
        stop_and_clear()
    except Exception:
        try:
            stop_and_clear("self")
        except Exception:
            pass
    if joined_room:
        _send_ui("stop")

def change_time_and_broadcast(time_val):
    try:
        changeTime(time_val)
    except Exception:
        pass
    if joined_room:
        _send_ui("change_time", {"time": int(time_val)})

seekbar = Scale(seekframe, from_=0, to=100, orient="horizontal", length=700, command=lambda ctime: change_time_and_broadcast(round(seekbar.get())))
seekbar.pack(side="left", fill="x", padx=(5,0))
seekBarUpdate()


timelabel = Label(seekframe, text="00:00:00")
timelabel.pack(side="right")

buttonsFrame = Frame(videoPlayer, style="Dark.TFrame")
buttonsFrame.pack(fill="x")
style.configure("Dark.TFrame", background="#242424")

openfolderb = Button(buttonsFrame, text="🗂️", width=2, command= lambda: openFolder("self"))
openfolderb.pack(side="left")

urlb = Button(buttonsFrame, text="🔗", width=2, command=lambda: openUrl("self"))
urlb.pack(side="left")

serverb = Button(buttonsFrame, text="🌐", width=2, command=lambda: connect_ws("self"))
serverb.pack(side="left")

fullscreenb = Button(buttonsFrame, text="⛶", width=2, command= lambda: setFullscreen("self"))
fullscreenb.pack(side="left")

recyncb = Button(buttonsFrame, text="⟲", width=2, command= lambda: recync("self"))
recyncb.pack(side="left")

stopb = Button(buttonsFrame, text="🗑️", width=2, command=stop_and_broadcast)
stopb.pack(side="left")

infob = Button(buttonsFrame, text="!", width=2, command= info)
infob.pack(side="left")

perviousb = Button(buttonsFrame, text="|◁", width=2, command=lambda: perviousVid("self"))
perviousb.place(x=367, y=0)

pauseb = Button(buttonsFrame, text="►", width=2, command=pause_and_broadcast)
pauseb.place(x=387, y=0)

nextb = Button(buttonsFrame, text="▷|", width=2, command=lambda: nextVid("self"))
nextb.place(x=407, y=0)

Len = 0
def pausebUpdate():
    global Len
    WinSize = videoPlayer.winfo_geometry()
    if Len < 10:
        videoPlayer.after(100, pausebUpdate)
        Len += 1
        return
    xlength = ""
    for letter in WinSize:
        if letter != "x":
            xlength += letter
        else:
            break
    perviousb.place_configure(x=int(xlength) / 2 - 33)
    pauseb.place_configure(x=int(xlength) / 2 - 13)
    nextb.place_configure(x=int(xlength) / 2 + 7)
    videoPlayer.after(1, pausebUpdate)
pausebUpdate()

setvolume = Scale(buttonsFrame, from_=0, to=100, orient="horizontal", command=lambda volume: changeVolume(round(setvolume.get())), value=volumecurrent)
setvolume.pack(side="right")
media_player.audio_set_volume(volumecurrent)

muteb = Button(buttonsFrame, text="🔊", width=2, command= lambda: toggleMute("self"))
muteb.pack(side="right")

## WebSocket client state
ws_app = None
ws_thread = None
ws_connected = False
client_name = None

def _ui_thread_safe(fn, *a, **k):
    videoPlayer.after(0, lambda: fn(*a, **k))

def _on_ws_open(ws):
    global ws_connected
    ws_connected = True
    threading.Thread(target=showinfo, kwargs={"title":"WS", "message":"Connected to server"}).start()

user_counts = 0
get_notifcation = True
is_owner = False
def _on_ws_message(ws, message):        
    global user_counts, is_owner, room_id
    try:
        data = json.loads(message)
    except Exception:
        data = {"type": "raw", "data": message}

    t = data.get("type")
    if t == "rooms":
        # ignore for now
        return
    if t == "created":
        _ui_thread_safe(_set_joined, data.get("room"))
        set_status(True, user_counts=user_counts)
    elif t == "joined":
        _ui_thread_safe(_set_joined, data.get("room"))
        set_status(True, user_counts=user_counts)
    elif t == "left":
        set_status(False, user_counts=user_counts)
        _ui_thread_safe(_set_left)
    elif t == "notice":
        msg = data.get('message')
        if get_notifcation:
            threading.Thread(target=showinfo, kwargs={"title":"Info", "message":msg}).start()
        if "joined the room." in msg:
            if media_player.get_media() is not None:
                ms = media_player.get_time()
            else:
                ms = None
            _send_json({"action":"current_time", "room":room_id, "time":ms, "joined_user":data.get('joined_user'), "sent_at":time.time()*1000})
        _ui_thread_safe(_append_msg, f"[notice] {msg}")
    elif t == "error":
        msg = data.get('message')
        if msg == "You can't play the video unless everybody is loaded.":
            changeTime(10)
            pauseMovie("self")
        threading.Thread(target=showerror, kwargs={"title":"Error", "message":msg}).start()
    elif t == "message":
        _ui_thread_safe(_append_msg, f"[{data.get('from')}] {data.get('message')}")
    elif t == "welcome":
        _ui_thread_safe(_append_msg, data.get("message"))
    elif t == "is_owner":
        is_owner = data.get("value")
    elif t == "user_count":
        user_counts = data.get("data")
        set_status(True, user_counts=user_counts)
    elif t == "streaming_data":
        room_data = data.get("data")
        url = room_data.get("url")
        if url:
            _ui_thread_safe(PlayVid, url, True, room_data.get('is_paused'), True)
    else:
        _ui_thread_safe(_append_msg, str(data))
    # handle UI messages
    if t == "ui":
        ui_action = data.get("ui_action")
        params = data.get("params") or {}
        # dispatch UI actions on the main thread
        if ui_action == "pause":
            _ui_thread_safe(pauseMovie, "self")
        elif ui_action == "fullscreen":
            _ui_thread_safe(setFullscreen, "self")
        elif ui_action == "change_time":
            tm = params.get("time")
            try:
                sent_at = params.get("sent_at")
                current = time.time()*1000
                between = current - sent_at
                tm += (between+220)
            except:
                tm = params.get("time")
            if isinstance(tm, (int, float)):
                _ui_thread_safe(changeTime, int(tm))
        elif ui_action == "open_url":
            url = params.get("url")
            is_paused = params.get("is_paused")
            if url:
                _ui_thread_safe(PlayVid, url, True, is_paused)
        elif ui_action == "stop":
            _ui_thread_safe(stop_and_clear, "self")

def _on_ws_close(ws, close_status_code, close_msg):
    global ws_connected
    ws_connected = False
    _ui_thread_safe(_append_msg, "Disconnected from server")
    _ui_thread_safe(_set_left)

def _on_ws_error(ws, err):
    _ui_thread_safe(_append_msg, f"WS error: {err}")

def _start_ws(url):
    global ws_app
    if websocket is None:
        _ui_thread_safe(showerror, "Missing dependency", "Please install 'websocket-client' (pip install websocket-client)")
        return
    ws_app = websocket.WebSocketApp(url,
                                    on_open=_on_ws_open,
                                    on_message=_on_ws_message,
                                    on_close=_on_ws_close,
                                    on_error=_on_ws_error)
    ws_app.run_forever()

## UI helpers and widgets (populated when UI created)
ws_window = None
room_entry = None
create_btn = None
join_btn = None
leave_btn = None
msg_box = None
name_entry = None

def _append_msg(text):
    if msg_box is None:
        return
    msg_box.configure(state='normal')
    msg_box.insert('end', text + "\n")
    msg_box.see('end')
    msg_box.configure(state='disabled')

def _set_joined(room):
    try:
        stop_and_clear()
    except Exception:
        stop_and_clear("self")
    global joined_room, room_id
    joined_room = room
    room_id = room
    if leave_btn:
        leave_btn.configure(state='normal')
    _append_msg(f"Joined room: {room}")
    # populate entry if UI present
    if room_entry:
        try:
            room_entry.delete(0, 'end')
            room_entry.insert(0, room)
        except Exception:
            pass

def _set_left():
    global joined_room
    joined_room = None
    if leave_btn:
        leave_btn.configure(state='disabled')
    _append_msg("Left room")
    stop_and_clear()
    if room_entry:
        try:
            room_entry.delete(0, 'end')
        except Exception:
            pass

def _send_json(obj):
    global ws_app
    if not ws_app:
        showerror("WS", "Not connected")
        return
    try:
        ws_app.send(json.dumps(obj))
    except Exception as e:
        showerror("WS Send Failed", str(e))

def _send_ui(action, params=None):
    if params is None:
        params = {}
    _send_json({"action": "ui", "ui_action": action, "params": params})

ROOM_CODE_CHARS = string.ascii_letters + string.digits

def generate_room_code(length=10):
    return "".join(secrets.choice(ROOM_CODE_CHARS) for _ in range(length))


def _do_create():
    global room_id
    code = room_entry.get().strip()
    room_password = password_entry.get().strip()
    code = generate_room_code()
    room_entry.delete(0, 'end')
    room_entry.insert(0, code)
    room_id = code
    _send_json({"action": "create", "room": code, "password": room_password})

def _do_join():
    global room_id
    code = room_entry.get().strip()
    room_password = password_entry.get().strip()
    if code == "":
        showerror("Join", "Enter a room code or create one")
        return
    room_id = code
    _send_json({"action": "join", "room": code, "password": room_password})

def _do_leave():
    global room_id
    room_id = 000000
    _send_json({"action": "leave"})


host = "0.0.0.0"
def connect_ws(event):
    """Connect to websocket server and show room UI."""
    global ws_thread, ws_window, room_entry, password_entry, create_btn, join_btn, leave_btn, msg_box, ws_app, host
    
    if host == "0.0.0.0":
        host = ask_dialog(videoPlayer, title="Host", prompt="Enter a host IP:", undertext="Leave blank to use localhost")
    if host is None:
        host = "0.0.0.0"
        return None
    if host == "":
        host = "127.0.0.1"
    port = 8765
    url = f"ws://{host}:{port}"

    # start WS thread if not running
    if not ws_thread or (ws_thread and not ws_thread.is_alive()):
        try:
            # quick TCP check
            s = socket.create_connection((host, port), timeout=3)
            s.close()
        except Exception as e:
            showerror("WS Connect Failed", f"Could not connect to ws server at {host}:{port}.\n{e}")
            return

        ws_thread = threading.Thread(target=_start_ws, args=(url,), daemon=True)
        ws_thread.start()

    # create UI window
    if ws_window and ws_window.winfo_exists():
        ws_window.lift()
        return

    BG = "#222222"
    BG_LIGHT = "#2c2c2c"
    ACCENT = "#9C539C"
    ACCENT_HOVER = "#B26AB2"
    FG = "#EAEAEA"
    FG_MUTED = "#9A9A9A"
    BORDER = "#3a3a3a"

    ws_window = tk.Toplevel(videoPlayer)
    ws_window.title("Network Rooms")
    ws_window.geometry("420x500")
    ws_window.configure(bg=BG)
    ws_window.minsize(420, 500)
    ws_window.maxsize(420, 500)
    ws_window.resizable(False, False)

    def style_button(btn, primary=False):
        base = ACCENT if primary else BG_LIGHT
        hover = ACCENT_HOVER if primary else "#3a3a3a"
        fg = "#FFFFFF" if primary else FG
        btn.configure(
            bg=base, fg=fg, activebackground=hover, activeforeground=fg,
            relief='flat', bd=0, font=("Segoe UI", 10),
            padx=14, pady=6, cursor='hand2'
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda e: btn.configure(bg=base))

    frame = tk.Frame(ws_window, bg=BG)
    frame.pack(fill='both', expand=True, padx=16, pady=16)

    # Header
    header = tk.Label(frame, text="Network Rooms", bg=BG, fg=FG,
                    font=("Segoe UI", 13, "bold"))
    header.pack(anchor='w', pady=(0, 10))

    # Room code input
    lbl = tk.Label(frame, text="Room code", bg=BG, fg=FG_MUTED, font=("Segoe UI", 9))
    lbl.pack(anchor='w')

    entry_frame = tk.Frame(frame, bg=BORDER)
    entry_frame.pack(fill='x', pady=(4, 12))
    room_entry = tk.Entry(
        entry_frame, bg=BG_LIGHT, fg=FG, insertbackground=ACCENT,
        relief='flat', bd=0, font=("Segoe UI", 11)
    )
    room_entry.pack(fill='x', ipady=6, padx=1, pady=1)

    lbl2 = tk.Label(frame, text="Room password (optional)", bg=BG, fg=FG_MUTED, font=("Segoe UI", 9))
    lbl2.pack(anchor='w')

    password_entry_frame = tk.Frame(frame, bg=BORDER)
    password_entry_frame.pack(fill='x', pady=(4, 12))
    password_entry = tk.Entry(
        password_entry_frame, bg=BG_LIGHT, fg=FG, insertbackground=ACCENT,
        relief='flat', bd=0, font=("Segoe UI", 11), show="*"
    )
    password_entry.pack(fill='x', ipady=6, padx=1, pady=1)
    password_show = tk.BooleanVar(value=False)

    def toggle_password():
        if password_show.get():
            password_entry.configure(show="")
        else:
            password_entry.configure(show="*")

    def toggle_notifications():
        global get_notifcation
        get_notifcation = notification_show.get()

    checkbox_row = tk.Frame(frame, bg=BG)
    checkbox_row.pack(fill='x', pady=(0, 12))

    password_toggle = tk.Checkbutton(
        checkbox_row,
        text="Show password",
        variable=password_show,
        command=toggle_password,
        bg=BG,
        fg=FG_MUTED,
        font=("Segoe UI", 9),
        activebackground=BG,
        activeforeground=FG_MUTED,
        selectcolor=BG,
    )
    password_toggle.pack(side='left', anchor='w', padx=(0, 12))

    notification_show = tk.BooleanVar(value=True)
    notification_show.set(True)
    notification_toggle = tk.Checkbutton(
        checkbox_row,
        text="Get room notifications",
        variable=notification_show,
        command=toggle_notifications,
        bg=BG,
        fg=FG_MUTED,
        font=("Segoe UI", 9),
        activebackground=BG,
        activeforeground=FG_MUTED,
        selectcolor=BG,
    )
    notification_toggle.pack(side='left', anchor='w')

    # Status indicator
    status_frame = tk.Frame(frame, bg=BG)
    status_frame.pack(fill='x', pady=(0, 10))
    status_dot = tk.Label(status_frame, text="●", bg=BG, fg="#666666", font=("Segoe UI", 10))
    status_dot.pack(side='left')
    status_label = tk.Label(status_frame, text="Not joined a room", bg=BG, fg=FG_MUTED, font=("Segoe UI", 9))
    status_label.pack(side='left', padx=(0, 0))
    count_label = tk.Label(status_frame, text=f"", bg=BG, fg=FG_MUTED)
    count_label.pack(side='right', padx=(0, 0))
    # Buttons
    btns = tk.Frame(frame, bg=BG)
    btns.pack(fill='x', pady=(0, 12))

    create_btn = tk.Button(btns, text="Create", command=_do_create)
    create_btn.pack(side='left', padx=(0, 6))
    style_button(create_btn, primary=True)

    join_btn = tk.Button(btns, text="Join", command=_do_join)
    join_btn.pack(side='left')
    style_button(join_btn, primary=True)

    leave_btn = tk.Button(btns, text="Leave", command=_do_leave, state='disabled')
    leave_btn.pack(side='right')
    style_button(leave_btn, primary=False)

    # Message log
    log_lbl = tk.Label(frame, text="Activity", bg=BG, fg=FG_MUTED, font=("Segoe UI", 9))
    log_lbl.pack(anchor='w')

    msg_frame = tk.Frame(frame, bg=BORDER)
    msg_frame.pack(fill='both', expand=True, pady=(4, 0))
    msg_box = tk.Text(
        msg_frame, height=10, state='disabled', bg=BG_LIGHT, fg=FG,
        relief='flat', bd=0, font=("Consolas", 9), padx=8, pady=6,
        wrap='word'
    )
    msg_box.pack(fill='both', expand=True, padx=1, pady=1)

    global set_status
    def set_status(connected: bool, text: str = None, room_code = room_id, user_counts = 0):
        """Call after connect/disconnect to update the dot + label + button states."""
        status_dot.configure(fg=ACCENT if connected else "#666666")
        status_label.configure(text=text or (f"Connected to room {room_id}" if connected else "Not joined a room"))
        count_label.configure(text= f"in room: {user_counts}" if connected else "")
        leave_btn.configure(state='normal' if connected else 'disabled')
        create_btn.configure(state='disabled' if connected else 'normal')
        join_btn.configure(state='disabled' if connected else 'normal')

    if room_id != 000000:
        set_status(True, user_counts=user_counts)
    def log_message(text: str):
        """Append a line to the message box and auto-scroll."""
        msg_box.configure(state='normal')
        msg_box.insert('end', text + '\n')
        msg_box.see('end')
        msg_box.configure(state='disabled')

    _append_msg("UI ready. Use Create or Join to enter a room.")

    # restore state if already joined or name set
    if client_name:
        try:
            name_entry.delete(0, 'end')
            name_entry.insert(0, client_name)
        except Exception:
            pass
    if joined_room:
        try:
            room_entry.delete(0, 'end')
            room_entry.insert(0, joined_room)
            leave_btn.configure(state='normal')
            _append_msg(f"Re-attached to room: {joined_room}")
        except Exception:
            pass

videoPlayer.bind("<i>", info)
videoPlayer.bind("<I>", info)
videoPlayer.bind("<o>", lambda self: openFolder("self"))
videoPlayer.bind("<O>", lambda self: openFolder("self"))
videoPlayer.bind("<r>", recync)
videoPlayer.bind("<R>", recync)
videoPlayer.bind("<Up>", lambda volume: changeVolume(volumecurrent + 1))
videoPlayer.bind("<Down>", lambda volume: changeVolume(volumecurrent - 1))
videoPlayer.bind("<Left>", lambda e: change_time_and_broadcast(currentTime - 3000))
videoPlayer.bind("<Right>", lambda e: change_time_and_broadcast(currentTime + 3000))
videoPlayer.bind("<Control-Left>", lambda self: perviousVid("self"))
videoPlayer.bind("<p>", pause_and_broadcast)
videoPlayer.bind("<P>", pause_and_broadcast)
videoPlayer.bind("<c>", stop_and_broadcast)
videoPlayer.bind("<C>", stop_and_broadcast)
videoPlayer.bind("<.>", lambda self: openUrl("self"))
videoPlayer.bind("<Control-Right>", lambda self: nextVid("self"))
videoPlayer.bind("<F11>", lambda self: setFullscreen("self"))
videoPlayer.bind("<u>", uiStatus)
videoPlayer.bind("<U>", uiStatus)
videoPlayer.bind("<s>", connect_ws)
videoPlayer.bind("<S>", connect_ws)
videoPlayer.bind("<Control-s>", connect_ws)
videoPlayer.bind("<Control-S>", connect_ws)
videoPlayer.bind("<f>", show_server_console)
videoPlayer.bind("<F>", show_server_console)
videoPlayer.bind("<=>", connect_ws)
videoPlayer.bind("<+>", connect_ws)
videoPlayer.bind("<Control-v>", paste_url_from_clipboard)
videoPlayer.bind("<Control-V>", paste_url_from_clipboard)
videoPlayer.bind("<Control-t>", lambda self: showinfo("Info","I love you:)<3"))
videoPlayer.bind("<Control-T>", lambda self: showinfo("Info","I love you:)<3"))
videoPlayer.bind("<m>", lambda self: toggleMute("self"))
videoPlayer.bind("<M>", lambda self: toggleMute("self"))

if len(sys.argv) > 1:
    arg = sys.argv[1]
    # If it's a local file path, play that; otherwise attempt to play as URL or direct input
    if os.path.isfile(arg):
        PlayVid(os.path.abspath(arg), True)
    elif arg.startswith(("http://", "https://", "rtsp://", "mms://", "rtmp://", "ftp://")):
        PlayVid(arg, True)
    else:
        # Fallback: try absolute path, then attempt to play the raw argument (VLC can handle many schemes)
        abs_arg = os.path.abspath(arg)
        if os.path.isfile(abs_arg):
            PlayVid(abs_arg, True)
        else:
            PlayVid(arg, True)
progress()
videoPlayer.mainloop()

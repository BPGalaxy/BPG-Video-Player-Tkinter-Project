import sys
import vlc
import tkinter as tk
from tkinter.ttk import *
from time import sleep
from tkinter.messagebox import *
from tkinter.filedialog import *
import time
import os

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

volumecurrent = 100
Len1 = 0

#Use to locate icon files in exe app
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller .exe"""
    if hasattr(sys, "_MEIPASS"):
        # Running in a PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def msToCleanTime(ms):
    second = ms/1000
    minute = 0
    hour = 0
    while second>59:
        if second >59:
            second -= 59
            minute += 1
        if minute>59:
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
        media = player.media_new(dirVids[vidIndex])
        media_player.set_media(media)
        media_player.play()
        media_player.set_hwnd(vidPlayFrame.winfo_id())
        media_player.audio_set_volume(volumecurrent)
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
        media = player.media_new(dirVids[vidIndex])
        media_player.set_media(media)
        media_player.play()
        media_player.set_hwnd(vidPlayFrame.winfo_id())
        media_player.audio_set_volume(volumecurrent)
        seekbar.configure(to=movielength())
        pauseb.configure(text="❚❚")

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

def openFolder(self):
    videoPlayer.maxsize(10000, 10000)
    global media
    global dirVids
    global vidIndex

    fileSelect = askopenfile(title="Select a movie", filetypes=[('Mp4 files', '*.mp4'), ('Mkv files', '*.mkv')])
    if fileSelect is None:
        return
    
    videoName = os.path.basename(fileSelect.name)
    vidDir = os.path.dirname(fileSelect.name)
    dirVidsTemp = os.listdir(vidDir)
    dirVids = []
    for vid in dirVidsTemp:
        dirVids.append(vidDir +"/"+ vid)
    vidIndex = dirVids.index(fileSelect.name)

    media = player.media_new(fileSelect.name)
    media_player.set_media(media)
    media_player.video_set_spu(2)
    media_player.play()
    
    media_player.set_hwnd(vidPlayFrame.winfo_id())
    media_player.audio_set_volume(volumecurrent)
    seekbar.configure(to=movielength())
    pauseb.configure(text="❚❚")
    videoPlayer.title(f"BPG Video Player | Video ---> {videoName}")

    timelabel.configure(text=msToCleanTime(media_player.get_length()))

def info():
    showinfo("All Keybinds:\n",
    "Next Video: Ctrl+PageRight\n" \
    "Pause: P\n" \
    "Pervious Video: Ctrl+PageLeft\n" \
    "FullScreen: F11\n" \
    "OpenFolder: O\n" \
    "Cync: R\n" \
    "Toggle UI (Only while fullscreen): U\n" \
    "Toggle Mute: M\n" \
    "Volume Up: PageUp\n" \
    "Volume Down: PageDown\n" \
    "3 Sec BackWard: PageLeft\n" \
    "3 Sec Forward: PageRight\n\n" \
    "If you want to play the movie on a specific time, use Cync option.")

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
    ms = media_player.get_time()
    currentTime = ms

    timelabel2.configure(text=msToCleanTime(ms))
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

# thinner track height
style.configure("Horizontal.Scale.trough", thickness=4)
style.configure("Horizontal.Scale.slider", relief="flat", borderwidth=0)

welcome = Label(vidPlayFrame, text="Welcome to BPG video player.\n Choose a video to play using bottom left button or pressing 'o'.", font=("Georgia", 15), justify=tk.CENTER)
welcome.pack(anchor="center", pady=(250,0))

madeBy = Label(vidPlayFrame, text="Made By Arthur",font=("Georgia", 15))
madeBy.pack(pady=(80,0))

style.configure("ICON.TButton", background="#222222", foreground="#9C539C", font=(font, 12),
                relief="flat", borderwidth=0, focusthickness=0)
style.map("ICON.TButton", background=[("active", "#222222")], foreground=[("active","#9C539C")])

telLogo = tk.PhotoImage(file="TelegramLogo.png")
telLabel= Label(image=telLogo)
telegram = Button(vidPlayFrame, image=telLogo, style="ICON.TButton", command=lambda: os.system('python -m webbrowser -t "https://t.me/BP_Galaxy"'))
telegram.place(x=325,y=410)

gitLogo = tk.PhotoImage(file="GitHubLogo.png")
gitLabel = Label(image=gitLogo)

github = Button(vidPlayFrame, image=gitLogo, style="ICON.TButton", command=lambda: os.system('python -m webbrowser -t "https://github.com/BPGalaxy"'))
github.place(x=400,y=410)

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

seekbar = Scale(seekframe, from_=0, to=100, orient="horizontal", length=700, command=lambda ctime: changeTime(round(seekbar.get())))
seekbar.pack(side="left", fill="x", padx=(5,0))
seekBarUpdate()

timelabel = Label(seekframe, text="00:00:00")
timelabel.pack(side="right")

buttonsFrame = Frame(videoPlayer, style="Dark.TFrame")
buttonsFrame.pack(fill="x")
style.configure("Dark.TFrame", background="#242424")

openfolderb = Button(buttonsFrame, text="🗂️", width=2, command= lambda: openFolder("self"))
openfolderb.pack(side="left")

fullscreenb = Button(buttonsFrame, text="⛶", width=2, command= lambda: setFullscreen("self"))
fullscreenb.pack(side="left")

recyncb = Button(buttonsFrame, text="⟲", width=2, command= lambda: recync("self"))
recyncb.pack(side="left")

infob = Button(buttonsFrame, text="!", width=2, command= info)
infob.pack(side="left")

perviousb = Button(buttonsFrame, text="|◁", width=2, command=lambda: perviousVid("self"))
perviousb.place(x=367, y=0)

pauseb = Button(buttonsFrame, text="►", width=2, command=lambda: pauseMovie("self"))
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

setvolume = Scale(buttonsFrame, from_=0, to=100, orient="horizontal", command=lambda volume: changeVolume(round(setvolume.get())), value=100)
setvolume.pack(side="right")

muteb = Button(buttonsFrame, text="🔊", width=2, command= lambda: toggleMute("self"))
muteb.pack(side="right")

videoPlayer.bind("<o>", lambda self: openFolder("self"))
videoPlayer.bind("<r>", recync)
videoPlayer.bind("<Up>", lambda volume: changeVolume(volumecurrent + 1))
videoPlayer.bind("<Down>", lambda volume: changeVolume(volumecurrent - 1))
videoPlayer.bind("<Left>", lambda ctime: changeTime(currentTime - 3000))
videoPlayer.bind("<Right>", lambda ctime: changeTime(currentTime + 3000))
videoPlayer.bind("<Control-Left>", lambda self: perviousVid("self"))
videoPlayer.bind("<p>", lambda self: pauseMovie("self"))
videoPlayer.bind("<Control-Right>", lambda self: nextVid("self"))
videoPlayer.bind("<F11>", setFullscreen)
videoPlayer.bind("<u>", uiStatus)
videoPlayer.bind("<Control-t>", lambda self: showinfo("Info","I love you:)<3"))
videoPlayer.bind("<m>", lambda self: toggleMute("self"))



progress()
videoPlayer.mainloop()
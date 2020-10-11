#!/usr/bin/env python3
import tkinter as tk
from tkinter import Tk, Frame
import os, sys
import time
import subprocess
import signal
import glob
from pymediainfo import MediaInfo
from PIL import ImageTk, Image
from mplayer import Player
import tkinter.font
import math
import getpass
RunningOnPi = os.uname()[4].startswith('arm')
UseOmxplayer = False
if RunningOnPi:
    import RPi.GPIO as GPIO
    import alsaaudio
    UseOmxplayer = True

Player.introspect()
global fullscreen
fullscreen = 0

TITLELO=4
TITLEHI=12

IDLE=0
PLAYING=1

GAPTIME=0.2

class ZeroPlayer(Frame):
    
    def __init__(self, windowed = False):
        super().__init__()
        self.windowed = windowed
        self.user = getpass.getuser()
        if windowed:
            self.player = Player(args=('-xy', '800', '-geometry', '1100:100', '-noborder', '-ontop'))
        else:
            self.player = Player()
        self.mp3_search = "/media/" + self.user + "/*/*/*/*.mp*"
        self.m3u_def    = "ALLTracks"
        self.m3u_dir    = "/media/" + self.user + "/MUSIC/"
        self.mp4playing     = False
        self.volume         = 100
        self.stop_start     = 22
        self.nexttrk        = 27
        self.prevtrk        = 23
        self.autoplay       = 0
        self.track          = ""
        self.track_no       = 0
        self.drive_name     = ""
        self.que_dir        = self.m3u_dir + self.m3u_def + ".m3u"
        self.m              = 0
        self.counter5        = 0
        self.trackchangetime = time.time() + GAPTIME
        self.status = IDLE
        self.cmdbutton = PLAYING
        self.play_stopped = False
        
        if RunningOnPi:
            print (alsaaudio.mixers())
            if len(alsaaudio.mixers()) > 0:
                for mixername in alsaaudio.mixers():
                    self.m = alsaaudio.Mixer(mixername)
            self.m.setvolume(self.volume)
            self.gpio_enable = 1
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.stop_start,GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.nexttrk,GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.prevtrk,GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # setup GUI
        self.canvas = tk.Canvas(width=320, height=240)
        self.canvas.bind("<Key>", self.key)
        self.canvas.bind("<Button-1>", self.callback)
        self.canvas.pack()
        self.bgimg = ImageTk.PhotoImage(
            Image.open('Minibackground.png').resize((320, 240),
                Image.ANTIALIAS))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bgimg)
        self.titlefont     = tkinter.font.Font(
            family='KG Defying Gravity Bounce',
            size=28)
        self.artistfont     = tkinter.font.Font(
            family='Victoria',
            size=30)
        self.numberfont     = tkinter.font.Font(
            family='DotMatrix',
            size=20)
        self.title_id = None
        self.artist_id = None
        self.remining_id = None
        self.start_id = None
        self.stop_id = None
        self.startimg = ImageTk.PhotoImage(
            Image.open('play.png').resize((32, 32),
                Image.ANTIALIAS))
        self.stopimg = ImageTk.PhotoImage(
            Image.open('stop.png').resize((32, 32),
                Image.ANTIALIAS))
        self.canvas.focus_set()
        self.change_start_button()

        self.length = 27
            
        if RunningOnPi:
            self.Check_switches()

        # check default .m3u exists, if not then make it
        if not os.path.exists(self.que_dir):
            self.Create_Playlist()
        self.init_tunes()
        self.Show_Track()
       
    def change_start_button(self):
        if self.status == PLAYING and self.cmdbutton == IDLE:
            if self.stop_id:
                self.canvas.delete(self.stop_id)
                self.stop_id = None
            self.start_id = self.canvas.create_image(20,10, anchor=tk.NW,
                image=self.startimg)
            self.cmdbutton = PLAYING
        elif self.status == IDLE and self.cmdbutton == PLAYING:
            if self.start_id:
                self.canvas.delete(self.start_id)
                self.start_id = None
            self.stop_id = self.canvas.create_image(20,10, anchor=tk.NW,
                image=self.stopimg)
            self.cmdbutton = IDLE

    def init_tunes(self):
        Tracks = []
        with open(self.que_dir,"r") as textobj:
            line = textobj.readline()
            while line:
               Tracks.append(line.strip())
               line = textobj.readline()
        self.tunes = []
        for counter in range (0,len(Tracks)):
            z,self.drive_name1,self.drive_name2,self.drive_name,self.artist_name,self.album_name,self.track_name  = Tracks[counter].split('/')
            self.tunes.append(self.artist_name + "^" + self.album_name + "^" + self.track_name + "^" + self.drive_name + "^" + self.drive_name1 + "^" + self.drive_name2)

    def key(self, event):
        '''print("pressed", event.char)'''
        if event.char == 'w' and self.status == IDLE:
            self.Play()
        if event.char == 's' and self.status == PLAYING:
            self.Stop()
        if event.char == 'd':
            self.Next_Track()
        if event.char == 'a':
            self.Prev_Track()
        if event.char == 'q':
            quit()

    def callback(self, event):
        if time.time() < self.trackchangetime:
            return
        self.trackchangetime = time.time() + GAPTIME
        if event.y < 52:
            if self.status == PLAYING:
                print("clicked Stop", event.x, event.y)
                self.Stop()
            elif self.status == IDLE:
                print("clicked Play", event.x, event.y)
                self.Play()
        else:
            if event.x < 160:
                print("clicked Prev", event.x, event.y)
                self.Prev_Track()
            elif event.x > 160:
                print("clicked Next", event.x, event.y)
                self.Next_Track()

    def Check_switches(self):
        buttonPressed = False
        if GPIO.input(self.prevtrk)== 0:
            buttonPressed = True
            self.Prev_Track()
        elif GPIO.input(self.nexttrk)== 0:
            buttonPressed = True
            self.Next_Track()
        elif GPIO.input(self.stop_start) == 0:
            if self.status == PLAYING:
                buttonPressed = True
                self.Stop()
            elif self.status == IDLE:
                buttonPressed = True
                self.Play()
        if buttonPressed:
            self.after(200, self.Buttons_released)
        else:
            self.after(200, self.Check_switches)

    def Buttons_released(self):
        if self.status == IDLE:
            self.after(200, self.Check_switches)
            return
        buttonPressed = False
        if GPIO.input(self.prevtrk)== 0:
            buttonPressed = True
        elif GPIO.input(self.nexttrk)== 0:
            buttonPressed = True
        elif GPIO.input(self.stop_start) == 0:
            buttonPressed = True
        if buttonPressed:
            self.after(200, self.Buttons_released)
        else:
            self.after(200, self.Check_switches)

    def getline(self, str, breakpoint):
        if breakpoint is None:
            return str[0:TITLEHI] + ']\n[' + str[TITLEHI:]
        return str[0:breakpoint] + ']\n[' + str[breakpoint + 1:]

    def set_title(self, title):
        if self.title_id:
            self.canvas.delete(self.title_id)
        title_has_space = False
        title_has_lower = False
        for ch in title:
            if ch.islower():
                title_has_lower = True
            if ch == ' ' or ch == '_':
                title_has_space = True
        modded = ''
        breakpoints = []
        count = 0
        if title_has_lower == True and title_has_space == False:
            ''' Add spaces before every uppercase letter '''
            for ch in title:
                if ch.isupper():
                    if count == 0:
                        modded = modded + ch.lower()
                        count += 1
                    else:
                        modded = modded + '|' + ch.lower()
                        breakpoints.append(count)
                        count += 2
                if ch.islower():
                    modded = modded + ch
                    count += 1
        else:
            ''' Convert everything to lower case letters '''
            for ch in title:
                if ch.isupper():
                    modded = modded + ch.lower()
                    count += 1
                if ch.islower():
                    modded = modded + ch
                    count += 1
                if ch == ' ' or ch == '_':
                    modded = modded + '|'
                    breakpoints.append(count)
                    count += 1
        modded = '[' + modded + ']'
        goodbreak = 0
        extra = 0
        if len(modded) > TITLEHI:
            ''' Insert linebreak for first line '''
            goodbreak = 0
            extra = 1
            for b in breakpoints:
                if goodbreak == 0:
                    goodbreak = b
                if b > TITLELO and b < TITLEHI + 1:
                    goodbreak = b
            if goodbreak == 0:
                goodbreak = len(modded)
            elif len(modded) > goodbreak + extra:
                modded = self.getline(modded, goodbreak + extra)
                extra += 2
        if len(modded[goodbreak + extra:]) > TITLEHI:
            ''' Insert linebreaks for second line '''
            lastbreak = goodbreak
            for b in breakpoints:
                if b > lastbreak and goodbreak == lastbreak:
                    goodbreak = b
                if b > lastbreak and b - lastbreak > TITLELO and b - lastbreak < TITLEHI + 1:
                    goodbreak = b
            if len(modded) > goodbreak + extra:
                modded = self.getline(modded, goodbreak + extra)
        ''' Three lines is max for this display '''
        
        self.title_id = self.canvas.create_text(
            320/2, 240/2 - 2, anchor='center', justify='center',
            text=modded, font=self.titlefont, fill='red')

    def set_artist(self, artist):
        if self.artist_id:
            self.canvas.delete(self.artist_id)
        self.artist_id = self.canvas.create_text(
            320/2, 210, anchor='center',
            text=artist, font=self.artistfont)

    def set_remining_time(self, remining_time = None):
        if self.remining_id:
            self.canvas.delete(self.remining_id)
        if not remining_time is None:
            self.remining_id = self.canvas.create_text(
                310, 30, anchor='e',
                text=remining_time, font=self.numberfont, fill='light green')

    def tune(self):
        if 'mp4' in self.track:
            return 4000.0
        return 0.0

    def Show_Track(self):
        if len(self.tunes) > 0:
            self.artist_name,self.album_name,self.track_name,self.drive_name,self.drive_name1,self.drive_name2  = \
                self.tunes[self.track_no].split('^')
            self.track = os.path.join("/" + self.drive_name1,self.drive_name2,self.drive_name, self.artist_name,
                self.album_name, self.track_name)
            self.set_artist(self.artist_name)
            self.set_title(self.track_name[:-4])
            if os.path.exists(self.track):
                audio = MediaInfo.parse(self.track)
                self.track_len = (audio.tracks[0].duration + self.tune()) / 1000.0
                minutes = int(self.track_len // 60)
                seconds = int (self.track_len - (minutes * 60))
            
    def Play(self):
        self.autoplay = 1
        if self.status == IDLE:
            self.status = PLAYING
            self.Play_track()

    def Stop(self):
        self.status = IDLE
        self.autoplay = 0

    def Next_Track(self):
        if self.status == PLAYING:
            self.status = IDLE
            while self.play_stopped:
                time.sleep(0.2)
            self.inc_track()
        elif self.status == IDLE:
            self.inc_track()

    def Prev_Track(self):
        if self.status == PLAYING:
            self.status = IDLE
            while self.play_stopped:
                time.sleep(0.2)
            self.dec_track(2)
        elif self.status == IDLE:
            self.dec_track()

    def Play_track(self):
        if self.status == IDLE:
            return
        if os.path.exists(self.track):
            if 'mp3' in self.track or not RunningOnPi or UseOmxplayer == False:
                self.player.stop()
                if self.mp4playing:
                    os.killpg(self.p.pid, signal.SIGTERM)
                self.player.loadfile(self.track)
            else:
                self.player.stop()
                if self.mp4playing:
                    os.killpg(self.p.pid, signal.SIGTERM)
                if self.windowed:
                    rpistr = "omxplayer --win 800,90,1840,700 " + '"' + self.track + '"'
                else:
                    rpistr = "omxplayer --win 0,49,320,240 " + '"' + self.track + '"'
                self.p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
                self.mp4playing = True
            self.start = time.time()
        else:
            return
        self.play_stopped = False
        self.player.time_pos = 0
        self.show_remining_time()
        self.change_start_button()
        self.Play_track2()

    def Play_track2(self):
        if time.time() - self.start > self.track_len or self.status == IDLE:
            self.status = IDLE
            if self.mp4playing:
                os.killpg(self.p.pid, signal.SIGTERM)
                self.mp4playing = False
                self.player.stop()
            else:
                self.player.stop()
            self.show_remining_time()
            self.change_start_button()
            self.play_stopped = True
            if self.autoplay == 1:
                self.status = PLAYING
                self.inc_track()
            return
        self.show_remining_time()
        self.after(200, self.Play_track2)
            
    def show_remining_time(self):
        if self.status == IDLE:
            self.set_remining_time()
            return
        played = time.time() - self.start
        p_minutes = int(played // 60)
        p_seconds = int (played - (p_minutes * 60))
        lefttime = self.track_len - played
        minutes = int(lefttime // 60)
        seconds = int (lefttime - (minutes * 60))
        self.set_remining_time("%02d:%02d" % (minutes, seconds % 60))

    def inc_track(self):
        self.track_no +=1
        if self.track_no > len(self.tunes) -1:
            self.track_no = 0
        self.Show_Track()
        if self.autoplay == 1:
            self.status = PLAYING
            self.Play_track()
        else:
            self.status = IDLE

    def dec_track(self, val=1):
        for i in range(0,val):
            self.track_no -= 1
            if self.track_no < 0:
                self.track_no = len(self.tunes) -1
        self.Show_Track()
        if self.autoplay == 1:
            self.Play_track()
        else:
            self.status = IDLE
 
    def Create_Playlist(self):
        self.timer = time.time()
        if self.status == PLAYING:
            self.status = IDLE
            self.player.stop()
        if os.path.exists(self.m3u_dir + self.m3u_def + ".m3u"):
            os.remove(self.m3u_dir + self.m3u_def + ".m3u")
        self.Tracks = glob.glob(self.mp3_search)
        if len (self.Tracks) > 0 :
            with open(self.m3u_dir + self.m3u_def + ".m3u", 'w') as f:
                for item in sorted(self.Tracks):
                    f.write("%s\n" % item)

def main():
    root = Tk()
    root.title("ZeroPlayer")
    print('Screen', root.winfo_screenwidth(), root.winfo_screenheight())
    if root.winfo_screenwidth() == 800 and root.winfo_screenheight() == 480 and fullscreen == 1:
        root.wm_attributes('-fullscreen','true')
    elif root.winfo_screenwidth() == 320 and root.winfo_screenheight() == 240 and fullscreen == 1:
        root.wm_attributes('-fullscreen','true')
    elif root.winfo_screenwidth() == 640 and root.winfo_screenheight() == 480 and fullscreen == 1:
        root.wm_attributes('-fullscreen','true')
    elif root.winfo_screenwidth() == 480 and root.winfo_screenheight() == 800 and fullscreen == 1:
        root.wm_attributes('-fullscreen','true')
    ex = ZeroPlayer(root.winfo_screenwidth() != 320)
    root.geometry("320x240")
    root.mainloop() 

if __name__ == '__main__':
    main() 

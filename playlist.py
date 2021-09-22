import time, threading, os
from collections import OrderedDict

class StopWatch():
    def __init__(self):
        self.start_time = 0
        self.stop_time = 0
        self.time = 0
        self.isStop = True
    def start(self):
        if self.isStop:
            self.start_time = time.time() 
            self.isStop=False
        else:
            pass
    def stop(self):
        if self.isStop:
            pass
        else:
            self.time+=time.time()-self.start_time
            self.isStop=True
    def clear(self):
        self.time = 0
        self.stop_time=0
        self.isStop=True
    def getTime(self):
        if self.isStop:
            return self.time
        else:
            return self.time+(time.time()-self.start_time)
    def setTime(self, t):
        stoped=self.isStop
        try:
            self.stop()
        except:
            pass
        self.time=t
        if not stoped:
            self.start()

class Playlist():
    def __init__(self):
        self.thread=None
        self.state="stop"
        self.stopwatch=StopWatch()
        self.playlist=OrderedDict()
        self.channel=None
        self.loop=False
        self.play_callback=play_callback
        self.pause_callback=pause_callback
        self.stop_callback=stop_callback
        self.resume_callback=resume_callback
    def watcher(self):
        while 1:
            if len(self.playlist) != 0:
                data=list(self.playlist.values())[0]
            if self.state == "playing":
                self.stopwatch.clear()
                self.play_callback(self, data)
                self.stopwatch.start()
                self.state = "play"
            elif self.state == "skipping":
                self.stop_callback(self, data)
                self.playlist.pop(data["title"])
                threading.Thread(target=self._delfile, args=[data["path"]]).start()
                if len(self.playlist)!=0: self.state="playing"
                else: self.state="stoping"
            elif self.state == "pausing":
                self.pause_callback(self)
                self.stopwatch.stop()
                self.state="pause"
                while self.state == "pause":
                    time.sleep(0.1)
                if self.state == "resuming":
                    self.resume_callback(self)
                    self.stopwatch.start()
                    self.state="play"
                else:
                    pass
            elif self.state == "stoping":
                self.stopwatch.stop()
                self.stop_callback(self, data)
                self.playlist.pop(data["title"])
                self._delfile(data["path"])
                self.state="stop"
                return
            elif data["length"]+1 <= self.stopwatch.getTime():
                if len(self.playlist)>1:
                    self.state="playing"
                    if self.loop:
                        self.playlist.move_to_end(data["title"])
                    else:
                        self.playlist.pop(data["title"])
                        threading.Thread(target=self._delfile, args=[data["path"]]).start()
                elif len(self.playlist)==1:
                    self.state="stopping"
                else:
                    if self.loop:
                        pass
                    else:
                        self.state="stopping"
                
            time.sleep(0.1)
    def add(self, length, title, path, user, nico=None):
        self.playlist[title]={"title":title, "length":length, "path":path, "nico":nico, "user":user}
    def play(self):
        self.thread=threading.Thread(target=self.watcher)
        self.state="playing"
        self.thread.start()
    def skip(self):
        self.state="skipping"
    def stop(self):
        self.state="stoping"
    def pause(self):
        self.state="pausing"
    def resume(self):
        self.state="resuming"
    def _delfile(self, path):
        while os.path.exists(path):
            try:
                os.remove(path)
            except:
                time.sleep(1)
            else:
                break
    def cleanup(self):
        for i in self.playlist:
            if os.path.exists(self.playlist[i]["path"]): os.remove(self.playlist[i]["path"])
        self.playlist=OrderedDict()
def play_callback(self, data):
    pass
def pause_callback(self):
    pass
def stop_callback(self):
    pass
def resume_callback(self):
    pass
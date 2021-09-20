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
        self.play_callback=play_callback
        self.pause_callback=pause_callback
        self.stop_callback=stop_callback
    def watcher(self):
        while 1:
            data=list(self.playlist.values())[0]
            if self.state == "playing":
                self.stopwatch.clear()
                self.play_callback(self, data)
                self.stopwatch.start()
                self.state = "play"
            elif data["length"]+1 <= self.stopwatch.getTime():
                self.playlist.pop(data["title"])
                threading.Thread(target=self._delfile, args=[data["path"]]).start()
                if len(self.playlist)!=0: self.state="playing"
            elif self.state == "skipping":
                self.stop_callback(self)
                self.playlist.pop(data["title"])
                threading.Thread(target=self._delfile, args=[data["path"]]).start()
                if len(self.playlist)!=0: self.state="playing"
            elif self.state == "pausing":
                self.pause_callback(self)
                self.stopwatch.stop()
                self.state="pause"
                while self.state == "pause":
                    time.sleep(0.1)
                self.play_callback(self, data)
                self.stopwatch.start()
            elif self.state == "stoping":
                self.stopwatch.stop()
                self.stop_callback(self)
                self.state="stop"
                return
            time.sleep(0.1)
    def add(self, length, title, path):
        self.playlist[title]={"title":title, "length":length, "path":path}
    def play(self):
        self.thread=threading.Thread(target=self.watcher)
        self.state="playing"
        self.thread.start()
    def skip(self):
        self.state="skipping"
    def stop(self):
        self.state="stoping"
    def _delfile(self, path):
        while os.path.exists(path):
            try:
                os.remove(path)
            except:
                time.sleep(1)
            else:
                break
def play_callback(self, data):
    pass
def pause_callback(self):
    pass
def stop_callback(self):
    pass
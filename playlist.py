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
        self.move2=False
        self.play_callback=play_callback
        self.pause_callback=pause_callback
        self.stop_callback=stop_callback
        self.resume_callback=resume_callback
    def add(self, length, title, path, user, nico=None):
        self.playlist[title]={"title":title, "length":length, "path":path, "nico":nico, "user":user}
    def play(self):
        if len(self.playlist) != 0:
            data=list(self.playlist.values())[0]
            self.stopwatch.clear()
            self.play_callback(self, data)
            self.stopwatch.start()
            self.state = "play"
        else:
            pass
    def skip(self):
        if len(self.playlist)!=0:
            data=list(self.playlist.values())[0]
            self.stop_callback(self, data)
            self.playlist.pop(data["title"])
            threading.Thread(target=self._delfile, args=[data["path"]]).start()
            self.play()
        else:
            self.stop()
    def stop(self):
        if len(self.playlist)!=0:
            data=list(self.playlist.values())[0]
            self.stopwatch.stop()
            self.stop_callback(self, data)
            self.playlist.clear()
            threading.Thread(target=self._delfile, args=[data["path"]]).start()
            self.state="stop"
    def pause(self):
        self.pause_callback(self)
        self.stopwatch.stop()
        self.state="pause"
    def resume(self):
        self.resume_callback(self)
        self.stopwatch.start()
        self.state="play"
    def _delfile(self, path):
        while os.path.exists(path):
            try:
                os.remove(path)
            except:
                time.sleep(1)
            else:
                break
    def next(self, exp):
        if len(self.playlist)>1:
            data=list(self.playlist.values())[0]
            if self.loop:
                self.playlist.move_to_end(data["title"])
            else:
                self.playlist.pop(data["title"])
                threading.Thread(target=self._delfile, args=[data["path"]]).start()
            self.play()
        elif len(self.playlist)==1:
            if self.loop:
                self.play()
            else:
                self.stop()
        else:
            pass
    def cleanup(self):
        for i in self.playlist:
            if os.path.exists(self.playlist[i]["path"]): os.remove(self.playlist[i]["path"])
        self.playlist=OrderedDict()
def play_callback(self, data):
    pass
def pause_callback(self):
    pass
def stop_callback(self, data):
    pass
def resume_callback(self):
    pass
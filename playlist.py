import time, threading, os, random
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
    def __init__(self, parent):
        self.thread=None
        self.state="stop"
        self.stopwatch=StopWatch()
        self.playlist=OrderedDict()
        self.channel=None
        self.loop=False
        self.move2=False
        self.skiped=False
        self.shuffle=False
        self.parent=parent
        self.play_callback=play_callback
        self.pause_callback=pause_callback
        self.stop_callback=stop_callback
        self.resume_callback=resume_callback
    def add(self, length, title, path, user, url, nico=None):
        self.playlist[title]={"title":title, "length":length, "path":path, "nico":nico, "user":user, "uid":user.id, "url": url}
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
            self.skiped=True
            self.stop_callback(self, data)
        else:
            self.stop()
    def stop(self, save=False):
        if len(self.playlist)!=0:
            data=list(self.playlist.values())[0]
            self.stopwatch.stop()
            try:
                self.stop_callback(self, data)
            except:
                pass
            if save:
                self.save()
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
        if type(path) == str: 
            while os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    time.sleep(1)
                else:
                    break
    def next(self, exp):
        if self.state!="play"  or len(self.channel.channel.members) == 0:
            return
        while self.channel.is_playing():
            time.sleep(0.1)
        if not exp is None:
            time.sleep(1)
            self.play()
            return
        if len(self.playlist)>1:
            data=list(self.playlist.values())[0]
            if self.shuffle:
                self.playlist.move_to_end(random.choice(self.playlist.keys()), False)
            if self.loop:
                #if self.skiped:
                self.playlist.move_to_end(data["title"])
            else:
                self.playlist.pop(data["title"])
                threading.Thread(target=self._delfile, args=[data["path"]]).start()
            self.skiped=False
            self.play()
        elif len(self.playlist)==1:
            if self.loop:
                self.play()
            else:
                self.stop()
        else:
            pass
    def save(self, name="saved"):
        temp={}
        for music in self.playlist:
            temp[music]={"title":self.playlist[music]["title"], "length":self.playlist[music]["length"], "path":self.playlist[music]["path"], "user":self.playlist[music]["uid"], "url":self.playlist[music]["url"]}
        self.parent.data["playlists"][name]=temp
        self.parent._syncData()
def play_callback(self, data):
    pass
def pause_callback(self):
    self.channel.pause()
def stop_callback(self, data):
    if not data["nico"] is None:
        data["nico"].close()
    self.channel.stop()
def resume_callback(self):
    self.channel.resume()
class PlayList():
    def __init__(self):
        self.playlist={}
        self.playing=False
    def add(self, length, title):
        self.playlist[title]={}
    def stop(self):
        pass

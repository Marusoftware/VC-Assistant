import os, pickle
from playlist import Playlist
playlist_list=[]
class Data():
    def __init__(self, data_dir=""):
        self.data_dir=data_dir
        self.loaded_guilds={}
    def getGuildData(self, guild_id):
        if guild_id in self.loaded_guilds:
            return self.loaded_guilds[guild_id]
        else:
            guild=GuildData(guild_id, self.data_dir)
            self.loaded_guilds[guild_id]=guild
            return guild
class GuildData():
    def __init__(self, guild_id, data_dir):
        self.data_dir=data_dir#HERE:Guild DB Directory
        self.data_path=os.path.join(self.data_dir,str(guild_id)+".guild")
        if os.path.exists(self.data_path):
            self.data = pickle.load(open(self.data_path, "rb"))
        else:
            self.data = {"prefix":"!", "matcher_dict":{}, "enMatcher":False, "enMusic":True}
            self._syncData()
        self.playlist=Playlist()
        playlist_list.append(self.playlist)
    def _syncData(self):
        pickle.dump(self.data, open(self.data_path, "wb"))
    def getProperty(self, property_name):
        if not property_name in self.data:
            return False
        else:
            return self.data[property_name]
    def setProperty(self, property_name, value):
        self.data[property_name]=value
        self._syncData()
    def getMatcherDict(self):
        return self.data["matcher_dict"]
    def addMatcherDict(self, pattern, check_type, text):
        self.data["matcher_dict"][pattern]=(check_type, text)
    def delMatcherDict(self, pattern):
        self.data["matcher_dict"].pop(pattern)
    def getPlaylist(self):
        return self.playlist
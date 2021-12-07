import os, pickle
from playlist import Playlist
if "DATABASE_URL" in os.environ:
    import psycopg2
    import psycopg2.extras
    db_url=os.environ["DATABASE_URL"]
else:
    db_url=None

def getGidlist(datas):
    l = list()
    for d in datas:
        l.append(d["gid"])
    return l

class Data():
    def __init__(self, data_dir=""):
        self.data_dir=data_dir
        self.loaded_guilds={}
        self.playlists=[]
        self.command_perms={}
        self.perms={"DJ":{"desc":"", "def":False}}
    def getGuildData(self, guild_id):
        if guild_id in self.loaded_guilds:
            return self.loaded_guilds[guild_id]
        else:
            guild=GuildData(self, guild_id, self.data_dir)
            self.loaded_guilds[guild_id]=guild
            return guild
class GuildData():
    def __init__(self, data_obj, guild_id, data_dir):
        self.data_dir=data_dir#HERE:Guild DB Directory
        self.guild_id=guild_id
        self.data_path=os.path.join(self.data_dir,str(guild_id)+".guild")
        self.default_data = {"prefix":"!", "matcher_dict":{}, "enMatcher":False, "enMusic":True,
                             "keyYoutube":"none", "TTSChannels":[], "enTTS":False, "playlists":{},
                             "perms":{}}
        if db_url:
            self.conn = psycopg2.connect(db_url)
            cursor=self.conn.cursor()
            cursor.execute("create table if not exists datas(gid text, data bytea)")
            self.conn.commit()
            cursor.close()
            cursor=self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("select * from datas")
            datas=cursor.fetchall()
            cursor.close()
            if str(guild_id) in getGidlist(datas):
                for data in datas:
                    if data["gid"] == str(guild_id):
                        self.data=pickle.loads(data["data"].tobytes())
                        break
            else:
                self.data=self.default_data
                self._syncData()
        else:
            if os.path.exists(self.data_path):
                self.data = pickle.load(open(self.data_path, "rb"))
            else:
                self.data=self.default_data
                self._syncData()
        for index in self.default_data:
            if not index in self.data:
                self.data[index]=self.default_data[index]
        self.playlist=Playlist(parent=self)
        data_obj.playlists.append(self.playlist)
    def _syncData(self):
        if db_url:
            cursor=self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute("select * from datas")
            datas=cursor.fetchall()
            cursor.close()
            if str(self.guild_id) in getGidlist(datas):
                cursor=self.conn.cursor()
                cursor.execute("delete from datas where gid = %s", (str(self.guild_id),))
                self.conn.commit()
                cursor.close()
            cursor=self.conn.cursor()
            cursor.execute("insert into datas (gid, data) values (%s, %s)", (str(self.guild_id),psycopg2.Binary(pickle.dumps(self.data)),))
            self.conn.commit()
            cursor.close()
        else:
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
        if check_type == "event":
            self.data["matcher_dict"]["on_"+pattern]=(check_type, text)
        else:
            self.data["matcher_dict"][pattern]=(check_type, text)
        self._syncData()
    def delMatcherDict(self, pattern, check_type):
        if check_type == "event":
            self.data["matcher_dict"].pop(pattern)
        else:
            for pt in self.data["matcher_dict"]:
                if pt.pattern == pattern:
                    self.data["matcher_dict"].pop(pt)
                    break
        self._syncData()
    def getPlaylist(self):
        return self.playlist
    def getTTSChannels(self):
        return self.data["TTSChannels"]
    def switchTTSChannel(self, channel):
        if channel.id in self.data["TTSChannels"]:
            self.data["TTSChannels"].remove(channel.id)
            self._syncData()
            return False
        else:
            self.data["TTSChannels"].append(channel.id)
            self._syncData()
            return True
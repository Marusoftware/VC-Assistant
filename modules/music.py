from email.policy import default
from discord.ext import commands, bridge
from discord import SelectOption, Option, Member, Embed
import discord, re, datetime
from pytube.streams import Stream
from pytube import YouTube, Search, Playlist
from pytube.exceptions import LiveStreamError
from apiclient.discovery import build
from niconico_dl import NicoNicoVideo
from discord.ui import Select, View, Button
from lib import _getGuildId, Send, randomstr

class MusicSelction(Select):
    def __init__(self, custom_id:str, urllist:list, parent, max_values=1):
        super().__init__(custom_id=custom_id, options=urllist,max_values=max_values, placeholder="Select Music from here.")
        self.urllist=urllist
        self.parent=parent
    async def callback(self, interaction):
        if len(self.values) == 1:
            view=View(timeout=0)
            view.add_item(TFButton(True, callback=self.ok, data=interaction))
            view.add_item(TFButton(False, callback=self.cancel, data=None))
            await interaction.response.send_message(content=f'Is this OK? \n "{self.values[0]}" ', view=view)
        else:
            await interaction.message.edit(content=f'Prepareing playing Musics...', view=None)
            await self.play(interaction)
    async def ok(self, interaction, data):
        await interaction.message.delete()
        await data.message.edit(content=f'Prepareing playing Music... \n {self.values[0]}', view=None)
        await self.play(data)
    async def play(self, interaction):
        text=""
        for value in self.values:
            status=await self.parent.play_music(value, interaction.guild.voice_client, interaction.user, stream=len(self.values)>1, stream_ex=len(self.values)>5)
            text+=await self.parent.status2msg(status, value)
        await interaction.message.edit(content=text, view=None)
    async def cancel(self, interaction, data):
        await interaction.message.delete()

class TFButton(Button):
    def __init__(self, boolen:bool, callback, data):
        if boolen:
            style=discord.ButtonStyle.green
            label="OK"
            emoji="⭕"
        else:
            style=discord.ButtonStyle.gray
            label="Cancel"
            emoji="❌"
        self.cb=callback
        self.data=data
        super().__init__(style=style, label=label, emoji=emoji)
    async def callback(self, interaction):
        await self.cb(interaction, self.data)

class Music(commands.Cog, name="music", description="Music playback and record."):
    def __init__(self, bot):
        self.bot=bot
        self.data=bot.data
        self.recodings=[]
    ##Event
    #Auto disconnect
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        playlist = self.data.getGuildData(_getGuildId(member)).getPlaylist()
        try:
            if len(playlist.channel.channel.members) <= 1 and not playlist.move2:
                playlist.stop(save=True)
                await playlist.channel.disconnect()
            else:
                playlist.move2 = False
        except AttributeError:
            pass
    ##Utils
    #StoTime
    def StoTime(self, s, length=None):
        t=datetime.timedelta(seconds=int(s))
        if length is None:
            return str(t)
        else:
            t2=datetime.timedelta(seconds=int(length))
            text=""
            try:
                for i in range(int((s/length)*10)):
                    text+="="
            except ZeroDivisionError:
                text="====∞===="
                return f'{text} {str(t)}/∞(Live)'
            else:
                text+="○"
                text=text.ljust(10, "=")
                return f'{text} {str(t)}/{str(t2)}'
    #state2emoji
    def state2emoji(self, state):
        if state == "play":
            return ":arrow_forward:"
        elif state == "pause":
            return ":pause_button:"
        elif state == "stop":
            return ":stop_button:" 
        else:
            return ":grey_question:"
    #statusToMessage
    async def status2msg(self, status, value=None, msg=None, options={}):
        if value is None:
            value=""
        else:
            value=f'"{value}"'
        if status == 0:
            text=f'Start playing {value}.\n'
        elif status == 1:
            text=f'Added to queue {value}.\n'
        else:
            text=f'Oh...Some Error occured...\n'
        if msg is None:
            return text
        else:
            await msg.edit(text, **options)
    #connect
    async def connect(self, channel):
        try:
            if channel.guild.voice_client is None:
                await channel.connect()
            else:
                await channel.guild.voice_client.move_to(channel)
        except:
            return False
        else:
            playlist=self.data.getGuildData(_getGuildId(channel)).getPlaylist()
            playlist.channel=channel.guild.voice_client
            playlist.play_callback=Music.play_callback
            playlists=self.data.getGuildData(_getGuildId(channel)).getProperty("playlists")
            if "saved" in playlists:
                if len(playlists["saved"]) !=0:
                    return playlists["saved"]
                else:
                    return True
            else:
                return True
    #search
    async def search_music(self, ctx, query, service):
        urllist=[]
        if service == "search-nico":
            query=query.replace("nico:","")
            import json, urllib.request
            params = {
                'q':query,
                'targets':'title,description,tags',
                'fields':'contentId,title',
                '_sort':'-viewCounter',
                '_context':'vc-assistant-nico',
                '_limit':5,
            }
            req = urllib.request.Request(f'https://api.search.nicovideo.jp/api/v2/snapshot/video/contents/search?{urllib.parse.urlencode(params)}')
            res = json.loads(urllib.request.urlopen(req).read())
            if res["meta"]["status"] != 200:
                return False
            else:
                for item in res["data"]:
                    title=item["title"]
                    if len(title)>90:
                        title=title[0:90]
                    urllist.append(SelectOption(label=title,value=f'https://www.nicovideo.jp/watch/{item["contentId"]}'))
                return urllist
        elif service == "search-spotify":
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
            client_id=self.bot.argv.spot
            client_secret=self.bot.argv.spotse
            spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
            query=query.replace("spot:","")
            results=spotify.search(query, limit=5, type="track")
            for item in results["tracks"]["items"]:
                title=item["name"]
                if len(title)>90:
                    title=title[0:90]
                urllist.append(SelectOption(label=title, value=f'{item["external_urls"]["spotify"]}'))
            return urllist
        else:
            key=self.data.getGuildData(_getGuildId(ctx)).getProperty("keyYoutube")
            if key == "none":
                yts=Search(query=query).results
                for yt in yts:
                    if len(urllist) > 5:
                        break
                    if yt.age_restricted:
                        continue
                    try:
                        yt.check_availability()
                    except LiveStreamError:
                        live="🎥"
                    else:
                        live=None
                    title=yt.title
                    if len(yt.title)>90:
                        title=yt.title[0:90]
                    else:
                        title=yt.title
                    if len(yt.author)>90:
                        channel=yt.author[0:90]
                    else:
                        channel=yt.author
                    urllist.append(SelectOption(label=title,value=yt.watch_url, emoji=live, description=channel))
                return urllist
            else:
                youtube = build('youtube', 'v3', developerKey=key)
                youtube_query = youtube.search().list(q=query, part='id,snippet', maxResults=5, safeSearch="strict")
                youtube_res = youtube_query.execute()
                url=youtube_res.get('items', [])
                for item in url:
                    if item['id']['kind'] == 'youtube#video':
                        vid_info=item["snippet"]
                        if len(vid_info["title"])>90:
                            title=vid_info["title"][0:90]
                        else:
                            title=vid_info["title"]
                        if len(vid_info["channelTitle"])>90:
                            channel=vid_info["channelTitle"][0:90]
                        else:
                            channel=vid_info["channelTitle"]
                        urllist.append(SelectOption(label=title,value=f'https://www.youtube.com/watch?v={item["id"]["videoId"]}', description=channel))
                return urllist
    #playlist
    async def get_playlist(self, ctx, query, service, select=True):
        urllist=[]
        if service in ["playlist-youtube","playlist-youtube-all"]:
            pl=Playlist(query)
            for item in pl.videos:
                title=item.title
                if len(title)>90:
                    title=title[0:90]
                if select:
                    urllist.append(SelectOption(label=title,value=item.watch_url))
                else:
                    urllist.append(item.watch_url)
            return urllist
        elif service in ["save", "save-select"]:
            save=self.data.getGuildData(_getGuildId(ctx)).data["playlists"][query]
            for item in save:
                title=item
                if len(title)>90:
                    title=title[0:90]
                if select:
                    urllist.append(SelectOption(label=title,value=save[item]["url"]))
                else:
                    urllist.append(save[item]["url"])
            return urllist
    #play
    async def play_music(self, url, channel, user, service="detect", stream=False, stream_ex=False):
        if service == "detect":
            service=self.service_detection(url)
        if service == "youtube":
            try:
                yt = YouTube(url=url)
                st:Stream=yt.streams.get_audio_only()
                if stream_ex:
                    path=st.url
                elif stream:
                    path=st
                else:
                    path=st.download(output_path=self.bot.argv.path, filename_prefix=randomstr(5), timeout=1000)
            except LiveStreamError:
                path=yt.streaming_data["hlsManifestUrl"]
            except:
                print("Music error(Youtube)")
            self.data.getGuildData(_getGuildId(channel)).getPlaylist().add(yt.length, yt.title, path, user, url)
        elif service == "nico":
            nico=NicoNicoVideo(url=url)
            nico.connect()
            data=nico.get_info()
            self.data.getGuildData(_getGuildId(channel)).getPlaylist().add(data["video"]["duration"], data["video"]["title"], nico.get_download_link(), user, url, nico=nico)
        elif service == "file":
            import ffmpeg
            self.data.getGuildData(_getGuildId(channel)).getPlaylist().add(int(float(ffmpeg.probe(url)["streams"][0]["duration"])), stream, url, user, url)
        elif service == "spotify":
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
            client_id=self.bot.argv.spot
            client_secret=self.bot.argv.spotse
            spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
            track=spotify.track(url)
            music=await self.search_music(channel, track["album"]["name"], "search-youtube")[0]
            await self.play_music(music.value, channel, user, service="youtube")
        else:
            return -1
        if channel.is_playing():
            return 1
        elif len(self.data.getGuildData(_getGuildId(channel)).getPlaylist().playlist)>1:
            return 1
        else:
            self.data.getGuildData(_getGuildId(channel)).getPlaylist().play()
            return 0
    #play_callback(internal)
    def play_callback(self, data):
        if type(data["path"]) == str:
            if ".m3u8" in data["path"]:
                self.channel.play(discord.FFmpegPCMAudio(data["path"], options="-vn -hls_allow_cache 1"), after=self.next)
            else:
                self.channel.play(discord.FFmpegPCMAudio(data["path"], options='-vn -af loudnorm -hls_allow_cache 1 -fflags +discardcorrupt'), after=self.next)
        else:
            path=data["path"].download(output_path=self.bot.argv.path, filename_prefix=randomstr(5), timeout=1000)
            self.playlist[list(self.playlist.keys())[0]]["path"]=path
            self.channel.play(discord.FFmpegPCMAudio(path, options="-vn -af loudnorm -fflags +discardcorrupt"), after=self.next)
    #service_detector
    def service_detection(self, url):
        if re.match("https?://(\S+\.)?youtube\.com/watch\?v=(\S)+",url):
            return "youtube"
        elif re.match("https?://(\S+\.)?nicovideo\.jp/watch/(\S)+",url):
            return "nico"
        elif re.match("https?://(\S+\.)?youtube\.com/playlist\?list=(\S)+",url):
            return "playlist-youtube"
        elif re.match("https?://open.spotify.com/track/(\S)+",url):
            return "spotify"
        elif re.match("nico:(\S)+", url):
            return "search-nico"
        elif re.match("spot:(\S)+", url):
            return "search-spotify"
        elif re.match("all:(\S)+", url):
            return "playlist-youtube-all"
        elif re.match("save:(\S)+", url):
            return "save"
        elif re.match("savel:(\S)+", url):
            return "save-select"
        elif "file" in url:
            return "file"
        else:
            return "search-youtube"
    ##Body
    #join
    @bridge.bridge_command(name="join", aliases=["j"], description="join to VC")
    async def join(self, ctx, channel:Option(discord.VoiceChannel, "VC", required=False, default=None), restore:Option(bool, "Restore latest playing.", required=False, default=True)):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
            await ctx.respond('Music is not enabled.', ephemeral=True)
            return
        if isinstance(ctx.author, Member):
            if ctx.author.voice is None and channel is None:
                await ctx.respond("Please assign or enter to VC.", ephemeral=True)
            else:
                if channel is None:
                    state=await self.connect(ctx.author.voice.channel)
                    channel=ctx.author.voice.channel
                else:
                    state=await self.connect(channel)
                if state!=False:
                    if type(state) == dict and restore:
                        msg=await ctx.respond("Connected to VC(And restoreing latest session.)")
                        for music in state:
                            await self.play_music(state[music]["url"], ctx.guild.voice_client, self.bot.get_user(state[music]["user"]), stream=len(state)>1, stream_ex=len(state)>5)
                        await msg.edit("Connected to VC(And restored latest session.)")
                        self.data.getGuildData(_getGuildId(ctx)).data["playlists"].pop("saved")
                        self.data.getGuildData(_getGuildId(ctx))._syncData()
                    else:
                        await ctx.respond("Connected to VC")
                else:
                    await ctx.respond("Sorry... Can't connect to VC....", ephemeral=True)
        else:
            await ctx.respond("Now no support for DM...Sorry...", ephemeral=True)
    #record
    @bridge.bridge_command(name="record", aliases=["rec"], description="Record VC")
    async def record(self, ctx, encoding:Option(str,choices=["mp3","wav","pcm","ogg","mka","mkv","mp4","m4a"], default="mp3", required=False)):
        if ctx.guild.id in self.recodings:
            ctx.guild.voice_client.stop_recording()
            await ctx.respond("The recording has stoped!")
            self.recodings.remove(ctx.guild.id)
        else:
            if encoding == "mp3":
                sink = discord.sinks.MP3Sink()
            elif encoding == "wav":
                sink = discord.sinks.WaveSink()
            elif encoding == "pcm":
                sink = discord.sinks.PCMSink()
            elif encoding == "ogg":
                sink = discord.sinks.OGGSink()
            elif encoding == "mka":
                sink = discord.sinks.MKASink()
            elif encoding == "mkv":
                sink = discord.sinks.MKVSink()
            elif encoding == "mp4":
                sink = discord.sinks.MP4Sink()
            elif encoding == "m4a":
                sink = discord.sinks.M4ASink()
            else:
                return await ctx.respond("Invalid encoding.")
            ctx.guild.voice_client.start_recording(
                sink,
                self.finished_callback,
                ctx.channel,
            )
            await ctx.respond("The recording has started!")
            self.recodings.append(ctx.guild.id)
    async def finished_callback(self, sink, channel: discord.TextChannel, *args):
        recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
        await sink.vc.disconnect()
        files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()]
        await channel.send(f"Finished! Recorded audio for {', '.join(recorded_users)}.", files=files)
    #play
    @commands.command(name="play", aliases=["p"], description="Play in VC")
    async def play(self, ctx, *query):
        if type(query) != str:
            query=" ".join(query)
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
            await Send(ctx, 'Music is not enabled.', ephemeral=True)
            return
        if ctx.guild.voice_client is None:
            if ctx.author.voice is None:
                await Send(ctx, "Wasn't connected to VC")
                return
            else:
                await self.connect(ctx.author.voice.channel)
                await Send(ctx, "Wasn't connected to VC. But you connected VC, So I connect there.")
        service=self.service_detection(query)
        if service in ["youtube","nico"]:
            msg = await Send(ctx, content=f'Prepareing playing...', mention_author=True)
            status=await self.play_music(query, ctx.guild.voice_client, ctx.author, service)
            await self.status2msg(status, msg=msg)
        elif service in ["playlist-youtube", "save-select"]:
            query=query.replace("savel:","")
            msg=await Send(ctx, "Processing...")
            urllist=await self.get_playlist(ctx, query, service)
            if urllist:
                n=int(len(urllist)/25)
                view=View(timeout=None)
                for i in range(n):
                    view.add_item(MusicSelction(custom_id="test"+str(i), urllist=urllist[i*25:i*25+25], parent=self, max_values=25))
                if not len(urllist)%25 == 0:
                    view.add_item(MusicSelction(custom_id="test", urllist=urllist[len(urllist)%25*-1:], parent=self, max_values=len(urllist)%25))
                await msg.edit("Select Music to Play.(Multiple is OK)",view=view)
            else:
                await msg.edit("Error in Searching Music.")
        elif service in ["playlist-youtube-all", "save"]:
            message = await Send(ctx, "Processing...")
            query=query.replace("all:","")
            query=query.replace("save:","")
            urllist=await self.get_playlist(ctx, query, service, select=False)
            if len(urllist) == 1:
                await message.edit(content=f'Prepareing playing "{urllist[0]}"...', view=None)
            else:
                await message.edit(content='Prepareing playing Musics...', view=None)
            text=""
            for value in urllist:
                status=await self.play_music(value, ctx.guild.voice_client, ctx.author, stream=len(urllist)>1, stream_ex=len(urllist)>5)
            await self.status2msg(0,msg=message, value=(None if len(urllist)<2 else f'And {len(urllist)-1} musics were added to queue'))
        elif service == "file":
            if len(ctx.message.attachments) != 0:
                file=ctx.message.attachments[0]
                msg = await Send(ctx, content='Prepareing playing...', mention_author=True)
                status=await self.play_music(file.url, ctx.guild.voice_client, ctx.author, "file", file.filename)
                await self.status2msg(status, msg=msg)
            else:
                msg = await Send(ctx, content="Wrong Attachment.(just one attachment is required.)", mention_author=True)
        else:
            msg=await Send(ctx, "Searching...")
            urllist=await self.search_music(ctx, query, service)
            if urllist:
                view=View(timeout=None)
                view.add_item(MusicSelction(custom_id="test", urllist=urllist, parent=self))
                await msg.edit("Select Music to Play.",view=view)
            else:
                await msg.edit("Error in Searching Music.")
    @commands.slash_command(name="play", description="Play music on VC")
    async def play_sl(self, ctx, query:Option(str, "Search text or url", required=True), service:Option(str, "Service", required=False, choices=["youtube","nico","playlist-youtube","search-youtube","search-nico","playlist-youtube-all","save","savel"], default="detect")):
        await self.play(ctx, query)
    #skip
    @bridge.bridge_command(name="skip", aliases=["s"], description="Skip Music")
    async def skip(self, ctx):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
            await ctx.respond('Music is not enabled.')
            return
        if not ctx.guild.voice_client is None:
            await ctx.respond('Skiping Music...')
            self.data.getGuildData(_getGuildId(ctx)).getPlaylist().skip()
    #pause
    @bridge.bridge_command(name="pause", aliases=["pa"], description="Pause Music")
    async def pause(self, ctx):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
            await ctx.respond('Music is not enabled.')
            return
        if not ctx.guild.voice_client is None:
            await ctx.respond('Pausing Music...')
            self.data.getGuildData(_getGuildId(ctx)).getPlaylist().pause()
    #resume
    @bridge.bridge_command(name="resume", aliases=["re"], description="Resume Music")
    async def resume(self, ctx):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
            await ctx.respond('Music is not enabled.')
            return
        if not ctx.guild.voice_client is None:
            await ctx.respond('Resuming Music...')
            self.data.getGuildData(_getGuildId(ctx)).getPlaylist().resume()
    #stop
    @bridge.bridge_command(name="stop", aliases=["st"], description="Stop Music")
    async def stop(self, ctx):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
            await ctx.respond('Music is not enabled.')
            return
        if not ctx.guild.voice_client is None:
            await ctx.respond('Stop playing...')
            self.data.getGuildData(_getGuildId(ctx)).getPlaylist().stop()
    #nowplaying
    @bridge.bridge_command(name="nowplaying", aliases=["np"], description="Show playing Music.")
    async def np(self, ctx):
        data=self.data.getGuildData(_getGuildId(ctx))
        if not data.getProperty("enMusic"):
            await ctx.respond('Music is not enabled.', ephemeral=True)
            return
        playlist=data.getPlaylist()
        if len(playlist.playlist)!=0:
            music=list(playlist.playlist.keys())[0]
            embed=Embed(title=playlist.playlist[music]["title"], description=f'{self.state2emoji(playlist.state)}{self.StoTime(playlist.stopwatch.getTime(),playlist.playlist[music]["length"])}')
            user=playlist.playlist[music]["user"]
            embed.set_author(name=user, icon_url=user.avatar)
            if playlist.loop:
                embed.add_field(name="Loop", value="Enabled!!:repeat:")
            await ctx.respond("", embed=embed)
        else:
            await ctx.respond("Now, No Music is playing...")
    #showq
    @bridge.bridge_command(name="showq", aliases=["q"], description="Show queued Music.")
    async def showq(self, ctx):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
            await ctx.respond('Music is not enabled.', ephemeral=True)
            return
        pl=self.data.getGuildData(_getGuildId(ctx)).getPlaylist()
        if len(pl.playlist)!=0:
            playlist=pl.playlist
            embed=Embed(title="Queue", description=f'Now, {len(playlist)} musics are in queue. Total time is {self.StoTime(sum([playlist[m]["length"] for m in playlist]))}.{":repeat:" if pl.loop else ""}')
            n=0
            for music in playlist:
                n+=1
                embed.add_field(name=f'{str(n)}"{playlist[music]["title"]}"', value=f'[{self.StoTime(playlist[music]["length"])}]', inline=False)
            if len(playlist) > 25:
                embed.set_footer(text=f'{len(playlist)-25} musics are after these.')
            await ctx.respond("", embed=embed)
        else:
            await ctx.respond("Now, No Music(s) is in queue...")
    #getsaved
    @bridge.bridge_command(name="getsaved", aliases=["gsv"])#TODO: option to select save
    async def getsaved(self, ctx):
        temp=""
        saved=self.data.getGuildData(_getGuildId(ctx)).data["playlists"]
        for i in saved:
            temp+=f'{i} : `{",".join(list(saved[i].keys()))}\n`'
        if len(temp)==0:
            temp="Saved music list is not found."
        await ctx.respond(temp)
    #save
    @bridge.bridge_command(name="save", aliases=["sv"], description="Save queued Music.")
    async def save(self, ctx, id:Option(int, description="An ID for save.", required=True)):
        self.data.getGuildData(_getGuildId(ctx)).playlist.save(id)
        await ctx.respond("Saved.")
    #del
    @bridge.bridge_command(name="delete", aliases=["del","d"], description="Delete queued Music/Save.")
    async def delete(self, ctx, index:Option(str, "Music Index", required=True)):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
            await ctx.respond('Music is not enabled.')
            return
        if index.startswith("save:"):
            index=index.replace("save:","")
            self.data.getGuildData(_getGuildId(ctx)).data["playlists"].pop(index)
            await ctx.respond("Delete Save")
        else:
            index=int(index)-1
            if index == 0:
                await ctx.respond("If you want to delete Index 1, please use skip.")
                return
            if not ctx.guild.voice_client is None:
                playlist=self.data.getGuildData(_getGuildId(ctx)).getPlaylist().playlist
                playlist.pop(list(playlist.keys())[index])
                await ctx.respond("Delete Music")
    #movetoend
    @bridge.bridge_command(name="movetoend", aliases=["mv","m"], description="Move queued Music to end.")
    async def movetoend(self, ctx, index:Option(int, "Music Index", required=True)):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
            await ctx.respond('Music is not enabled.')
            return
        index-=1
        if index == 0:
            await ctx.respond("If you want to move Index 1, please use skip.")
            return
        if not ctx.guild.voice_client is None:
            playlist=self.data.getGuildData(_getGuildId(ctx)).getPlaylist().playlist
            playlist.move_to_end(list(playlist.keys())[index])
            await ctx.respond("Music was moved!!")
    #loop
    @bridge.bridge_command(name="loop", aliases=["l"], description="Loop queued Music.")
    async def loop(self, ctx, tf:Option(bool, "ON, OFF", required=False, default=None)):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
            await ctx.respond('Music is not enabled.')
            return
        playlist=self.data.getGuildData(_getGuildId(ctx)).getPlaylist()
        if tf is None:
            playlist.loop=not playlist.loop
        else:
            playlist.loop=tf
        await ctx.respond(f'Loop was now {"enabled" if playlist.loop else "disabled"}!!')
    #shuffle
    @bridge.bridge_command(name="shuffle", aliases=["sh"], description="Shuffle playing.")
    async def shuffle(self, ctx, tf:Option(bool, "ON, OFF", required=False, default=None)):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
            await ctx.respond('Music is not enabled.')
            return
        playlist=self.data.getGuildData(_getGuildId(ctx)).getPlaylist()
        if tf is None:
            playlist.shuffle=not playlist.shuffle
        else:
            playlist.shuffle=tf
        await ctx.respond(f'Shuffle was now {"enabled" if playlist.shuffle else "disabled"}!!')
    #disconnect
    @bridge.bridge_command(name="disconnect", aliases=["dc"], description="Disconnect from VC")
    async def dc(self, ctx):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
            await ctx.respond('Music is not enabled.')
            return
        if not ctx.guild.voice_client is None:
            playlist=self.data.getGuildData(_getGuildId(ctx)).getPlaylist()
            playlist.stop()
            await ctx.guild.voice_client.disconnect()
            await ctx.respond('Disconnect from VC')
    #move_to
    @bridge.bridge_command(name="move2", aliases=["mvt"], description="Move to Another VC")
    async def mvt(self, ctx, channel:Option(discord.VoiceChannel, "VC", required=True)):
        playlist = self.data.getGuildData(_getGuildId(ctx)).getPlaylist()
        playlist.move2=True
        await ctx.author.move_to(channel)
        await ctx.guild.voice_client.move_to(channel)
        await ctx.respond("Moved....")

def setup(bot):
    return bot.add_cog(Music(bot))
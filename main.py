from discord import SelectOption, Option, Member, Embed
import logging, argparse, discord, random, string, re, datetime, os, io, traceback
try:
    import pyopenjtalk, numpy
    from scipy.io import wavfile
    enjtalk=True
except:
    enjtalk=False
from data import Data as _Data, playlist_list
from pytube import YouTube, Search, Playlist
from pytube.exceptions import LiveStreamError
from apiclient.discovery import build
from niconico_dl import NicoNicoVideo
from discord.ui import Select, View
from discord.ext import commands

#parse argv
argparser = argparse.ArgumentParser("VC Assistant Bot", description="The Bot that assistant VC.")
argparser.add_argument("-log_level", action="store", type=int, dest="log_level", default=20 ,help="set Log level.(0-50)")
argparser.add_argument("-token", action="store", type=str, dest="token", required=True ,help="discord bot token")
argparser.add_argument("-path", action="store", type=str, dest="path", required=False ,help="data path", default="")
##argparser.add_argument("--daemon", dest="daemon", help="Start in daemon mode.", action="store_true")
argv=argparser.parse_args()
#setting logging
logging.basicConfig(level=argv.log_level)
logger = logging.getLogger("Main")
#intents
intents=discord.Intents.default()
intents.typing=False
intents.members=True
#backend
Data=_Data(data_dir=argv.path)

##utils
#get_guild_id
def _getGuildId(message):

    if not message.guild is None:
        return message.guild.id
    elif message.author is discord.Member:
        return message.author.guild.id
    else:
        return message.author.id
#randomstr
def randomstr(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))
#prefix_setter(May be deprecated in future)
def prefix_setter(bot, message):
    if message.guild is None:
        return "!"
    else:
        return Data.getGuildData(_getGuildId(message)).getProperty("prefix")
#StoTime
def StoTime(s, length=None):
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
def state2emoji(state):
    if state == "play":
        return ":arrow_forward:"
    elif state == "pause":
        return ":pause_button:"
    elif state == "stop":
        return ":stop_button:" 
    else:
        return ":grey_question:"
#Send
async def Send(ctx, content="", view=None, ephemeral=False, embed=None):
    options={}
    if not view is None: options["view"]=view
    if not embed is None: options["embed"]=embed
    if type(ctx) == commands.Context:
        ctx:commands.Context=ctx
        await ctx.send(content=content, **options)
    else:
        await ctx.respond(content=content, ephemeral=ephemeral, **options)

##bot
bot = commands.Bot(command_prefix=prefix_setter, intents=intents)

##event
#on_ready
@bot.event
async def on_ready():
    logger.info("Login")
#on_message(Matcher)
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot: return
    elif bot.user in message.mentions:
        prefix=prefix_setter(bot, message)
        await message.reply(f'Oh, It\'s me..!! My Command prefix is "{prefix}"\n If you want to see all commandlist, please type {prefix}help')
    if Data.getGuildData(_getGuildId(message)).getProperty(property_name="enMatcher"):
        await matcher_callback(message)
    if Data.getGuildData(_getGuildId(message)).getProperty(property_name="enTTS"):
        try:
            await tts_callback(message)
        except Exception as e:
            logger.exception("TTS Error:")
    await bot.process_commands(message)
#on_join(Matcher)
@bot.event
async def on_member_join(member:discord.Member):
    guild=Data.getGuildData(_getGuildId(member))
    if not guild.getProperty(property_name="enMatcher"): return
    plist=guild.getMatcherDict()
    if member.bot:
        if "on_bot_join" in plist:
            txt = plist["on_bot_join"][1].replace("$member",member.mention)
            await member.guild.system_channel.send(txt)
    else:
        if "on_member_join" in plist:
            txt = plist["on_member_join"][1].replace("$member",member.mention)
            await member.guild.system_channel.send(txt)
#on_vc_state_update(Autodisconnect)
@bot.event
async def on_voice_state_update(member, before, after):
    playlist = Data.getGuildData(_getGuildId(member)).getPlaylist()
    try:
        if len(playlist.channel.channel.members) <= 1 and not playlist.move2:
            playlist.save()
            await playlist.channel.disconnect()
        else:
            playlist.move2 = False
    except AttributeError:
        pass
#on_error
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    logger.error(f'Error:\n{"".join(list(traceback.TracebackException.from_exception(error).format()))}')
    await Send(ctx, "Sorry... Error was huppened...")

"""commands"""
## general
@bot.group(name="va")
async def general(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('This command must have subcommands.\n (chprefix, feature)')
# change_prefix
@general.command(name="chprefix", desecription="Changing Prefix")
async def chprefix(ctx, prefix: str):
    Data.getGuildData(_getGuildId(ctx)).setProperty(property_name="prefix",value=prefix)
    await ctx.send("Prefix was successfully changed.")
@bot.slash_command(name="chprefix", description="Changing Prefix")
async def chprefix(ctx, prefix: Option(str, "Prefix string", required=True)):
    Data.getGuildData(_getGuildId(ctx)).setProperty(property_name="prefix",value=prefix)
    await ctx.respond("Prefix was successfully changed.")
#feature
features={"matcher":"Matcher","tts":"TTS","music":"Music"}
@general.group(name="feature", desecription="Setting Feather")
async def featureGrp(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('This command must have subcommands.\n (enable, disable, list, apikey)')
@featureGrp.command(name="enable", desecription="Enable Feather")
async def enable(ctx, feature: str):
    if feature in features:
        Data.getGuildData(_getGuildId(ctx)).setProperty("en"+features[feature],True)
        await ctx.send(features[feature]+" is now enabled!!")
    else:
        await ctx.send(f'Oh no...Can\'t find such as feature..\nSupported features: {",".join(list(features.keys()))}')
@featureGrp.command(name="disable", desecription="Disable Feather")
async def disable(ctx, feature: str):
    if feature in features:
        Data.getGuildData(_getGuildId(ctx)).setProperty("en"+features[feature],False)
        await ctx.send(features[feature]+" is now disabled!!")
    else:
        await ctx.send(f'Oh no...Can\'t find such as feature..\nSupported features: {",".join(list(features.keys()))}')
@featureGrp.command(name="apikey", desecription="Set API key using in Feather")
async def apikey(ctx, kind:str, key:str):
    Data.getGuildData(_getGuildId(ctx)).setProperty("key"+kind,key)
    await ctx.send("Key was seted.")
@bot.slash_command(name="feature", desecription="Setting Feather")
async def feature_com(ctx, subcommand:Option(str, "Subcommand", required=True, choices=["enable","disable","list","apikey"]), value:Option(str, "Feather or Key Type", required=False), key:Option(str, "API-Key", required=False, default=None)):
    if subcommand=="enable":
        if value is None:
            await ctx.respond("This subcommand must have value option(feature name).", ephemeral=True)
        elif value in features:
            Data.getGuildData(_getGuildId(ctx)).setProperty("en"+features[value],True)
            await ctx.respond(features[value]+" is now enabled!!")
        else:
            await ctx.respond(f'Oh no...Can\'t find such as feature..\nSupported features: {",".join(list(features.keys()))}', ephemeral=True)
    elif subcommand=="disable":
        if value is None:
            await ctx.respond("This subcommand must have value option.(feature name)", ephemeral=True)
        elif value in features:
            Data.getGuildData(_getGuildId(ctx)).setProperty("en"+features[value],True)
            await ctx.respond(features[value]+" is now enabled!!")
        else:
            await ctx.respond(f'Oh no...Can\'t find such as feature..\nSupported features: {",".join(list(features.keys()))}', ephemeral=True)
    elif subcommand=="apikey":
        if apikey is None:
            await ctx.respond("Key was seted.", ephemeral=True)
        Data.getGuildData(_getGuildId(ctx)).setProperty("key"+value,key)
        await ctx.respond("Key was seted.", ephemeral=True)

## ping
@bot.command(name="ping", desecription="Ping! Pong!")
async def ping(ctx):
    await ctx.send("Pong!!")
@bot.slash_command(name="ping", description="Ping! Pong!")
async def ping(ctx):
    await ctx.respond("Pong!", ephemeral=True)

## matcher
#callback
async def matcher_callback(message):
    plist=Data.getGuildData(_getGuildId(message)).getMatcherDict()
    for pattern in plist:
        if plist[pattern][0] == "match":
            result=pattern.match(message.content)
        elif plist[pattern][0] == "search":
            result=pattern.search(message.content)
        elif plist[pattern][0] == "fullmatch":
            result=pattern.match(message.content)
        else:
            result=False
        if result:
            await message.channel.send(plist[pattern][1])
#matcher
@general.group("matcher", desecription="Setting Matcher Feature.")
async def matcher(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMatcher"):
        await ctx.send('Matcher is not enabled.')
        return
    if ctx.invoked_subcommand is None:
        await ctx.send('This command must have subcommands.\n (add, del, list)')
@matcher.command("add", desecription="Add word to dict.")
async def add(ctx, pattern:str, check_type:str="search", text:str="Hello World"):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMatcher"):
        await ctx.send('Matcher is not enabled.')
        return
    if not check_type in ["match","search","fullmatch","event"]:
        await ctx.send(f'{check_type} is not supported.')
        return
    try:
        if check_type != "event":
            pattern=re.compile(pattern)
    except re.error:
        await ctx.respond("Oh no...Pattern is wrong...", ephemeral=True)
    else:
        Data.getGuildData(_getGuildId(ctx)).addMatcherDict(pattern, check_type, text)
    await ctx.send("Add word to dict.")
@matcher.command("del", desecription="Del word from dict.")
async def delete(ctx, pattern:str, check_type:str="search"):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMatcher"):
        await ctx.send('Matcher is not enabled.')
        return
    Data.getGuildData(_getGuildId(ctx)).delMatcherDict(pattern, check_type)
    await ctx.send("Del word from dict.")
@matcher.command("list", desecription="Del word from dict.")
async def matcher_list(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMatcher"):
        await ctx.send('Matcher is not enabled.')
        return
    plist=Data.getGuildData(_getGuildId(ctx)).getMatcherDict()
    text="index pattern check_type text\n"
    i=0
    for pattern in plist:
        i+=1
        text+=f'{i} {pattern.pattern if type(pattern) == re.Pattern else pattern} {plist[pattern][0]} {plist[pattern][1]}\n'
    await ctx.send(text)
@bot.slash_command(name="matcher", desecription="Setting Matcher Feature.")
async def matcher(ctx, subcommand:Option(str, "Subcommand", required=True, choices=["add","del","list"]), pattern:Option(str, "Pattern(regax)", required=False), check_type:Option(str, "Check Type",choices=["match","search","fullmatch","event"], required=False, default="search"), text:Option(str, "Text", required=False)):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMatcher"):
        await ctx.respond('Matcher is not enabled.', ephemeral=True)
        return
    if subcommand=="add":
        if pattern is None or check_type is None or text is None:
            await ctx.respond("You must set pattern and text option.", ephemeral=True)
        else:
            try:
                if check_type != "event":
                    pattern=re.compile(pattern)
            except re.error:
                await ctx.respond("Oh no...Pattern is wrong...", ephemeral=True)
            else:
                Data.getGuildData(_getGuildId(ctx)).addMatcherDict(pattern, check_type, text)
                await ctx.respond("Add word to dict.")
    elif subcommand=="del":
        if pattern is None:
            await ctx.respond("You must set pattern option.", ephemeral=True)
        else:
            try:
                Data.getGuildData(_getGuildId(ctx)).delMatcherDict(pattern, check_type)
            except IndexError:
                await ctx.respond("No such pattern found.", ephemeral=True)
            else:
                await ctx.respond("Del word from dict.")
    else:
        plist=Data.getGuildData(_getGuildId(ctx)).getMatcherDict()
        text="index pattern check_type text\n"
        i=0
        for pattern in plist:
            i+=1
            text+=f'{i} {pattern.pattern if type(pattern) == re.Pattern else pattern} {plist[pattern][0]} {plist[pattern][1]}\n'
        await ctx.respond(text)

##Music
#utils
async def connect(channel):
    try:
        if channel.guild.voice_client is None:
            protocol:discord.VoiceProtocol=await channel.connect()
        else:
            await channel.guild.voice_client.move_to(channel)
    except:
        return False
    else:
        playlist=Data.getGuildData(_getGuildId(channel)).getPlaylist()
        playlist.channel=channel.guild.voice_client
        playlist.play_callback=play_callback
        playlists=Data.getGuildData(_getGuildId(channel)).getProperty("playlists")
        if "saved" in playlists:
            if len(playlists["saved"]) !=0:
                return playlists["saved"]
            else:
                return True
        else:
            return True
async def search_music(ctx, query, service):
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
    else:
        key=Data.getGuildData(_getGuildId(ctx)).getProperty("keyYoutube")
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
                if len(yt.title)>80:
                    title=yt.title[0:80]
                else:
                    title=yt.title
                if len(yt.author)>18:
                    channel=yt.author[0:18]
                else:
                    channel=yt.author
                title=f'[{channel}]{title}'
                urllist.append(SelectOption(label=title,value=yt.watch_url, emoji=live))
            return urllist
        else:
            youtube = build('youtube', 'v3', developerKey=key)
            youtube_query = youtube.search().list(q=query, part='id,snippet', maxResults=5, safeSearch="strict")
            youtube_res = youtube_query.execute()
            url=youtube_res.get('items', [])
            for item in url:
                if item['id']['kind'] == 'youtube#video':
                    vid_info=item["snippet"]
                    if len(vid_info["title"])>80:
                        title=vid_info["title"][0:80]
                    else:
                        title=vid_info["title"]
                    if len(vid_info["channelTitle"])>18:
                        channel=vid_info["channelTitle"][0:18]
                    else:
                        channel=vid_info["channelTitle"]
                    title=f'[{channel}]{title}'
                    urllist.append(SelectOption(label=title,value=f'https://www.youtube.com/watch?v={item["id"]["videoId"]}'))
            return urllist
async def get_playlist(ctx, query, service, select=True):
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
def play_music(url, channel, user, service="detect", stream=False):
    if service == "detect":
        service=service_detection(url)
    if service == "youtube":
        try:
            yt = YouTube(url=url)
            #yt.bypass_age_gate()
            yt.check_availability()
            st=yt.streams.get_audio_only()
            if stream:
                path=st
            else:
                path=st.download(output_path=argv.path, filename_prefix=randomstr(5))
        except LiveStreamError:
            path=yt.streaming_data["hlsManifestUrl"]
        except:
            logger.info("Using youtube-dl")
            opts={'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], "outtmpl":randomstr(5)+'%(title)s.%(etx)s', 'nocheckcertificate': True}
            path=opts["outtmpl"].replace("%(title)s.%(etx)s", yt.title+".mp3")#fmm...
            from youtube_dl import YoutubeDL
            with YoutubeDL(opts) as ytdl:
                ytdl.download([url])
        Data.getGuildData(_getGuildId(channel)).getPlaylist().add(yt.length, yt.title, path, user, url)
    elif service == "nico":
        nico=NicoNicoVideo(url=url)
        nico.connect()
        data=nico.get_info()
        Data.getGuildData(_getGuildId(channel)).getPlaylist().add(data["video"]["duration"], data["video"]["title"], nico.get_download_link(), user, url, nico=nico)
    elif service == "file":
        Data.getGuildData(_getGuildId(channel)).getPlaylist().add(int(float(ffmpeg.probe(url)["streams"][0]["duration"])), stream, url, user, url)
    else:
        return -1
    if channel.is_playing():
        return 1
    elif len(Data.getGuildData(_getGuildId(channel)).getPlaylist().playlist)>1:
        return 1
    else:
        Data.getGuildData(_getGuildId(channel)).getPlaylist().play()
        return 0
def play_callback(self, data):
    if type(data["path"]) == str:
        if ".m3u8" in data["path"]:
            self.channel.play(discord.FFmpegPCMAudio(data["path"], options="-vn -hls_allow_cache 1"), after=self.next)
        else:
            self.channel.play(discord.FFmpegPCMAudio(data["path"], options="-vn -af dynaudnorm -hls_allow_cache 1"), after=self.next)
    else:
        path=data["path"].download(output_path=argv.path, filename_prefix=randomstr(5))
        self.playlist[list(self.playlist.keys())[0]]["path"]=path
        self.channel.play(discord.FFmpegPCMAudio(path, options="-vn -af dynaudnorm"), after=self.next)
def service_detection(url):
    if re.match("https?://(\S+\.)?youtube\.com/watch\?v=(\S)+",url):
        return "youtube"
    elif re.match("https?://(\S+\.)?nicovideo\.jp/watch/(\S)+",url):
        return "nico"
    elif re.match("https?://(\S+\.)?youtube\.com/playlist\?list=(\S)+",url):
        return "playlist-youtube"
    elif re.match("nico:(\S)+", url):
        return "search-nico"
    elif re.match("all:(\S)+", url):
        return "playlist-youtube-all"
    elif "file" in url:
        return "file"
    else:
        return "search-youtube"
class MusicSelction(Select):
    def __init__(self, custom_id:str, urllist:list, channel, max_values=1):
        super().__init__(custom_id=custom_id, options=urllist,max_values=max_values)
        self.urllist=urllist
    async def callback(self, interaction):
        if len(self.values) == 1:
            await interaction.message.edit(content=f'Prepareing playing "{self.values[0]}"...', view=None)
        else:
            await interaction.message.edit(content=f'Prepareing playing Musics...', view=None)
        text=""
        for value in self.values:
            status=play_music(value, interaction.guild.voice_client, interaction.user, stream=len(self.values)>1)
            if status == 0:
                text+=f'Start playing "{value}".\n'
            elif status == 1:
                text+=f'Added to queue "{value}".\n'
            else:
                text+=f'Oh...Some Error occured...\n'
        await interaction.message.edit(content=text)
#join
@bot.command(name="join", aliases=["j"], desecription="join to VC")
async def join(ctx, channel:discord.VoiceChannel=None, restore:bool=True):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await Send(ctx, 'Music is not enabled.', ephemeral=True)
        return
    if isinstance(ctx.author, Member):
        if ctx.author.voice is None:
            await Send(ctx, "Please assign or enter to VC.", ephemeral=True)
        else:
            if channel is None:
                state=await connect(ctx.author.voice.channel)
                channel=ctx.author.voice.channel
            else:
                state=await connect(channel)
            if state!=False:
                if type(state) == dict and restore:
                    for music in state:
                        play_music(state[music]["url"], ctx.guild.voice_client, ctx.author)
                    await Send(ctx, "Connected to VC(And restore latest session.)")
                    Data.getGuildData(_getGuildId(ctx)).data["playlists"].pop("saved")
                    Data.getGuildData(_getGuildId(ctx))._syncData()
                else:
                    await Send(ctx, "Connected to VC")
            else:
                await Send(ctx, "Sorry... Can't connect to VC....", ephemeral=True)
    else:
        await Send(ctx, "Now no support for DM...Sorry...", ephemeral=True)
@bot.slash_command(name="join", desecription="join to VC")
async def join_sl(ctx, channel:Option(discord.VoiceChannel, "VC", required=False, default=None), restore:Option(bool, "Restore latest playing.", required=False, default=True)):#7 is Option type channel.
    await join(ctx, channel, restore)
#play
@bot.command(name="play", aliases=["p"], desecription="Play in VC")
async def play(ctx, *query):
    query=" ".join(query)
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    if ctx.guild.voice_client is None:
        if ctx.author.voice is None:
            await ctx.send("Wasn't connected to VC")
            return
        else:
            await connect(ctx.author.voice.channel)
            await ctx.send("Wasn't connected to VC. But you connected VC, So I connect there.")
    service=service_detection(query)
    if service in ["youtube","nico"]:
        msg = await ctx.reply(content=f'Prepareing playing...', mention_author=True)
        status=play_music(query, ctx.guild.voice_client, ctx.author, service)
        if status == 0:
            await msg.edit(content=f'Start playing.')
        elif status == 1:
            await msg.edit(content=f'Added to queue.')
        else:
            await msg.edit(content=f'Oh...Some Error occured...')
    elif service in ["playlist-youtube"]:
        msg=await ctx.send("Processing...")
        urllist=await get_playlist(ctx, query, service)
        if urllist:
            n=int(len(urllist)/25)
            view=View(timeout=None)
            for i in range(n):
                view.add_item(MusicSelction(custom_id="test"+str(i), urllist=urllist[i*25:i*25+25], channel=ctx.guild.voice_client, max_values=25))
            if not len(urllist)%25 == 0:
                view.add_item(MusicSelction(custom_id="test", urllist=urllist[len(urllist)%25*-1:], channel=ctx.guild.voice_client, max_values=len(urllist)%25))
            await msg.edit("Select Music to Play.(Multiple is OK)",view=view)
        else:
            await msg.edit("Error in Searching Music.")
    elif service in ["playlist-youtube-all"]:
        message = await ctx.send("Processing...")
        query=query.replace("all:","")
        urllist=await get_playlist(ctx, query, service, select=False)
        if len(urllist) == 1:
            message.edit(content=f'Prepareing playing "{urllist[0]}"...', view=None)
        else:
            message.edit(content=f'Prepareing playing Musics...', view=None)
        text=""
        for value in urllist:
            status=play_music(value, ctx.guild.voice_client, ctx.author, stream=len(urllist)>1)
            if status == 0:
                text+=f'Start playing "{value}".\n'
            elif status == 1:
                text+=f'Added to queue "{value}".\n'
            else:
                text+=f'Oh...Some Error occured...\n'
            await message.edit(content=text)
    elif service == "file":
        if len(ctx.message.attachments) != 0:
            file=ctx.message.attachments[0]
            msg = await ctx.reply(content=f'Prepareing playing...', mention_author=True)
            status=play_music(file.url, ctx.guild.voice_client, ctx.author, "file", file.filename)
            if status == 0:
                await msg.edit(content=f'Start playing.')
            elif status == 1:
                await msg.edit(content=f'Added to queue.')
            else:
                await msg.edit(content=f'Oh...Some Error occured...')
        else:
            msg = await ctx.reply(content="Wrong Attachment.(only one attachment is required.)", mention_author=True)
    else:
        msg=await ctx.send("Searching...")
        urllist=await search_music(ctx, query, service)
        if urllist:
            view=View(timeout=None)
            view.add_item(MusicSelction(custom_id="test", urllist=urllist, channel=ctx.guild.voice_client))
            await msg.edit("Select Music to Play.",view=view)
        else:
            await msg.edit("Error in Searching Music.")
@bot.slash_command(name="play", desecription="join to VC")
async def play(ctx, query:Option(str, "Search text or url", required=True), service:Option(str, "Service", required=False, choices=["youtube","nico","playlist-youtube","search-youtube","search-nico","playlist-youtube-all"], default="detect")):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.', ephemeral=True)
        return
    if ctx.guild.voice_client is None:
        if ctx.author.voice is None:
            await ctx.respond("Wasn't connected to VC")
            return
        else:
            await connect(ctx.author.voice.channel)
            await ctx.respond("Wasn't connected to VC. But you connected VC, So I connect there.")
    if service == "detect":
        service=service_detection(query)
    if service in ["youtube","nico"]:
        msg = await ctx.respond(content=f'Prepareing playing...', mention_author=True)
        status=play_music(query, ctx.guild.voice_client, ctx.author, service)
        if status == 0:
            await msg.edit(content=f'Start playing.')
        elif status == 1:
            await msg.edit(content=f'Added to queue.')
        else:
            await msg.edit(content=f'Oh...Some Error occured...')
    elif service in ["playlist-youtube"]:
        msg=await ctx.respond("Processing...")
        urllist=await get_playlist(ctx, query, service)
        if urllist:
            view=View(timeout=None)
            n=int(len(urllist)/25)
            for i in range(n):
                view.add_item(MusicSelction(custom_id="test"+str(i), urllist=urllist[i*25:i*25+25], channel=ctx.guild.voice_client, max_values=25))
            if not len(urllist)%25 == 0:
                view.add_item(MusicSelction(custom_id="test", urllist=urllist[len(urllist)%25*-1:], channel=ctx.guild.voice_client, max_values=len(urllist)%25))
            await msg.edit("Select Music to Play.(Multiple is OK)",view=view)
        else:
            await msg.edit("Error in Searching Music.")
    elif service in ["playlist-youtube-all"]:
        msg=await ctx.respond("Processing...")
        query=query.replace("all:","")
        urllist=await get_playlist(ctx, query, service, select=False)
        if len(urllist) == 1:
            await msg.edit(content=f'Prepareing playing "{urllist[0]}"...', view=None)
        else:
            await msg.edit(content=f'Prepareing playing Musics...', view=None)
        text=""
        for value in urllist:
            status=play_music(value, ctx.guild.voice_client, ctx.author, stream=len(urllist)>1)
            if status == 0:
                text+=f'Start playing "{value}".\n'
            elif status == 1:
                text+=f'Added to queue "{value}".\n'
            else:
                text+=f'Oh...Some Error occured...\n'
            await msg.edit(content=text)
    elif service == "file":
        if len(ctx.message.attachments) != 0:
            file=ctx.message.attachments[0]
            msg = await ctx.respond(content=f'Prepareing playing...')
            status=play_music(file.url, ctx.guild.voice_client, ctx.author, "file", file.filename)
            if status == 0:
                await msg.edit(content=f'Start playing.')
            elif status == 1:
                await msg.edit(content=f'Added to queue.')
            else:
                await msg.edit(content=f'Oh...Some Error occured...')
        else:
            await ctx.respond(content="Wrong Attachment.(only one attachment is required.)")
    else:
        msg=await ctx.send("Searching...")
        urllist=await search_music(ctx, query, service)
        if urllist:
            view=View(timeout=None)
            view.add_item(MusicSelction(custom_id="test", urllist=urllist, channel=ctx.guild.voice_client))
            await msg.edit("Select Music to Play.",view=view)
#skip
@bot.command(name="skip", aliases=["s"], desecription="Skip Music")
async def skip(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        await ctx.send(content=f'Skiping Music...')
        Data.getGuildData(_getGuildId(ctx)).getPlaylist().skip()
@bot.slash_command(name="skip", desecription="Skip Music")
async def skip(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        await ctx.respond(content=f'Skiping Music...')
        Data.getGuildData(_getGuildId(ctx)).getPlaylist().skip()
#pause
@bot.command(name="pause", aliases=["pa"], desecription="Pause Music")
async def pause(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        await ctx.send(content=f'Pausing Music...')
        Data.getGuildData(_getGuildId(ctx)).getPlaylist().pause()
@bot.slash_command(name="pause", desecription="Pause Music")
async def pause(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        await ctx.respond(content=f'Pausing Music...')
        Data.getGuildData(_getGuildId(ctx)).getPlaylist().pause()
#resume
@bot.command(name="resume", aliases=["re"], desecription="Resume Music")
async def resume(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        await ctx.send(content=f'Resuming Music...')
        Data.getGuildData(_getGuildId(ctx)).getPlaylist().resume()
@bot.slash_command(name="resume", desecription="Resume Music")
async def resume(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        await ctx.respond(content=f'Resuming Music...')
        Data.getGuildData(_getGuildId(ctx)).getPlaylist().resume()
#stop
@bot.command(name="stop", aliases=["st"], desecription="Stop Music")
async def stop(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        await ctx.send(content=f'Stop playing...')
        Data.getGuildData(_getGuildId(ctx)).getPlaylist().stop()
@bot.slash_command(name="stop", desecription="Stop Music")
async def stop(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        await ctx.respond(content=f'Stop playing...')
        Data.getGuildData(_getGuildId(ctx)).getPlaylist().stop()
#nowplaying
@bot.command(name="nowplaying", aliases=["np"], desecription="Show playing Music.")
async def np(ctx):
    data=Data.getGuildData(_getGuildId(ctx))
    if not data.getProperty("enMusic"):
        await Send('Music is not enabled.', ephemeral=True)
        return
    playlist=data.getPlaylist()
    if len(playlist.playlist)!=0:
        music=list(playlist.playlist.keys())[0]
        embed=Embed(title=playlist.playlist[music]["title"], description=f'{state2emoji(playlist.state)}{StoTime(playlist.stopwatch.getTime(),playlist.playlist[music]["length"])}')
        user=playlist.playlist[music]["user"]
        embed.set_author(name=user, icon_url=user.avatar)
        if playlist.loop:
            embed.add_field(name=":repeat:", value="Loop was Enabled!!")
        await Send(ctx, embed=embed)
    else:
        await Send(ctx, "Now, No Music is playing...")
@bot.slash_command(name="nowplaying", desecription="Show playing Music.")
async def np_sl(ctx):
    await np(ctx)
#showq
@bot.command(name="showq", aliases=["q"], desecription="Show queued Music.")
async def showq(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await Send(ctx,'Music is not enabled.', ephemeral=True)
        return
    pl=Data.getGuildData(_getGuildId(ctx)).getPlaylist()
    if len(pl.playlist)!=0:
        playlist=pl.playlist
        embed=Embed(title="Queue", description=f'Now, {len(playlist)} musics are in queue. Total time is {StoTime(sum([playlist[m]["length"] for m in playlist]))}.{":repeat:" if pl.loop else ""}')
        n=0
        for music in playlist:
            n+=1
            embed.add_field(name=f'{str(n)}"{playlist[music]["title"]}"', value=f'[{StoTime(playlist[music]["length"])}]', inline=False)
        if len(playlist) > 25:
            embed.set_footer(text=f'{len(playlist)-25} musics are after these.')
        await Send(ctx, embed=embed)
    else:
        await Send(ctx, "Now, No Music(s) is in queue...")
@bot.slash_command(name="showq", desecription="Show queued Music.")
async def showq_sl(ctx):
    await showq(ctx)
#del
@bot.command(name="delete", aliases=["del","d"], desecription="Delete queued Music.")
async def delete(ctx, index:int):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    index-=1
    if index == 0:
        await ctx.send("If you want to delete Index 1, please use skip.")
        return
    if not ctx.guild.voice_client is None:
        playlist=Data.getGuildData(_getGuildId(ctx)).getPlaylist().playlist
        playlist.pop(list(playlist.keys())[index])
        await ctx.send("Delete Music")
@bot.slash_command(name="delete", desecription="Delete queued Music.")
async def delete(ctx, index:Option(int, "Music Index", required=True)):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.')
        return
    index-=1
    if index == 0:
        await ctx.respond("If you want to delete Index 1, please use skip.")
        return
    if not ctx.guild.voice_client is None:
        playlist=Data.getGuildData(_getGuildId(ctx)).getPlaylist().playlist
        playlist.pop(list(playlist.keys())[index])
        await ctx.respond("Delete Music")
#movetoend
@bot.command(name="movetoend", aliases=["mv","m"], desecription="Move queued Music to end.")
async def movetoend(ctx, index:int):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    index-=1
    if index == 0:
        await ctx.send("If you want to move Index 1, please use skip.")
        return
    if not ctx.guild.voice_client is None:
        playlist=Data.getGuildData(_getGuildId(ctx)).getPlaylist().playlist
        playlist.move_to_end(list(playlist.keys())[index])
        await ctx.send("Music was moved!!")
@bot.slash_command(name="move", desecription="Move queued Music to end.")
async def movetoend(ctx, index:Option(int, "Music Index", required=True)):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.')
        return
    index-=1
    if index == 0:
        await ctx.respond("If you want to move Index 1, please use skip.")
        return
    if not ctx.guild.voice_client is None:
        playlist=Data.getGuildData(_getGuildId(ctx)).getPlaylist().playlist
        playlist.move_to_end(list(playlist.keys())[index])
        await ctx.respond("Music was moved!!")
#loop
@bot.command(name="loop", aliases=["l"], desecription="Loop queued Music.")
async def loop(ctx, tf:bool=None):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    playlist=Data.getGuildData(_getGuildId(ctx)).getPlaylist()
    if tf is None:
        playlist.loop=not playlist.loop
    else:
        playlist.loop=tf
    await ctx.send(f'Loop was now {"enabled" if playlist.loop else "disabled"}!!')
@bot.slash_command(name="loop", desecription="Loop queued Music.")
async def loop(ctx, tf:Option(bool, "Music Index", required=False, default=None)):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.')
        return
    playlist=Data.getGuildData(_getGuildId(ctx)).getPlaylist()
    if tf is None:
        playlist.loop=not playlist.loop
    else:
        playlist.loop=tf
    await ctx.respond(f'Loop was now {"enabled" if playlist.loop else "disabled"}!!')
#disconnect
@bot.command(name="disconnect", aliases=["dc"], desecription="Disconnect from VC")
async def dc(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await Send(ctx, 'Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        playlist=Data.getGuildData(_getGuildId(ctx)).getPlaylist()
        playlist.stop()
        #playlist.cleanup()
        await ctx.guild.voice_client.disconnect()
        await Send(ctx, content=f'Disconnect from VC')
@bot.slash_command(name="disconnect", desecription="Disconnect from VC")
async def dc_sl(ctx):
    await dc(ctx)
#move_to
@bot.command(name="move2", aliases=["mvt"], desecription="Move to Another VC")
async def mvt(ctx, channel:discord.VoiceChannel):
    playlist = Data.getGuildData(_getGuildId(ctx)).getPlaylist()
    playlist.move2=True
    await ctx.author.move_to(channel)
    await ctx.guild.voice_client.move_to(channel)
    await Send(ctx, "Moved....")
@bot.slash_command(name="move2", desecription="Move to Another VC")
async def mvt_sl(ctx, channel:Option(discord.VoiceChannel, "VC", required=True)):
    await mvt(ctx, channel)
##tts
if enjtalk:
    @bot.group(name="tts", desecription="Text to Speech!!")
    async def tts(ctx):
        if ctx.invoked_subcommand is None:
            if Data.getGuildData(_getGuildId(ctx)).switchTTSChannel(ctx.channel):
                await ctx.send("TTS is now enable on this channel!!")
            else:
                await ctx.send("TTS is now disable on this channel!!")
    @bot.slash_command(name="tts", desecription="Text to Speech!!")
    async def tts(ctx):
        if Data.getGuildData(_getGuildId(ctx)).switchTTSChannel(ctx.channel):
            await ctx.respond("TTS is now enable on this channel!!")
        else:
            await ctx.respond("TTS is now disable on this channel!!")
    async def tts_callback(message):
        data=Data.getGuildData(_getGuildId(message))
        if message.channel.id in data.getTTSChannels():
            playlist=data.getPlaylist()
            vdata, vsr=pyopenjtalk.tts(message.content)
            bio=io.BytesIO()
            wavfile.write(bio, vsr, vdata.astype(numpy.int16))
            dpy_pcm=discord.PCMAudio(bio)
            if playlist.state=="play":
                playlist.pause()
                while True:
                    d=dpy_pcm.read()
                    if d == b'':
                        break
                    else:
                        playlist.channel.send_audio_packet(d, encode=False)
                playlist.resume()
            else:
                while True:
                    d=dpy_pcm.read()
                    if d == b'':
                        break
                    else:
                        playlist.channel.send_audio_packet(d, encode=False)
if not enjtalk: logger.warning("Jtalk is not enabled.")
##Run
if argv.token == "env":
    bot.run(os.environ["BOT_TOKEN"])
else:
    bot.run(argv.token)
for i in playlist_list:
    i.save()

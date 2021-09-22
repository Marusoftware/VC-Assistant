from discord.ext import commands
from discord.member import Member
from discord.ui import Select, View
from data import Data as _Data, playlist_list
import logging, argparse, discord, random, string, re, datetime, os, subprocess, urllib
from discord import SelectOption, Option, SlashCommandOptionType
from pytube import YouTube, Search
from apiclient.discovery import build
from niconico_dl import NicoNicoVideo
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
    elif not message.author.guild is None:
        return message.author.guild
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
        for i in range(int((s/length)*10)):
            text+="="
        text+="○"
        text=text.ljust(10, "=")
        return f'{text} {str(t)}/{str(t2)}'

##bot
bot = commands.Bot(command_prefix=prefix_setter, intents=intents)

##event
#on_connect
@bot.event
async def on_ready():
    logger.info("Login")
#on_message
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot: return
    if Data.getGuildData(_getGuildId(message)).getProperty(property_name="enMatcher"):
        await matcher_callback(message)
    await bot.process_commands(message)

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
@general.group(name="feature", desecription="Setting Feather")
async def feature(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('This command must have subcommands.\n (enable, disable, list, apikey)')
@feature.command(name="enable", desecription="Enable Feather")
async def enable(ctx, feature: str):
    if feature == "matcher":
        Data.getGuildData(_getGuildId(ctx)).setProperty("enMatcher",True)
        await ctx.send("Matcher is now enabled!!")
@feature.command(name="disable", desecription="Disable Feather")
async def disable(ctx, feature: str):
    if feature == "matcher":
        Data.getGuildData(_getGuildId(ctx)).setProperty("enMatcher",False)
        await ctx.send("Matcher is now disabled!!")
@feature.command(name="apikey", desecription="Set API key using in Feather")
async def apikey(ctx, kind:str, key:str):
    Data.getGuildData(_getGuildId(ctx)).setProperty("key"+kind,key)
    await ctx.send("Key was seted.")
@bot.slash_command(name="feature", desecription="Setting Feather")
async def feature(ctx, subcommand:Option(str, "Subcommand", required=True, choices=["enable","disable","list","apikey"]), value:Option(str, "Feather or Key Type", required=False), key:Option(str, "API-Key", required=False, default=None)):
    if subcommand=="enable":
        if value is None:
            await ctx.respond("This subcommand must have value option(feature name).", ephemeral=True)
        elif value == "matcher":
            Data.getGuildData(_getGuildId(ctx)).setProperty("enMatcher",True)
            await ctx.respond("Matcher is now enabled!!")
        elif value == "music":
            Data.getGuildData(_getGuildId(ctx)).setProperty("enMusic",True)
            await ctx.respond("Music is now enabled!!")
        else:
            await ctx.respond("Oh no...Can't find such as feature..", ephemeral=True)
    elif subcommand=="disable":
        if value is None:
            await ctx.respond("This subcommand must have value option.(feature name)", ephemeral=True)
        elif value == "matcher":
            Data.getGuildData(_getGuildId(ctx)).setProperty("enMatcher",False)
            await ctx.respond("Matcher is now disabled!!")
        elif value == "matcher":
            Data.getGuildData(_getGuildId(ctx)).setProperty("enMusic",False)
            await ctx.respond("Music is now disabled!!")
        else:
            await ctx.respond("Oh no...Can't find such as feature..", ephemeral=True)
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
async def add(ctx, pattern:str, check_type:str, text:str):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMatcher"):
        await ctx.send('Matcher is not enabled.')
        return
    if not check_type in ["match","search","fullmatch"]:
        await ctx.send(f'{check_type} is not supported.')
        return
    Data.getGuildData(_getGuildId(ctx)).addMatcherDict(pattern, check_type, text)
    await ctx.send("Add word to dict.")
@matcher.command("del", desecription="Del word from dict.")
async def delete(ctx, pattern:str):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMatcher"):
        await ctx.send('Matcher is not enabled.')
        return
    Data.getGuildData(_getGuildId(ctx)).delMatcherDict(pattern)
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
        text+=f'{i} {pattern} {plist[pattern][0]} {plist[pattern][1]}\n'
    await ctx.send(text)
@bot.slash_command(name="matcher", desecription="Setting Matcher Feature.")
async def matcher(ctx, subcommand:Option(str, "Subcommand", required=True, choices=["add","del","list"]), pattern:Option(str, "Pattern(regax)", required=False), check_type:Option(str, "Check Type",choices=["match","search","fullmatch"], required=False, default="search"), text:Option(str, "Text", required=False)):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMatcher"):
        await ctx.respond('Matcher is not enabled.', ephemeral=True)
        return
    if subcommand=="add":
        if pattern is None or check_type is None or text is None:
            await ctx.respond("You must set pattern, check_type and text option.", ephemeral=True)
        else:
            try:
                pattern=re.compile(pattern)
            except re.error:
                await ctx.respond("Oh no...Can't find such as feature..", ephemeral=True)
            else:
                Data.getGuildData(_getGuildId(ctx)).addMatcherDict(pattern, check_type, text)
                await ctx.respond("Add word to dict.")
    elif subcommand=="del":
        if pattern is None:
            await ctx.respond("You must set pattern option.", ephemeral=True)
        else:
            try:
                Data.getGuildData(_getGuildId(ctx)).addMatcherDict(pattern)
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
            text+=f'{i} {pattern} {plist[pattern][0]} {plist[pattern][1]}\n'
        await ctx.respond(text)

##Youtube
#utils
async def connect(channel):
    try:
        protocol:discord.VoiceProtocol=await channel.connect()
    except:
        return False
    else:
        playlist=Data.getGuildData(_getGuildId(channel)).getPlaylist()
        playlist.channel=channel.guild.voice_client
        playlist.play_callback=play_callback
        playlist.pause_callback=pause_callback
        playlist.stop_callback=stop_callback
        playlist.resume_callback=resume_callback
        return True
async def search_music(ctx, query, service):
    urllist=[]
    if service == "search-nico":
        query=query.replace("nico://","")
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
            for i in range(5):
                yt=yts[i]
                title=yt.title
                if len(title)>90:
                    title=title[0:90]
                urllist.append(SelectOption(label=title,value=yt.watch_url))
            return urllist
        else:
            youtube = build('youtube', 'v3', developerKey=key)
            youtube_query = youtube.search().list(q=query, part='id,snippet', maxResults=5)
            youtube_res = youtube_query.execute()
            url=youtube_res.get('items', [])
            for item in url:
                if item['id']['kind'] == 'youtube#video':
                    title=item["snippet"]["title"]
                    if len(title)>90:
                        title=title[0:90]
                    urllist.append(SelectOption(label=title,value=f'https://www.youtube.com/watch?v={item["id"]["videoId"]}'))
            return urllist
def pause_callback(self):
    self.channel.pause()
def stop_callback(self, data):
    if not data["nico"] is None:
        data["nico"].close()
    self.channel.stop()
def resume_callback(self):
    self.channel.resume()
def play_callback(self, data):
    self.channel.play(discord.FFmpegPCMAudio(data["path"], options="-vn"))
def play_music(url, channel, service="detect"):
    if service == "detect":
        service=service_detection(url)
    if service == "youtube":
        yt = YouTube(url=url)
        #stream=yt.streams.filter(only_audio=True)[0]
        stream=yt.streams.get_audio_only()
        path=stream.download(output_path=argv.path)
        Data.getGuildData(_getGuildId(channel)).getPlaylist().add(yt.length, stream.title, path)
    elif service == "nico":
        nico=NicoNicoVideo(url=url)
        nico.connect()
        data=nico.get_info()
        Data.getGuildData(_getGuildId(channel)).getPlaylist().add(data["video"]["duration"], data["video"]["title"], nico.get_download_link(), nico=nico)
    else:
        return -1
    if channel.is_playing():
        return 1
    else:
        Data.getGuildData(_getGuildId(channel)).getPlaylist().play()
        return 0
def service_detection(url):
    if re.match("https?://(\S+\.)?youtube\.com/watch\?v=(\S)+",url):
        return "youtube"
    elif re.match("https?://(\S+\.)?nicovideo\.jp/watch/(\S)+",url):
        return "nico"
    elif re.match("https?://(\S+\.)?youtube\.com/watch\?v=(\S)+",url):
        return "playlist-youtube"
    elif re.match("nico://(\S)+", url):
        return "search-nico"
    else:
        return "search-youtube"
class MusicSelction(Select):
    def __init__(self, custom_id:str, urllist:list, channel):
        super().__init__(custom_id=custom_id, options=urllist)
        self.urllist=urllist
    async def callback(self, interaction):
        await interaction.message.edit(content=f'Prepareing playing "{self.values[0]}"...', view=None)
        status=play_music(self.values[0], interaction.guild.voice_client)
        if status == 0:
            await interaction.message.edit(content=f'Start playing "{self.values[0]}".')
        elif status == 1:
            await interaction.message.edit(content=f'Added to queue "{self.values[0]}".')
        else:
            await interaction.message.edit(content=f'Oh...Some Error occured...')
#join
@bot.command(name="join", aliases=["j"], desecription="join to VC")
async def join(ctx, channel=None):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    if channel is None:
        if type(ctx.author) == Member:
            if ctx.author.voice is None:
                await ctx.send("Please assign or enter to VC.")
            else:
                if not await connect(ctx.author.voice.channel):
                    await ctx.send("Sorry... Can't connect to VC....")
                else:
                    await ctx.send("Connected to VC")
        else:
            await ctx.send("Now no support for DM...Sorry...")
    else:
        if not await connect(channel):
            await ctx.send("Sorry... Can't connect to VC....")
        else:
            await ctx.send("Connected to VC")
@bot.slash_command(name="join", desecription="join to VC")
async def join(ctx, channel:Option(SlashCommandOptionType.channel, "VC", required=False, default=None)):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.', ephemeral=True)
        return
    if channel is None:
        if type(ctx.author) == Member:
            if ctx.author.voice is None:
                await ctx.respond("Please assign or enter to VC.")
            else:
                if not await connect(ctx.author.voice.channel):
                    await ctx.respond("Sorry... Can't connect to VC....")
                else:
                    await ctx.respond("Connected to VC")
        else:
            await ctx.respond("Now no support for DM...Sorry...")
    else:
        if not await connect(channel):
            await ctx.respond("Sorry... Can't connect to VC....")
        else:
            await ctx.respond("Connected to VC")
#play
@bot.command(name="play", aliases=["p"], desecription="Play in VC")
async def play(ctx, *query):
    query=" ".join(query)
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    service=service_detection(query)
    if service in ["youtube","nico"]:
        msg = await ctx.send(content=f'Prepareing playing...', mention_author=True)
        status=play_music(query, ctx.guild.voice_client, service)
        if status == 0:
            await msg.edit(content=f'Start playing.')
        elif status == 1:
            await msg.edit(content=f'Added to queue.')
        else:
            await msg.edit(content=f'Oh...Some Error occured...')
    else:
        urllist=await search_music(ctx, query, service)
        if urllist:
            view=View(timeout=None)
            view.add_item(MusicSelction(custom_id="test", urllist=urllist, channel=ctx.guild.voice_client))
            await ctx.send("Select Music to Play.",view=view)
        else:
            await ctx.send("Error in Searching Music.")
@bot.slash_command(name="play", desecription="join to VC")
async def play(ctx, query:Option(str, "Serch text or url", required=True)):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.', ephemeral=True)
        return
    service=service_detection(query)
    if service in ["youtube","nico"]:
        msg = await ctx.respond(content=f'Prepareing playing...', mention_author=True)
        status=play_music(query, ctx.guild.voice_client, service)
        if status == 0:
            await msg.edit(content=f'Start playing.')
        elif status == 1:
            await msg.edit(content=f'Added to queue.')
        else:
            await msg.edit(content=f'Oh...Some Error occured...')
    else:
        urllist=await search_music(ctx, query, service)
        if urllist:
            view=View(timeout=None)
            view.add_item(MusicSelction(custom_id="test", urllist=urllist, channel=ctx.guild.voice_client))
            await ctx.respond("Select Music to Play.",view=view)
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
#pause
@bot.command(name="resume", aliases=["re"], desecription="Resume Music")
async def pause(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        await ctx.send(content=f'Resuming Music...')
        Data.getGuildData(_getGuildId(ctx)).getPlaylist().resume()
@bot.slash_command(name="resume", desecription="Resume Music")
async def pause(ctx):
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
async def nowplaying(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        playlist=Data.getGuildData(_getGuildId(ctx)).getPlaylist()
        music=list(playlist.playlist.keys())[0]
        await ctx.send(content=f'State:{playlist.state}\nTitle:{playlist.playlist[music]["title"]}\nPos:{StoTime(playlist.stopwatch.getTime(),playlist.playlist[music]["length"])}')
        
@bot.slash_command(name="nowplaying", desecription="Show playing Music.")
async def nowplaying(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        playlist=Data.getGuildData(_getGuildId(ctx)).getPlaylist()
        music=list(playlist.playlist.keys())[0]
        await ctx.respond(content=f'State:{playlist.state}\nTitle:{playlist.playlist[music]["title"]}\nPos:{StoTime(playlist.stopwatch.getTime(),playlist.playlist[music]["length"])}')
#showq
@bot.command(name="showq", aliases=["q"], desecription="Show queued Music.")
async def showq(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        text=f'Index Title Length\n'
        playlist=Data.getGuildData(_getGuildId(ctx)).getPlaylist().playlist
        n=0
        for music in playlist:
            n+=1
            text+=f'{str(n)} "{playlist[music]["title"]}" {StoTime(playlist[music]["length"])}s\n'
        await ctx.send(text)
@bot.slash_command(name="showq", desecription="Show queued Music.")
async def showq(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        text=f'Index Title Length\n'
        playlist=Data.getGuildData(_getGuildId(ctx)).getPlaylist().playlist
        n=0
        for music in playlist:
            n+=1
            text+=f'{str(n)} "{playlist[music]["title"]}" {StoTime(playlist[music]["length"])}s\n'
        await ctx.respond(text)
#del
@bot.command(name="delete", aliases=["del","d"], desecription="Delete queued Music.")
async def showq(ctx, index:int):
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
async def showq(ctx, index:Option(int, "Music Index", required=True)):
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
#disconnect
@bot.command(name="disconnect", aliases=["dc"], desecription="Disconnect from VC")
async def disconnect(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.send('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        if ctx.guild.voice_client.is_playing():
            ctx.guild.voice_client.stop()
        await ctx.send(content=f'Disconnect from VC')
        await ctx.guild.voice_client.disconnect()
@bot.slash_command(name="disconnect", desecription="Disconnect from VC")
async def disconnect(ctx):
    if not Data.getGuildData(_getGuildId(ctx)).getProperty("enMusic"):
        await ctx.respond('Music is not enabled.')
        return
    if not ctx.guild.voice_client is None:
        if ctx.guild.voice_client.is_playing():
            ctx.guild.voice_client.stop()
        await ctx.respond(content=f'Disconnect from VC')
        await ctx.guild.voice_client.disconnect()

##Run
bot.run(argv.token)
for i in playlist_list:
    i.cleanup()
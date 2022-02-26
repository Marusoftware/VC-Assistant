from discord import SelectOption, Option, Message, Intents, SlashCommandGroup
import logging, argparse, discord, os, traceback, typing
from data import Data as _Data
from discord.ui import Select, View
from discord.ext import commands
from lib import _getGuildId, Send

#parse argv
argparser = argparse.ArgumentParser("VC Assistant Bot", description="The Bot that assistant VC.")
argparser.add_argument("-log_level", action="store", type=int, dest="log_level", default=20 ,help="set Log level.(0-50)")
argparser.add_argument("token", action="store", type=str, help="discord bot token")
argparser.add_argument("-path", action="store", type=str, dest="path", required=False ,help="data path", default="")
argparser.add_argument("-spot", action="store", type=str, dest="spot", required=False ,help="Spotify Client ID", default="")
argparser.add_argument("-spot_secret", action="store", type=str, dest="spotse", required=False ,help="Spotify Client Secret", default="")
##argparser.add_argument("--daemon", dest="daemon", help="Start in daemon mode.", action="store_true")
argv=argparser.parse_args()
#setting logging
logging.basicConfig(level=argv.log_level)
logger = logging.getLogger("Main")
#intents
intents=Intents.default()
intents.typing=False
intents.members=True
#intents.message_content=True
##bot init
#prefix_setter
def prefix_setter(bot, message):
    if message.guild is None:
        return "!"
    else:
        return bot.data.getGuildData(_getGuildId(message)).getProperty("prefix")
bot = commands.Bot(command_prefix=prefix_setter, intents=intents)
bot.auto_sync_commands=True
#database
bot.data=_Data(data_dir=argv.path)
bot.argv=argv
import lib
lib.Data=bot.data
#add global check
def check_permission(ctx):
    perms=bot.data.getGuildData(_getGuildId(ctx)).data["perms"]
    if not ctx.command.name in bot.data.command_perms: return True
    if not hasattr(ctx.author, "guild_permissions"): return True
    if ctx.author.guild_permissions.administrator: return True
    if "user-"+str(ctx.author.id) in perms:
        if bot.data.command_perms[ctx.command.name] in perms["user-"+str(ctx.author.id)]: return True
    for role in ctx.author.roles:
        if "role-"+str(role.id) in perms:
            if bot.data.command_perms[ctx.command.name] in perms["role-"+str(role.id)]: return True
    return False
bot.add_check(check_permission)
#load modules
for ext in ["matcher", "music", "activity", "tts"]:
    bot.load_extension(f'modules.{ext}')

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot=bot
        self.data=bot.data
    ##event
    #on_ready
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Login")
        bot.sync_commands()
    #on_message
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if self.bot.user in message.mentions:
            prefix=prefix_setter(bot, message)
            await message.reply(f'Oh, It\'s me..!! My Command prefix is "{prefix}"\n If you want to see all commandlist, please type {prefix}help')
        else:
            await self.bot.process_commands(message)
    #on_error
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound): return
        logger.error(f'Error:\n{"".join(list(traceback.TracebackException.from_exception(error).format()))}')
        await Send(ctx, "Sorry... Error was huppened...")

    ##commands
    #ping
    @commands.command(name="ping", desecription="Ping! Pong!")
    async def ping(self, ctx):
        await Send(ctx, "Pong!!", ephemeral=True)
    @commands.slash_command(name="ping", description="Ping! Pong!")
    async def ping_sl(self, ctx):
        await self.ping(ctx)
    #va
    @commands.group(name="va", description="Core command of VC-Assistant")#text command group
    async def va(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('This command must have subcommands.\n (chprefix, feature)')
    #chprefix
    @va.command(name="chprefix", desecription="Changing Prefix")
    async def chprefix(self, ctx, prefix: str):
        self.data.getGuildData(_getGuildId(ctx)).setProperty(property_name="prefix",value=prefix)
        await Send(ctx, "Prefix was successfully changed.")
    @commands.slash_command(name="chprefix", description="Changing Prefix")
    async def chprefix_sl(self, ctx, prefix: Option(str, "Prefix string", required=True)):
        await self.chprefix(ctx, prefix)
    #feature
    features={"matcher":"Matcher","tts":"TTS","music":"Music"}
    @va.group(name="feature", desecription="Setting Feather")#text command group
    async def feature(self, ctx):
        if ctx.invoked_subcommand is None:
            await Send(ctx, 'This command must have subcommands.\n (enable, disable, list, apikey)')
    feature_sl=SlashCommandGroup("feature", "Setting Feather")#slash command group
    #feature - enable
    @feature.command(name="enable", desecription="Enable Feather")
    async def enable(self, ctx, feature: str):
        if feature in self.features:
            self.data.getGuildData(_getGuildId(ctx)).setProperty("en"+self.features[feature],True)
            await Send(ctx, self.features[feature]+" is now enabled!!")
        else:
            await Send(ctx, f'Oh no...Can\'t find such as feature..\nSupported features: {",".join(list(self.features.keys()))}')
    @feature_sl.command(name="enable", desecription="Enable Feather")
    async def enable_sl(self, ctx, feature:Option(str, "Feature name", choices=list(features.keys()), required=True)):
        await self.enable(ctx, feature)
    #feature - disable
    @feature.command(name="disable", desecription="Disable Feather")
    async def disable(self, ctx, feature: str):
        if feature in self.features:
            self.data.getGuildData(_getGuildId(ctx)).setProperty("en"+self.features[feature],False)
            await Send(ctx, self.features[feature]+" is now disabled!!")
        else:
            await Send(ctx, f'Oh no...Can\'t find such as feature..\nSupported features: {",".join(list(self.features.keys()))}')
    @feature_sl.command(name="disable", desecription="Disable Feather")
    async def disable_sl(self, ctx, feature:Option(str, "Feature name", choices=list(features.keys()), required=True)):
        await self.disable(ctx, feature)
    #feature - apikey
    @feature.command(name="apikey", desecription="Set API key using in Feather")
    async def apikey(self, ctx, kind:str, key:str):
        self.data.getGuildData(_getGuildId(ctx)).setProperty("key"+kind,key)
        await Send(ctx, "Key was seted.")
    @feature_sl.command(name="apikey", desecription="Set API key using in Feather")
    async def apikey_sl(self, ctx, kind:Option(str, "Keyname", required=True), key:Option(str, "Key", required=True)):
        await self.apikey(ctx, kind, key)
    #feature - config
    @feature.command(name="config", desecription="Set API key using in Feather")
    async def config(self, ctx, key:str, value:str=None):
        if value is None:
            await Send(ctx, f"{key}: {self.data.getGuildData(_getGuildId(ctx)).getProperty(key)}")
        else:
            self.data.getGuildData(_getGuildId(ctx)).setProperty(key, value)
            await Send(ctx, "Config was seted.")
    @feature_sl.command(name="config", desecription="Disable Feather")
    async def config_sl(self, ctx, key:Option(str, "key", required=True), value:Option(str, "value", required=False, default=None)):
        await self.config(ctx, key, value)
    #Perm
    @va.command(name="permission", description="Set Permission to User", aliases=["perm"])
    async def perm(self, ctx, user:typing.Optional[discord.Member]=None, role:typing.Optional[discord.Role]=None):
        view=View(timeout=0)
        if not user is None:
            permlist=[]
            try:
                guild_data=self.data.getGuildData(_getGuildId(ctx)).data["perms"]["user-"+str(user.id)]
            except KeyError:
                guild_data={}
            for perm in self.data.perms:
                permlist.append(SelectOption(label=perm, value=perm, description=self.data.perms[perm]["desc"], default=((perm in guild_data) if perm in guild_data else self.data.perms[perm]["def"])))
            view.add_item(PermSelction(self.data, "perm", user, permlist, ctx.author, "user"))
            await Send(ctx, f"Select Permission to grant {user.mention}.", view=view, ephemeral=True)
        if not role is None:
            permlist=[]
            try:
                guild_data=self.data.getGuildData(_getGuildId(ctx)).data["perms"]["role-"+str(role.id)]
            except KeyError:
                guild_data={}
            for perm in self.data.perms:
                permlist.append(SelectOption(label=perm, value=perm, description=self.data.perms[perm]["desc"], default=((perm in guild_data) if perm in guild_data else self.data.perms[perm]["def"])))
            view.add_item(PermSelction(self.data, "perm", role, permlist, ctx.author, "role"))
            await Send(ctx, f"Select Permission to grant {role.mention}.", view=view, ephemeral=True)
    @commands.slash_command(name="permission", description="Set Permission to User")
    async def perm_sl(self, ctx, user:Option(discord.Member, description="An User who would be grant permission", required=False, default=None), role:Option(discord.Role, description="An Role who would be grant permission", required=False, default=None)):
        await self.perm(ctx, user, role)
    @commands.user_command(name="permission", description="Set Permission to User")
    async def perm_usr(self, ctx, user):
        await self.perm(ctx, user)

class PermSelction(Select):
    def __init__(self, data, custom_id:str, user, permlist:list, author, user_type:typing.Literal["user","role"]):
        self.permlist=permlist
        self.target_user=user
        self.author_user=author
        self.target_user_type=user_type
        self.data=data
        super().__init__(custom_id=custom_id, options=self.permlist, max_values=len(self.permlist), placeholder="Select Permission.")
    async def callback(self, interaction):
        if self.author_user.id != interaction.user.id:
            return
        guild_data=self.data.getGuildData(_getGuildId(interaction))
        guild_data.data["perms"][f'{self.target_user_type}-{self.target_user.id}']=self.values
        guild_data._syncData()
        await interaction.response.send_message(content=f'Granted.', ephemeral=True)

bot.add_cog(Core(bot))

##Run
if argv.token == "env":
    bot.run(os.environ["BOT_TOKEN"])
else:
    bot.run(argv.token)
for i in bot.data.playlists:
    i.stop(save=True)
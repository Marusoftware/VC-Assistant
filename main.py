from discord.ext import commands
from discord.ui import Button, Select, View
from data import Data as _Data
import logging, argparse, discord, random, string, os, re
from discord import ButtonStyle, SelectOption, Option

def randomstr(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))
#parse argv
argparser = argparse.ArgumentParser("VoteBot", description="VotingBot")
argparser.add_argument("-log_level", action="store", type=int, dest="log_level", default=20 ,help="set Log level.(0-50)")
argparser.add_argument("-token", action="store", type=str, dest="token", required=True ,help="discord bot token")
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
Data=_Data()
#prefix_setter(May be deprecated in future)
def prefix_setter(bot, msg):
    if msg.guild is None:
        return "!"
    else:
        dt=Data.getGuildData(msg.guild.id)
        return dt.getProperty("prefix")
#bot
bot = commands.Bot(command_prefix=prefix_setter, intents=intents)
#event_on_connect
@bot.event
async def on_ready():
    logger.info("Login")
@bot.event
async def on_slash_command_error(ctx,ex):
    print("error"+str(ex))

"""commands"""
## general
@bot.group(name="va")
async def general(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('This command must have subcommands.\n (chprefix)')
# change_prefix
@general.command(name="chprefix", desecription="Changing Prefix")
async def chprefix(ctx, prefix: str):
    Data.getGuildData(ctx.guild.id).setProperty("prefix",prefix)
    await ctx.send("Prefix was successfully changed.")
@bot.slash_command(name="chprefix", description="Changing Prefix")
async def chprefix(ctx, prefix: Option(str, "Prefix string", required=True)):
    Data.getGuildData(ctx.guild.id).setProperty("prefix",prefix)
    await ctx.respond("Prefix was successfully changed.")

@general.group(name="feature")
async def feature(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send('This command must have subcommands.\n (chprefix)')

## ping
@bot.command(name="ping", desecription="Ping! Pong!")
async def ping(ctx):
    await ctx.send("Pong!!")
@bot.slash_command(name="ping", description="Ping! Pong!")
async def ping(ctx):
    await ctx.respond("Pong!", ephemeral=True)
## matcher
async def matcher(message):
    plist=Data.getGuildData(message.guild.id).getMatcherDict()
    for pattern in plist:
        if plist[pattern][0] == "match":
            result=re.match(pattern, message.content)
        elif plist[pattern][0] == "search":
            result=re.search(pattern, message.content)
        elif plist[pattern][0] == "fullmatch":
            result=re.match(pattern, message.content)
        else:
            result=False
        if result:
            await message.channel.send(plist[pattern][1])

@bot.event
async def on_message(message):
    print(dir(message.author.guild))
    if Data.getGuildData(message.author.guild.id).getProperty("enMatcher"):
        await matcher(message)
    await bot.process_commands(message)

#run
bot.run(argv.token)

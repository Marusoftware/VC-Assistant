from discord.ext import commands
from discord.mentions import A
from discord.ui import Button, Select, View
from user import User
import logging, argparse, discord, random, string
from discord import ButtonStyle, SelectOption
def randomstr(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

#parse argv
argparser = argparse.ArgumentParser("VoteBot", description="VotingBot")
argparser.add_argument("-log_level", action="store", type=int, dest="log_level", default=20 ,help="set Log level.(0-50)")
##argparser.add_argument("--daemon", dest="daemon", help="Start in daemon mode.", action="store_true")
argv=argparser.parse_args()
#setting logging
logging.basicConfig(level=argv.log_level)
logger = logging.getLogger("Main")
#intents
intents=discord.Intents.default()
intents.typing=False
intents.members=True
#bot
bot = commands.Bot(command_prefix="!", intents=intents)
#backend
user=User()

#event_on_connect
@bot.event
async def on_ready():
    logger.info("Login")
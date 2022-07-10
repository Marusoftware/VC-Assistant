from discord.ext import commands
import discord, random, string, datetime

Data=None

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

#Send
async def Send(ctx, content="", view=None, ephemeral=False, embed=None, mention_author=False):
    options={}
    if not view is None: options["view"]=view
    if not embed is None: options["embed"]=embed
    del_after=Data.getGuildData(_getGuildId(ctx)).getProperty("AutoRemove")
    if del_after:
        options["delete_after"]=int(del_after)
    if hasattr(ctx, "respond"):
        msg=await ctx.respond(content=content, ephemeral=ephemeral, **options)
    else:
        msg=await ctx.send(content=content, mention_author=mention_author, **options)
    if not hasattr(msg, "edit"):
        msg=await msg.original_message()
    return msg
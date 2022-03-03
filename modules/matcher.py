from discord.ext import commands
from discord import Option, SlashCommandGroup
from lib import _getGuildId, Send
import re

class Matcher(commands.Cog, name="matcher", description="Send message when find bingo message."):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data=bot.data
    #matcher
    matcher_sl=SlashCommandGroup("matcher", "Send message when find bingo message.")#slash command group
    @commands.group("matcher", description="Setting Matcher Feature.")#text command group
    async def matcher(self, ctx):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMatcher"):
            await Send(ctx, 'Matcher is not enabled.')
            return
        if ctx.invoked_subcommand is None:
            await Send(ctx, 'This command must have subcommands.\n (add, del, list)')
    ##callback
    #on_message
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        gdata=self.data.getGuildData(_getGuildId(message))
        if gdata.getProperty(property_name="enMatcher"):
            plist=gdata.getMatcherDict()
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
        #await self.bot.process_commands(message)
    #on_join
    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild=self.data.getGuildData(_getGuildId(member))
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
    #add sub command
    @matcher.command(name="add", description="Add word to dict.")
    async def add(self, ctx, pattern:str, check_type:str="search", text:str="Hello World"):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMatcher"):
            await Send(ctx, 'Matcher is not enabled.')
            return
        if not check_type in ["match","search","fullmatch","event"]:
            await Send(ctx, f'{check_type} is not supported.')
            return
        try:
            if check_type != "event":
                pattern=re.compile(pattern)
        except re.error:
            await ctx.respond("Oh no...Pattern is wrong...", ephemeral=True)
        else:
            self.data.getGuildData(_getGuildId(ctx)).addMatcherDict(pattern, check_type, text)
        await Send(ctx, "Add word to dict.")
    @matcher_sl.command(name="add", description="Add word to dict.")
    async def add_sl(self, ctx, pattern:Option(str, "Pattern(regax)", required=True), text:Option(str, "Text", required=True), check_type:Option(str, "Check Type", choices=["match","search","fullmatch","event"], default="search")):
        await self.add(ctx, pattern, check_type, text)
    #del sub command
    @matcher.command(name="del", description="Del word from dict.")
    async def delete(self, ctx, pattern:str, is_event:bool=False):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMatcher"):
            await Send(ctx, 'Matcher is not enabled.')
            return
        self.data.getGuildData(_getGuildId(ctx)).delMatcherDict(pattern, is_event)
        await Send(ctx, "Del word from dict.")
    @matcher_sl.command(name="del", description="Del word from dict.")
    async def del_sl(self, ctx, pattern:Option(str, "Pattern(regax)", required=True), is_event:Option(bool, "Is it Event?", default=False, required=False)):
        await self.delete(ctx, pattern, is_event)
    #list sub command
    @matcher.command(name="list", description="List word in dict.")
    async def matcher_list(self, ctx):
        if not self.data.getGuildData(_getGuildId(ctx)).getProperty("enMatcher"):
            await Send(ctx, 'Matcher is not enabled.')
            return
        plist=self.data.getGuildData(_getGuildId(ctx)).getMatcherDict()
        text="index pattern check_type text\n"
        i=0
        for pattern in plist:
            i+=1
            text+=f'{i} {pattern.pattern if type(pattern) == re.Pattern else pattern} {plist[pattern][0]} {plist[pattern][1]}\n'
        await Send(ctx, text)
    @matcher_sl.command(name="list", description="List word in dict.")
    async def list_sl(self, ctx):
        await self.matcher_list(ctx)

def setup(bot):
    return bot.add_cog(Matcher(bot))
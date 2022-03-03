from discord.ext import commands
from discord import Option, EmbeddedActivity, VoiceChannel
from lib import Send

class Activity(commands.Cog, name="activity", description="VC Activity"):
    def __init__(self, bot):
        self.bot=bot
    #activity
    @commands.command(name="activity", aliases=["act"], description="VC Activity")
    async def act(self, ctx, activity:str, vc:VoiceChannel=None):
        if activity == "youtube_together":
            activity=880218394199220334
        else:
            activity=getattr(EmbeddedActivity, activity, None)
        if activity is None:
            await Send(ctx, "No such activity was found.")
        else:
            if vc is None:
                if ctx.guild.voice_client is None:
                    await Send(ctx, "Channel is Not assigned and this bot is not join to any channel.", ephemeral=True)
                    return
                invite=await ctx.guild.voice_client.channel.create_activity_invite(activity, temporary=True)
            else:
                invite=await vc.create_activity_invite(activity, temporary=True)
            await Send(ctx, f'Click here to join VC Activity. \n {invite.url}')
    @commands.slash_command(name="activity", description="VC Activity")
    async def act_sl(self, ctx, activity:Option(str, "Activity Type", required=True, choices=["youtube_together"]), voice_channel:Option(VoiceChannel, "Where start activity.", required=False, default=None)):
        await self.act(ctx, activity, voice_channel)

def setup(bot):
    return bot.add_cog(Activity(bot))
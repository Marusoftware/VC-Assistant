from discord.ext import commands
from discord import Option, EmbeddedActivity
from lib import Send

class Activity(commands.Cog, name="activity", description="VC Activity"):
    def __init__(self, bot):
        self.bot=bot
    #activity
    @commands.command(name="activity", aliases=["act"], desecription="VC Activity")
    async def act(self, ctx, activity:str):
        activity=getattr(EmbeddedActivity, activity, None)
        if activity is None:
            await Send(ctx, "No such activity was found.")
        else:
            invite=await ctx.guild.voice_client.channel.create_activity_invite(activity, temporary=True)
            await Send(ctx, f'Click here to join VC Activity. \n {invite.url}')
    @commands.slash_command(name="activity", desecription="VC Activity")
    async def act_sl(self, ctx, activity:Option(str, "Activity Type", required=True, choices=["youtube_together"])):
        await self.act(ctx, activity)

def setup(bot):
    return bot.add_cog(Activity(bot))
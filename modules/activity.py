from discord.ext import commands, bridge
from discord import Option, EmbeddedActivity, VoiceChannel
from lib import Send

class Activity(commands.Cog, name="activity", description="VC Activity"):
    def __init__(self, bot):
        self.bot=bot
    #activity
    @bridge.bridge_command(name="activity", aliases=["act"], description="VC Activity")
    async def act(self, ctx, activity:Option(str, "Activity Type", required=True, choices=["youtube_together"]), vc:Option(VoiceChannel, "Where start activity.", required=False, default=None)):
        if activity == "youtube_together":
            activity=880218394199220334
        else:
            activity=getattr(EmbeddedActivity, activity, None)
        if activity is None:
            await ctx.respond("No such activity was found.")
        else:
            if vc is None:
                if ctx.guild.voice_client is None:
                    await Send(ctx, "Channel is Not assigned and this bot is not join to any channel.", ephemeral=True)
                    return
                invite=await ctx.guild.voice_client.channel.create_activity_invite(activity, temporary=True)
            else:
                invite=await vc.create_activity_invite(activity, temporary=True)
            await ctx.respond(f'Click here to join VC Activity. \n {invite.url}')

def setup(bot):
    return bot.add_cog(Activity(bot))
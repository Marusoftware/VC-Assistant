#activity
@bot.command(name="activity", aliases=["act"], desecription="VC Activity")
async def act(ctx, activity:str):
    activity=getattr(EmbeddedActivity, activity, None)
    if activity is None:
        await Send(ctx, "No such activity was found.")
    else:
        invite=await ctx.guild.voice_client.channel.create_activity_invite(activity, temporary=True)
        await Send(ctx, f'Click here to join VC Activity. \n {invite.url}')
@bot.slash_command(name="activity", desecription="VC Activity")
async def act_sl(ctx, activity:Option(str, "Activity Type", required=True, choices=["awkword",
"betrayal","checkers_in_the_park","chess_in_the_park","doodle_crew","fishington","letter_tile","ocho",
"poker_night","putts","sketchy_artist","spell_cast","watch_together","word_snacks","youtube_together"])):
    await act(ctx, activity)
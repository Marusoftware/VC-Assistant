from discord.ext import commands
try:
    import pyopenjtalk, numpy
    from scipy.io import wavfile
    enjtalk=True
except:
    enjtalk=False

class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    if Data.getGuildData(_getGuildId(message)).getProperty(property_name="enTTS"):
        try:
            await tts_callback(message)
        except Exception as e:
            logger.exception("TTS Error:")
except Exception as e:
    self.logger.exception("TTS Error:")
##tts
if enjtalk:
    @bot.group(name="tts", desecription="Text to Speech!!")
    async def tts(ctx):
        if ctx.invoked_subcommand is None:
            if Data.getGuildData(_getGuildId(ctx)).switchTTSChannel(ctx.channel):
                await ctx.send("TTS is now enable on this channel!!")
            else:
                await ctx.send("TTS is now disable on this channel!!")
    @bot.slash_command(name="tts", desecription="Text to Speech!!")
    async def tts(ctx):
        if Data.getGuildData(_getGuildId(ctx)).switchTTSChannel(ctx.channel):
            await ctx.respond("TTS is now enable on this channel!!")
        else:
            await ctx.respond("TTS is now disable on this channel!!")
    async def tts_callback(message):
        data=Data.getGuildData(_getGuildId(message))
        if message.channel.id in data.getTTSChannels():
            playlist=data.getPlaylist()
            vdata, vsr=pyopenjtalk.tts(message.content)
            bio=io.BytesIO()
            wavfile.write(bio, vsr, vdata.astype(numpy.int16))
            dpy_pcm=discord.PCMAudio(bio)
            if playlist.state=="play":
                playlist.pause()
                while True:
                    d=dpy_pcm.read()
                    if d == b'':
                        break
                    else:
                        playlist.channel.send_audio_packet(d, encode=True)
                playlist.resume()
            else:
                while True:
                    d=dpy_pcm.read()
                    if d == b'':
                        break
                    else:
                        playlist.channel.send_audio_packet(d, encode=True)
if not enjtalk: logger.warning("Jtalk is not enabled.")
def setup(bot):
    return bot.add_cog(MyCog(bot))
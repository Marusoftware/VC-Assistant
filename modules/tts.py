import logging, io, discord
from discord.ext import commands
from lib import _getGuildId, Send, randomstr
try:
    import pyopenjtalk, numpy
    from scipy.io import wavfile
    enjtalk=True
except:
    enjtalk=False

logger=logging.getLogger("TTS")

class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot=bot
        self.data=bot.data
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if self.data.getGuildData(_getGuildId(message)).getProperty(property_name="enTTS"):
            try:
                await self.tts_callback(message)
            except Exception as e:
                logger.exception("TTS Error:")
    @commands.group(name="tts", description="Text to Speech!!")
    async def tts(self, ctx):
        if ctx.invoked_subcommand is None:
            if self.data.getGuildData(_getGuildId(ctx)).switchTTSChannel(ctx.channel):
                await ctx.send("TTS is now enable on this channel!!")
            else:
                await ctx.send("TTS is now disable on this channel!!")
    @commands.slash_command(name="tts", description="Text to Speech!!")
    async def tts(self, ctx):
        if self.data.getGuildData(_getGuildId(ctx)).switchTTSChannel(ctx.channel):
            await ctx.respond("TTS is now enable on this channel!!")
        else:
            await ctx.respond("TTS is now disable on this channel!!")
    async def tts_callback(self, message):
        data=self.data.getGuildData(_getGuildId(message))
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
def setup(bot):
    if enjtalk:
        return bot.add_cog(TTS(bot))
    else:
        logger.warning("Jtalk is not enabled.")
import os
import random
import asyncio
import discord


playlist = dict()
voice_states = dict()
DEFAULT_VOLUME = 0.5
random_order = True


class PlaylistEntry:
    def __init__(self, requester, url):
        self.url = url
        self.requester = requester


class VoiceEntry:
    def __init__(self, requester, player):
        self.requester = requester
        self.player = player

    def __str__(self):
        requester = self.requester.nick if self.requester.nick else self.requester.name
        return "Now Playing: {} (신청자: {})".format(self.player.title, requester)


class VoiceState:
    def __init__(self, bot, server, vclient, channel):
        self.bot = bot
        self.server = server
        self.vclient = vclient
        self.text_channel = channel
        self.current = None
        self.play_next = asyncio.Event()
        self.playlist = asyncio.Queue()

    def is_playing(self):
        if not self.vclient or not self.current:
            return False
        return not self.current.player.is_done()

    def play(self):
        self.player = self.bot.loop.create_task(self.play_task())

    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next.set)

    async def play_task(self):
        while True:
            if self.playlist.empty():
                loaded = await get_playlist(self.server)
                for s in loaded:
                    await self.playlist.put(s)

            self.play_next.clear()
            song = await self.playlist.get()
            player = await self.vclient.create_ytdl_player(
                         song.url, after=self.toggle_next,
                         before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
            player.volumn = DEFAULT_VOLUME
            self.current = VoiceEntry(song.requester, player)
            await self.bot.edit_channel(self.text_channel, topic=str(self.current))
            self.current.player.start()
            await self.play_next.wait()


def get_voice_state(bot, server, vclient, channel):
    global voice_states

    state = voice_states.get(server.id)
    if not state:
        state = VoiceState(bot, server, vclient, channel)
        voice_states[server.id] = state
    return state


async def store_playlist(server, entry):
    filename = "playlist/{}.playlist".format(server.id)
    with open(filename, "at") as f:
        f.write("{} {}\n".format(entry.requester.id, entry.player.url))


async def get_playlist(server):
    global playlist

    if server.id in playlist:
        if random_order:
            random.shuffle(playlist[server.id])
        return playlist[server.id]

    else:
        entries = list()
        filename = "playlist/{}.playlist".format(server.id)
        if os.path.isfile(filename):
            with open(filename, "rt") as f:
                lines = f.readlines()
            for line in lines:
                member_id, url = line.split(" ")
                requester = server.get_member(member_id)
                entries.append(PlaylistEntry(requester, url))
        playlist[server.id] = entries
        if random_order:
            random.shuffle(entries)
        return entries

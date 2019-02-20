"""How to run this code.
1) Install python libraries.
   |  pip install discord pynacl youtube_dl
2) Check discord.key file. It should contains BOT_TOKEN value.
3) Run.
   |  python client.py
"""

import random
import asyncio
import discord
from discord.ext import commands

import utils
import music


if not discord.opus.is_loaded():
    # Change this value, which depends on OS.
    discord.opus.load_opus("libopus.so.1")

client = commands.Bot(command_prefix="!", description="")


@client.event
async def on_ready():
    print("Logged in as {}".format(client.user.name))


@client.event
async def on_message(msg):
    # When someone mentions this bot by "@미라#3409".
    if client.user in msg.mentions:
        vchannel = msg.author.voice_channel
        if vchannel:
            vclient = client.voice_client_in(msg.channel.server)
            if vclient:
                state = music.get_voice_state(client, msg.channel.server, vclient, msg.channel)
                await vclient.move_to(vchannel)
            else:
                vclient = await client.join_voice_channel(vchannel)
                state = music.get_voice_state(client, msg.channel.server, vclient, msg.channel)
                sent = await client.send_message(msg.channel,
                    embed=discord.Embed(
                        title="불러오는 중",
                        color=0xAAAAAA,
                        description="현재 서버의 재생목록을 불러오는 중입니다."
                    )
                )
                playlist = await music.get_playlist(msg.channel.server)
                for idx, song in enumerate(playlist):
                    await state.playlist.put(song)
                    sent = await client.edit_message(sent,
                        embed=discord.Embed(
                            title="불러오는 중",
                            color=0xAAAAAA,
                            description="현재 서버의 재생목록을 불러오는 중입니다. ({}/{})".format(idx+1, len(playlist))
                        )
                    )
                sent = await client.edit_message(sent,
                    embed=discord.Embed(
                        title="불러오기 완료",
                        color=0x77FF77,
                        description="현재 서버의 재생목록을 모두 불러왔습니다."
                    )
                )
                state.play()

    await client.process_commands(msg)


@client.command(name="추가", pass_context=True)
async def _add(ctx, *, song:str):
    server = ctx.message.channel.server
    vclient = client.voice_client_in(server)
    state = music.get_voice_state(client, server, vclient, ctx.message.channel)
    if not vclient:
        await client.send_message(ctx.message.channel,
            embed=discord.Embed(
                title="실행 오류",
                color=0xFF7777,
                description="음성채널에 접속하지 않았기 때문에 음악을 재생할 수 없습니다."
            )
        )
        return
    entry = music.PlaylistEntry(ctx.message.author, song)
    await state.playlist.put(entry)
    await music.store_playlist(server, entry)


@client.command(name="일시정지", pass_context=True)
async def _pause(ctx):
    server = ctx.message.channel.server
    vclient = client.voice_client_in(server)
    if vclient:
        state = music.get_voice_state(client, server, vclient, ctx.message.channel)
        if state.is_playing():
            state.current.player.pause()


@client.command(name="재생", pass_context=True)
async def _pause(ctx):
    server = ctx.message.channel.server
    vclient = client.voice_client_in(server)
    if vclient:
        state = music.get_voice_state(client, server, vclient, ctx.message.channel)
        if state.is_playing():
            state.current.player.resume()


@client.command(name="정지", pass_context=True)
async def _stop(ctx):
    server = ctx.message.channel.server
    vclient = client.voice_client_in(server)
    if vclient:
        state = music.get_voice_state(client, server, vclient, ctx.message.channel)
        if state.is_playing():
            state.current.player.stop()
        try:
            state.player.cancel()
            del music.voice_states[server.id]
            await vclient.disconnect()
            await client.edit_channel(ctx.message.channel, topic=None)
        except:
            pass


@client.command(name="순차재생", pass_context=True)
async def _continous_order(ctx):
    music.random_order = False
    await client.send_message(ctx.message.channel,
        embed=discord.Embed(
            title="재생순서 변경됨",
            color=0x77FF77,
            description="음악 재생순서가 **순차재생**으로 변경되었습니다."
        )
    )


@client.command(name="랜덤재생", pass_context=True)
async def _continous_order(ctx):
    music.random_order = False
    await client.send_message(ctx.message.channel,
        embed=discord.Embed(
            title="재생순서 변경됨",
            color=0x77FF77,
            description="음악 재생순서가 **랜덤재생**으로 변경되었습니다."
        )
    )


if __name__ == "__main__":
    token = utils.get_discord_token()
    if token is None:
        print("디스코드 봇의 토큰 값을 찾을 수 없습니다.")
    else:
        client.run(token)

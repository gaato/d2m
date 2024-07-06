import io
import os
import re
from datetime import datetime, timedelta

import discord
import dotenv
from misskey import Misskey

dotenv.load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)

names = ["HOLO", "MUSIC", "MERCH"]

channel_ids = [int(os.environ[f"DISCORD_CHANNEL_{name}_ID"]) for name in names]
print(channel_ids)

misskeys = [
    Misskey(os.environ["MISSKEY_HOST"], i=os.environ[f"MISSKEY_{name}_TOKEN"])
    for name in names
]
print(misskeys)


def convert_to_jst(timestamp: str) -> str:
    jst_offset = timedelta(hours=9)
    utc_time = datetime.utcfromtimestamp(int(timestamp))
    jst_time = utc_time + jst_offset
    return jst_time.strftime("%Y/%m/%d %H:%M JST")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    if message.channel.id not in channel_ids:
        return
    idx = channel_ids.index(message.channel.id)
    if idx < 0:
        return
    misskey = misskeys[idx]
    file_ids = []
    if message.attachments:
        for attachment in message.attachments:
            f = misskey.drive_files_create(
                file=io.BytesIO(await attachment.read()),
                name=attachment.filename,
            )
            file_ids.append(f["id"])

    discord_timestamp_pattern = r"<t:(\d+):[a-zA-Z]>"
    text = re.sub(
        discord_timestamp_pattern,
        lambda match: convert_to_jst(match.group(1)),
        message.content,
    )
    misskey.notes_create(
        text=text,
        file_ids=file_ids if file_ids else None,
        visibility="home",
    )


bot.run(os.environ["DISCORD_BOT_TOKEN"])

from unicodedata import name
from pyrogram.errors import MessageNotModified
from pyrogram import Client, filters
import datetime
import humanize
import asyncio
import pathlib
import uvloop
import time
import math
import os

# Environment Variables
TOKEN = os.getenv('TOKEN')
NAME = os.getenv('NAME')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

# Bot initialization

uvloop.install()

bot = Client(session_name=NAME, bot_token=TOKEN, api_hash=API_HASH, api_id=API_ID)

# Functions


async def shell_run(command):

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True,
        )

        stdout_raw, stderr_raw = await proc.communicate()
        stdout = stdout_raw.decode()
        stderr = stderr_raw.decode()

    except Exception as e:
        stdout = ''
        stderr = 'Critical exception ' + str(e)

    return stdout, stderr


async def get_thumbnail(video: str):
    duration, duration_error = await shell_run(
        f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video}"'
    )
    duration = int(float(duration.replace("\n", ""))) # Future Nolan, remember always to add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git to the heroku buildpacks (though it will close free dynos before you'd need this comment)
    seconds_raw = duration * 25 / 100
    seconds = int(seconds_raw)
    frame = datetime.timedelta(seconds=seconds)

    width, width_error = await shell_run(
        f'ffprobe -v error -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "{video}"'
    )
    height, height_error = await shell_run(
        f'ffprobe -v error -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "{video}"'
    )
    width = int(width)
    height = int(height)

    extension = pathlib.Path(video).suffix
    video_thumb = video.replace(extension, " thumbnail.jpg")

    await shell_run(
        f'ffmpeg -ss {frame} -i "{video}" -frames:v 1 -q:v 2 "{video_thumb}" -y'
    )

    if width > 320 and width > height:
        await shell_run(
            f'ffmpeg -i "{video_thumb}" -vf scale=320:-1 "{video_thumb}" -y'
        )
    elif height > 320 and width < height:
        await shell_run(
            f'ffmpeg -i "{video_thumb}" -vf scale=-1:320 "{video_thumb}" -y'
        )

    return video_thumb


async def progress_bar(current, total, status_msg, start, msg, filename):
    present = time.time()
    if round((present - start) % 3) == 0 or current == total:
        speed = current / (present - start)
        percentage = current * 100 / total
        time_to_complete = round(((total - current) / speed))
        time_to_complete = humanize.naturaldelta(time_to_complete)
        progressbar = "[{0}{1}]".format(
            "".join(["██" for i in range(math.floor(percentage / 10))]),
            "".join(["░░" for i in range(10 - math.floor(percentage / 10))]),
        )
        current_message = f"""{status_msg} {filename} {round(percentage, 2)}%
{progressbar}
📈 Speed: {humanize.naturalsize(speed)}/s
✅ Done: {humanize.naturalsize(current)}
🔲 Size: {humanize.naturalsize(total)}
🕔 Time Left: {time_to_complete}"""
        try:
            await msg.edit_text(current_message)
        except MessageNotModified as e:
            print(e)


# Message Handlers
@bot.on_message(filters=filters.command('start'))
async def welcome(client, message):
    await bot.send_message(
        chat_id=message.chat.id,
        text='Hello! I\'m your Telegram Video Toolkit, execute /help to learn how to use me'
    )


@bot.on_message(filters=filters.command('help'))
async def helper(client, message):
    await bot.send_message(
        chat_id=message.chat.id,
        text='''/resize - Resize/rescale a video using a given height, the bot automatically calculates the width keeping the aspect ratio, execute it with the format "/resize {height}", e. g. "/resize 360" (replying to the video)
/rename - Rename a file, e. g. "/rename {wanted name}"
/yt_dl - Download a video from YouTube, it downloads the highest resolution possible, e. g. "/yt_dl {YouTube link}"''',
    )


@bot.on_message(filters=filters.command('resize'))
async def resizer(client, message):
    replied_message = await bot.get_messages(
        chat_id=message.chat.id, 
        reply_to_message_ids=message.message_id
    )

    requested_height = message.text.replace('/resize ', '')
    file_name = getattr(replied_message, replied_message.media).file_name
    file_path = f'/app/downloads/{file_name}'
    start_time = time.time()

    response = await bot.send_message(
        chat_id=message.chat.id, 
        text='Downloading...'
        )

    download = await bot.download_media(
        message=replied_message,
        file_name=file_path,
        progress=progress_bar,
        progress_args=('Downloading:', start_time, response, file_name),
    )

    video_thumb = await get_thumbnail(download)
    extension = pathlib.Path(file_path).suffix
    resized_video = str(file_path).replace(extension, f' {requested_height}p.mp4')
    resized_video_name = pathlib.Path(resized_video).name
    video_duration, duration_errors = await shell_run(
        f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{download}"'
    )
    print('FIRST' + video_duration)
    video_duration = video_duration.replace('\n', ' ')
    print('SECOND' + video_duration)
    video_duration = int(float(video_duration))

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=response.message_id,
        text='Resizing video...'
    )

    await shell_run(
        f'ffmpeg -i "{download}" -vf scale=-2:{requested_height} -f mp4 "{resized_video}" -y'
    )

    await bot.edit_message_text(
        chat_id=message.chat.id, 
        message_id=response.message_id, 
        text='Uploading...'
    )

    await bot.send_video(
        chat_id=message.chat.id,
        video=resized_video,
        caption=f'Finished the resizing of:\n"{resized_video_name}"',
        thumb=video_thumb,
        progress=progress_bar,
        progress_args=('Uploading:', start_time, response, resized_video_name),
        duration=video_duration
    )

    await bot.delete_messages(
        chat_id=message.chat.id, 
        message_ids=response.message_id
    )


@bot.on_message(filters=filters.command('rename'))
async def renamer(client, message):
    requested_name = message.text.replace('/rename ', '')
    start_time = time.time()

    try:
        replied_message = await bot.get_messages(
            chat_id=message.chat.id, reply_to_message_ids=message.message_id
        )

        file_name = replied_message.video.file_name
        file_path = f'/app/downloads/{file_name}'

        response = await bot.send_message(
            chat_id=message.chat.id, text='Downloading...'
        )

        download = await bot.download_media(
            message=replied_message,
            file_name=file_path,
            progress=progress_bar,
            progress_args=('Downloading:', start_time, response, file_name),
        )

        video_thumb = await get_thumbnail(download)
        video_duration, duration_errors = await shell_run(
            f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{download}"'
        )
        video_duration = video_duration.replace("\n", "")
        video_duration = int(float(video_duration))

        extension = pathlib.Path(file_path).suffix
        new_file_path = pathlib.Path(file_path).rename(requested_name + extension)
        new_file_name = pathlib.Path(new_file_path).name

        await bot.edit_message_text(
            chat_id=message.chat.id, message_id=response.message_id, text='Uploading...'
        )

        await bot.send_video(
            chat_id=message.chat.id,
            video=new_file_path,
            caption=f'Renamed file to "{new_file_name}"',
            thumb=video_thumb,
            progress=progress_bar,
            progress_args=('Uploading:', start_time, response, new_file_name),
            duration=video_duration,
        )

        await bot.delete_messages(
            chat_id=message.chat.id, message_ids=response.message_id
        )

    except AttributeError:
        await bot.send_message(
            chat_id=message.chat.id,
            reply_to_message_id=message.message_id,
            text='To use this command, you must reply to a valid Telegram file',
        )


@bot.on_message(filters=filters.command('encode'))
async def encoder(client, message):
    replied_message = await bot.get_messages(
        chat_id=message.chat.id,
        reply_to_message_ids=message.message_id
    )

    file_name = getattr(replied_message, replied_message.media).file_name
    file_path = f'/app/downloads/{file_name}'
    start_time = time.time()

    response = await bot.send_message(
        chat_id=message.chat.id,
        text='Downloading...'
        )
    
    download = await bot.download_media(
        message=replied_message,
        file_name=file_path,
        progress=progress_bar,
        progress_args=('Downloading:', start_time, response, file_name)
    )

    video_thumb = await get_thumbnail(download)
    extension = pathlib.Path(file_path).suffix
    encoded_video = str(file_path).replace(extension, f' encoded.mp4')
    encoded_video_name = pathlib.Path(encoded_video).name
    video_duration, duration_errors = await shell_run(
        f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{download}"'
        )

    print(video_duration)
    video_duration = video_duration.replace('\n', '')
    video_duration = int(float(video_duration))

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=response.message_id,
        text='Encoding video'
    )

    await shell_run(
        f'ffmpeg -i "{download}" -c:v libx265 -c:a copy -x265-params crf=25 "{encoded_video_name}"'
    )

    await bot.edit_message_text(
        chat_id=message.chat.id, 
        message_id=response.message_id, 
        text="Uploading..."
    )

    await bot.send_video(
        chat_id=message.chat.id,
        video=encoded_video,
        caption=f'Finished the encoding of:\n"{encoded_video_name}"',
        thumb=video_thumb,
        progress=progress_bar,
        progress_args=('Uploading:', start_time, response, encoded_video_name),
        duration=video_duration
    )

    await bot.delete_messages(
        chat_id=message.chat.id,
        message_ids=response.message_id
        )


@bot.on_message(filters=filters.command('info'))
async def properties(client, message):
	replied_message = await bot.get_messages(
        chat_id=message.chat.id,
        reply_to_message_ids=message.message_id
    )
    
	file_name = getattr(replied_message, replied_message.media).file_name
	extension = pathlib.Path(file_name).suffix
	raw_duration = getattr(replied_message, replied_message.media).duration
	duration = str(datetime.timedelta(seconds = int(raw_duration)))
	raw_file_size = getattr(replied_message, replied_message.media).file_size
	file_size = humanize.naturalsize(int(raw_file_size))
	width = getattr(replied_message, replied_message.media).width
	height = getattr(replied_message, replied_message.media).height
	resolution = f'{height}p x {width}p'
	
	await bot.send_message(
        chat_id=message.chat.id,
        text=f'''📋Properties:

🆔Name: {file_name}
🎬Format: {extension}
⏰Duration: {duration}
📦Size: {file_size}
📏Resolution: {resolution}'''
        )


bot.run()

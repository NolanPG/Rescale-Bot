from pyrogram import Client, filters
from threading import Thread
from pytube import YouTube
import subprocess
import cv2
import pathlib


bot = Client(
    'TVT',
    bot_token='5118931943:AAFtqUOmTordsumt0yKerHcVlz-sUjRuCDA'
)

async def get_video_duration(url: str):
    data = await cv2.VideoCapture(url)

    frames = await data.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = await int(data.get(cv2.CAP_PROP_FPS))

    seconds = await int(frames / fps)

    return seconds
    

@bot.on_message(filters=filter.command('start'))
async def welcome(message):
    await bot.send_message(
        chat_id=message.chat.id, 
        text='Hello! I\'m your Telegram Video Toolkit, execute /help to learn how to use me'
        )


@bot.on_message(filters=filter.command('help'))
async def helper(message):
    await bot.send_message(
        chat_id=message.chat.id, 
        text='''/resize - Resize/rescale a video using a given height, the bot automatically calculates the width keeping the aspect ratio, execute it with the format "/resize {height}", e. g. "/resize 360" (replying to the video)
/rename - Rename a file, e. g. "/rename {wanted name}"
/yt_dl - Download a video from YouTube, it downloads the highest resolution possible, e. g. "/yt_dl {YouTube link}"'''
)


@bot.on_message(filters=filter.command('resize'))
async def resizer(message):
    replied_message = await bot.get_messages(
        chat_id=message.chat.id,
        reply_to_message_ids=message.message_id
    )

    requested_height = message.text.replace('/resize ', '')
    file_name = replied_message.document.file_name
    file_path = f'/app/downloads/{file_name}'

    response = await bot.send_message(
        chat_id=message.chat.id, 
        text='Downloading...'
        )

    download = await bot.download_media(message=replied_message, file_name=file_path)

    extension = pathlib.Path(download).suffix
    resized_video = str(download).replace(extension, f' {requested_height}p.mp4')
    resized_video_name = pathlib.Path(resized_video).name
    video_duration = get_video_duration(resized_video)
    video_size = pathlib.Path(resized_video).stat().st_size

    def ffmpeg():
        try:
            return subprocess.run(f'ffmpeg -i "{download}" -vf scale=-1:{requested_height} -f mp4 "{resized_video}" -y', shell=True, check=False)
        except Exception as e:
            return e

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=response,
        text='Resizing video...'
        )

    t = Thread(target=ffmpeg)
    t.start()
    t.join()

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=response,
        text='Uploading...'
        )

    await bot.send_video(
        chat_id=message.chat.id, 
        video=resized_video, 
        caption=f'Finished the resizing of:\n "{resized_video_name}"',
        duration=video_duration,
        total=video_size
        )
    
    await bot.delete_messages(
        chat_id=message.chat.id, 
        message_ids=message.message_id
        )


@bot.on_message(filters=filter.command('rename'))
async def renamer(message):
    requested_name = message.text.replace('/rename ', '')

    try:
        replied_message = await bot.get_messages(
            chat_id=message.chat.id,
            reply_to_message_ids=message.message_id
            )

        file_name = replied_message.document.file_name
        file_path = f'/app/downloads/{file_name}'

        await bot.download_media(message=replied_message, file_name=file_path)

        extension = pathlib.Path(file_path).suffix
        new_file_path = pathlib.Path(file_path).rename(requested_name + extension)
        new_file_name = pathlib.Path(new_file_path).name
        video_duration = get_video_duration(new_file_path)
        video_size = pathlib.Path(new_file_path).stat().st_size 

        await bot.send_video(
            chat_id=message.chat.id, 
            document=new_file_path, 
            caption=f'Renamed file to "{new_file_name}"',
            duration=video_duration,
            total=video_size
            )

    except AttributeError:
        await bot.send_message(
            chat_id=message.chat.id, 
            reply_to_message_id=message.message_id, 
            text='To use this command, you must reply to a valid Telegram file'
            )


@bot.on_message(filters=filter.command('yt_dl'))
async def yt_downloader(message):
    link = message.text.replace('/yt_dl ', '')

    response = await bot.send_message(
        chat_id=message.chat.id, 
        text='Downloading...'
        )
    
    yt = YouTube(link).streams.get_highest_resolution().download(output_path='/app/Youtube_downloads/')

    video_duration = get_video_duration(yt)
    video_size = pathlib.Path(yt).stat().st_size

    await bot.edit_message_text(
        chat_id=message.chat.id, 
        message_id=message.message_id, 
        text='Uploading'
        )
    
    await bot.send_video(
        chat_id=message.chat.id, 
        file=yt, 
        caption=pathlib.Path(yt).name,
        duration=video_duration,
        total=video_size
        )

    await bot.delete_messages(chat_id=message.chat.id, message_ids=message.message_id)


bot.run()

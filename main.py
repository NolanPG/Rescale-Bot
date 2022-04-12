from telethon import TelegramClient, events
from threading import Thread
from pytube import YouTube
import subprocess
import pathlib

api_id = 4482188
api_hash = '0712c4aacf5e779ed9f55421c1813aed'
bot_token = '5118931943:AAFtqUOmTordsumt0yKerHcVlz-sUjRuCDA'

bot = TelegramClient('rescaletestbot', api_id, api_hash).start(bot_token=bot_token)


@bot.on(events.NewMessage(pattern='/start'))
async def welcome(event):
	await bot.send_message(entity=event.chat_id, message='Hello! I\'m your Telegram Video Toolkit, execute /help to learn how to use me')


@bot.on(events.NewMessage(pattern='/help'))
async def helper(event):
	await bot.send_message(entity=event.chat_id, message='''/resize - Resize/rescale a video using a given height, the bot automatically calculates the width keeping the aspect ratio, execute it with the format "/resize {height}", e. g. "/resize 360" (replying to the video)

/rename - Rename a file, e. g. "/rename {wanted name}"

/yt_dl - Download a video from YouTube, it downloads the highest resolution possible, e. g. "/yt_dl {YouTube link}''')


@bot.on(events.NewMessage(pattern='/resize'))
async def resizer(event):
    replied_message = await event.get_reply_message()
    
    requested_height = event.raw_text.replace('/resize ', '')
    file_name = replied_message.file.name
    file_path = f'/app/downloads/{file_name}'
	
    response = await bot.send_message(event.chat_id, 'Downloading...')
    
    download = await bot.download_media(message=replied_message, file=file_path)
    
    extension = pathlib.Path(download).suffix
    resized_video = str(download).replace(extension, f'_{requested_height}p.mp4')
    resized_video_name = pathlib.Path(resized_video).name
    
    def ffmpeg():
        try:
            return subprocess.run(f'ffmpeg -i {download} -vf scale=-1:{requested_height} -f mp4 {resized_video} -y', shell=True)
        except Exception as e:
            return e,

    await response.edit('Resizing video...')
    t = Thread(target=ffmpeg)
    t.start()
    t.join()
	
    await response.edit('Uploading...')
    
    await bot.send_file(entity=event.chat_id, file=resized_video, caption=f'Finished the resizing of "{resized_video_name}"')
    
    await bot.delete_messages(entity=event.chat_id, message_ids=response)
    
    
@bot.on(events.NewMessage(pattern='/rename'))
async def renamer(event):
	requested_name = event.raw_text.replace('/rename ', '')
	
	replied_message = await event.get_reply_message()
	
	file_name = replied_message.file.name
	file_path = f'/app/downloads/{file_name}'
	
	await bot.download_media(message=replied_message, file=file_path)
	
	extension = pathlib.Path(file_path).suffix
	new_file_path = pathlib.Path(file_path).rename(requested_name+extension)
	new_file_name = pathlib.Path(new_file_path).name
	
	await bot.send_file(entity=event.chat_id, file=new_file_path, caption=f'Renamed file to "{new_file_name}"')
	

@bot.on(events.NewMessage(pattern='/yt_dl'))
async def yt_downloader(event):
	link = event.raw_text.replace('yt_dl ', '')
	
	response = await bot.send_message(entity=event.chat_id, message='Downloading...')
	
	yt = YouTube(link).streams.get_highest_resolution().download(output_path='/app/')
	
	await response.edit('Uploading...')
	
	await bot.send_file(entity=event.chat_id, file=yt, caption=pathlib.Path(yt).name)
	
	await bot.delete_messages(entity=event.chat_id, message_ids=response)

bot.run_until_disconnected()

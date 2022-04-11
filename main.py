from telethon import TelegramClient, events
from threading import Thread
import subprocess
import pathlib

api_id = 4482188
api_hash = '0712c4aacf5e779ed9f55421c1813aed'
bot_token = '5118931943:AAFtqUOmTordsumt0yKerHcVlz-sUjRuCDA'

bot = TelegramClient('rescaletestbot', api_id, api_hash).start(bot_token=bot_token)


@bot.on(events.NewMessage)
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
            return e

    response.edit('Resizing video...')
    t = Thread(target=ffmpeg)
    t.start()
    t.join()
	
    response.edit('Uploading...')
    
    await bot.send_file(entity=event.chat_id, file=resized_video, caption=f'Finished the resizing of "{resized_video_name}"')
    
    await bot.delete_messages(entity=event.chat_id, message_ids=response)
    

bot.run_until_disconnected()
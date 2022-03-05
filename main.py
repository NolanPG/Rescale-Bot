import moviepy.editor as mp
from pyrogram import Client, filters
import moviepy.video.io.ffmpeg_tools as ffmpeg

bot = Client(
    "rescaletestbot",
    bot_token="5258246251:AAHloqD0rw0X_iH5JPEG27qoWC3k3JQ8Q2A"
)

#Variables
size = [360, 640]
welcome_text_sp = "Bienvenida al bot :v"
help_text_sp = "Explicación detallada del bot :v"


#Functions
@bot.on_message(filters.command("start"))
async def welcome(client, message):
    await bot.send_message(chat_id=message.chat.id,
                           text=welcome_text_sp,
                           reply_to_message_id=message.message_id)


@bot.on_message(filters.command("help"))
async def helper(client, message):
    await bot.send_message(chat_id=message.chat.id,
                           text=help_text_sp,
                           reply_to_message_id=message.message_id)


@bot.on_message(filters.command(["resize"]))
async def resizer(client, message):
    replied_message = await bot.get_messages(chat_id=message.chat.id,
                                             reply_to_message_ids=message.message_id)
    requested_height = message.text.replace('/resize ', '')
    if replied_message.video is not None:
        if replied_message.video.file_name is None:
            if replied_message.video.mime_type == 'video/mp4':
                extension = '.mp4'
            elif replied_message.video.mime_type == 'video/x-matroska':
                extension = '.mkv'
            elif replied_message.video.mime_type == 'video/x-msvideo':
                extension = '.avi'
            else:
                extension = '.mp4'

            video_name = 'video ' + str(replied_message.video.file_unique_id) + extension
            download = await bot.download_media(message=replied_message.video.file_id,
                                                file_name=video_name)
        else:
            download = await bot.download_media(message=replied_message.video.file_id,
                                                file_name=replied_message.video.file_name)
    else:
        if replied_message.document.file_name is None:
            if replied_message.document.mime_type == 'video/mp4':
                extension = '.mp4'
            elif replied_message.document.mime_type == 'video/x-matroska':
                extension = '.mkv'
            elif replied_message.document.mime_type == 'video/x-msvideo':
                extension = '.avi'
            else:
                extension = '.mp4'

            video_name = 'video ' + str(replied_message.document.file_unique_id) + extension
            download = await bot.download_media(message=replied_message.document.file_id,
                                                file_name=video_name)
        else:
            download = await bot.download_media(message=replied_message.document.file_id,
                                                file_name=replied_message.document.file_name)

    resized_video = download[::-1].replace(".", f" {requested_height}p."[::-1], 1)[::-1]

    if str(resized_video).endswith('.mp4') or str(resized_video).endswith('.mkv'):
        codec = 'mpeg4'
    elif str(resized_video).endswith('.ogv'):
        codec = 'libvorbis'
    elif str(resized_video).endswith('.webm'):
        codec = 'libvpx'
    else:
        codec = None

    try:
        clip = mp.VideoFileClip(download)
        clip_resized = clip.resize(height=int(requested_height))
        resized_video = clip_resized.write_videofile(resized_video, codec=codec)

    except ValueError:
        await bot.send_message(chat_id=message.chat.id,
                               text='Altura no permitida')

    await bot.send_video(chat_id=message.chat.id, video=resized_video)

bot.run()

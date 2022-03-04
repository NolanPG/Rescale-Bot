import moviepy.editor as mp
from pyrogram import Client, filters

bot = Client(
    "rescaletestbot",
    bot_token="5258246251:AAHloqD0rw0X_iH5JPEG27qoWC3k3JQ8Q2A"
)

#Variables
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
    requested_height = message.text.replace('/resize ', '')
    replied_message = await bot.get_messages(chat_id=message.chat.id,
                                             reply_to_message_ids=message.message_id)
    download = await bot.download_media(replied_message.video.file_id,
                                        replied_message.video.file_name)
    resized_video = download[::-1].replace(".", f" {requested_height}p."[::-1], 1)[::-1]

    if resized_video.endswith(".mp4"):
        codec = 'mpeg4'
    elif resized_video.endswith(".ogv"):
        codec = 'libvorbis'
    elif resized_video.endswith(".webm"):
        codec = 'libvpx'
    else:
        codec = None

    try:
        clip = mp.VideoFileClip(download)
        clip_resized = clip.resize(height=int(requested_height))
        """changing the height (According to moviePy documentation The width is then computed so that the
        width/height ratio is conserved.)"""
        clip_resized.write_videofile(resized_video, codec=codec)

        await bot.send_video(chat_id=message.chat.id, video=resized_video)

    except ValueError:
        await bot.send_message(chat_id=message.chat.id,
                         text='Altura no permitida')

bot.run()

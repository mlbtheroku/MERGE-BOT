# bot.py
from dotenv import load_dotenv
load_dotenv("config.env", override=True)

import os
import time
import shutil
import asyncio
import psutil
import pyromod
from PIL import Image
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, InputUserDeactivated, PeerIdInvalid, UserIsBlocked
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, User

from __init__ import (
    AUDIO_EXTENSIONS, BROADCAST_MSG, LOGGER, MERGE_MODE,
    SUBTITLE_EXTENSIONS, UPLOAD_AS_DOC, UPLOAD_TO_DRIVE,
    VIDEO_EXTENSIONS, bMaker, formatDB, gDict, queueDB, replyDB
)
from config import Config
from helpers import database
from helpers.utils import UserSettings, get_readable_file_size, get_readable_time

botStartTime = time.time()
parent_id = Config.GDRIVE_FOLDER_ID

class MergeBot(Client):
    def start(self):
        super().start()
        try:
            self.send_message(chat_id=int(Config.OWNER), text="<b>Bot Started!</b>")
        except Exception as err:
            LOGGER.error("Boot alert failed! Please start bot in PM")
        LOGGER.info("Bot Started!")

    def stop(self):
        super().stop()
        LOGGER.info("Bot Stopped")


mergeApp = MergeBot(
    name="merge-bot",
    api_hash=Config.API_HASH,
    api_id=Config.TELEGRAM_API,
    bot_token=Config.BOT_TOKEN,
    workers=300,
    plugins=dict(root="plugins"),
    app_version="5.0+yash-mergebot",
)

# Ensure the downloads directory exists
os.makedirs("downloads", exist_ok=True)


@mergeApp.on_message(filters.command(["log"]) & filters.user(Config.OWNER_USERNAME))
async def sendLogFile(c: Client, m: Message):
    try:
        await m.reply_document(document="./mergebotlog.txt")
    except FileNotFoundError:
        await m.reply_text("Log file not found.")
    except Exception as e:
        LOGGER.error(f"Failed to send log file: {e}")


@mergeApp.on_message(filters.command(["login"]) & filters.private)
async def loginHandler(c: Client, m: Message):
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    
    if user.banned:
        await m.reply_text(
            text=f"**Banned User Detected!**\n  🛡️ Unfortunately, you can't use me\n\nContact: 🈲 @{Config.OWNER_USERNAME}", 
            quote=True
        )
        return
    
    if user.user_id == int(Config.OWNER):
        user.allowed = True
    
    if user.allowed:
        await m.reply_text(text=f"**Don't Spam**\n  ⚡ You can use me!!", quote=True)
    else:
        try:
            passwd = m.text.split(" ", 1)[1].strip()
        except IndexError:
            await m.reply_text(
                "**Command:**\n  `/login <password>`\n\n**Usage:**\n  `password`: Get the password from owner",
                quote=True,
                parse_mode=enums.ParseMode.MARKDOWN
            )
            return
        
        if passwd == Config.PASSWORD:
            user.allowed = True
            await m.reply_text(
                text=f"**Login passed ✅,**\n  ⚡ Now you can use me!!", quote=True
            )
        else:
            await m.reply_text(
                text=f"**Login failed ❌,**\n  🛡️ Unfortunately, you can't use me\n\nContact: 🈲 @{Config.OWNER_USERNAME}",
                quote=True,
            )
    
    user.set()
    return


@mergeApp.on_message(filters.command(["stats"]) & filters.private)
async def stats_handler(c: Client, m: Message):
    try:
        currentTime = get_readable_time(time.time() - botStartTime)
        total, used, free = shutil.disk_usage(".")
        total = get_readable_file_size(total)
        used = get_readable_file_size(used)
        free = get_readable_file_size(free)
        sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
        recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
        cpuUsage = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        stats = (
            f"<b>╭「 💠 BOT STATISTICS 」</b>\n"
            f"<b>│</b>\n"
            f"<b>├⏳ Bot Uptime : {currentTime}</b>\n"
            f"<b>├💾 Total Disk Space : {total}</b>\n"
            f"<b>├📀 Total Used Space : {used}</b>\n"
            f"<b>├💿 Total Free Space : {free}</b>\n"
            f"<b>├🔺 Total Upload : {sent}</b>\n"
            f"<b>├🔻 Total Download : {recv}</b>\n"
            f"<b>├🖥 CPU : {cpuUsage}%</b>\n"
            f"<b>├⚙️ RAM : {memory}%</b>\n"
            f"<b>╰💿 DISK : {disk}%</b>"
        )
        await m.reply_text(text=stats, quote=True)
    except Exception as e:
        LOGGER.error(f"Failed to fetch stats: {e}")
        await m.reply_text(text="Error retrieving bot statistics. Please try again later.", quote=True)


@mergeApp.on_message(
    filters.command(["broadcast"])
    & filters.private
    & filters.user(Config.OWNER_USERNAME)
)
async def broadcast_handler(c: Client, m: Message):
    msg = m.reply_to_message
    userList = await database.broadcast()
    total_users = userList.collection.count_documents({})
    status = await m.reply_text(text=BROADCAST_MSG.format(str(total_users), "0"), quote=True)
    success = 0

    for i in range(total_users):
        try:
            uid = userList[i]["_id"]
            if uid != int(Config.OWNER):
                await msg.copy(chat_id=uid)
            success = i + 1
            await status.edit_text(text=BROADCAST_MSG.format(total_users, success))
            LOGGER.info(f"Message sent to {userList[i]['name']} ")
        except FloodWait as e:
            LOGGER.warning(f"FloodWait: Sleeping for {e.x} seconds")
            await asyncio.sleep(e.x)
            continue
        except InputUserDeactivated:
            await database.deleteUser(userList[i]["_id"])
            LOGGER.info(f"{userList[i]['_id']} - {userList[i]['name']} : deactivated")
        except UserIsBlocked:
            await database.deleteUser(userList[i]["_id"])
            LOGGER.info(f"{userList[i]['_id']} - {userList[i]['name']} : blocked the bot")
        except PeerIdInvalid:
            await database.deleteUser(userList[i]["_id"])
            LOGGER.info(f"{userList[i]['_id']} - {userList[i]['name']} : user id invalid")
        except Exception as err:
            LOGGER.warning(f"Broadcast Error for {userList[i]['name']} - {err}")
        await asyncio.sleep(1)  # Reduced sleep time for efficiency
    await status.edit_text(
        text=BROADCAST_MSG.format(total_users, success)
        + f"**Failed: {str(total_users - success)}**\n\n__🤓 Broadcast completed successfully__",
    )


@mergeApp.on_message(filters.command(["start"]) & filters.private)
async def start_handler(c: Client, m: Message):
    user = UserSettings(m.from_user.id, m.from_user.first_name)

    if m.from_user.id != int(Config.OWNER):
        if not user.allowed:
            await m.reply_text(
                text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately, you can't use me\n\n**Contact: 🈲 @{Config.OWNER_USERNAME}** ",
                quote=True,
            )
            return
    else:
        user.allowed = True
        user.set()
    await m.reply_text(
        text=f"Hi **{m.from_user.first_name}**\n\n ⚡ I am a file/video merger bot\n\n😎 I can merge Telegram files and upload them to Telegram\n\n**Owner: 🈲 @{Config.OWNER_USERNAME}** ",
        quote=True,
    )
    del user

@mergeApp.on_message(
    (filters.document | filters.video | filters.audio) & filters.private
)
async def files_handler(c: Client, m: Message):
    user_id = m.from_user.id
    user = UserSettings(user_id, m.from_user.first_name)

    if user_id != int(Config.OWNER) and not user.allowed:
        await m.reply_text(
            text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately you can't use me\n\n**Contact: 🈲 @{Config.OWNER_USERNAME}** ",
            quote=True,
        )
        return

    if user.merge_mode == 4:  # extract_mode
        return

    input_ = f"downloads/{str(user_id)}/input.txt"
    if os.path.exists(input_):
        await m.reply_text("Sorry Bro,\nAlready One process in Progress!\nDon't Spam.")
        return

    media = m.video or m.document or m.audio
    if not media or not media.file_name:
        await m.reply_text("File Not Found or Unsupported Media Type.")
        return

    currentFileNameExt = media.file_name.rsplit(sep=".")[-1].lower()

    if currentFileNameExt == "conf":
        await m.reply_text(
            text="**💾 Config file found, Do you want to save it?**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✅ Yes", callback_data=f"rclone_save"),
                        InlineKeyboardButton("❌ No", callback_data="rclone_discard"),
                    ]
                ]
            ),
            quote=True,
        )
        return

    if user.merge_mode == 1:
        await handle_video_merge(c, m, user_id, currentFileNameExt)
    elif user.merge_mode == 2:
        await handle_audio_merge(c, m, user_id, currentFileNameExt)
    elif user.merge_mode == 3:
        await handle_subtitle_merge(c, m, user_id, currentFileNameExt)

async def handle_video_merge(c: Client, m: Message, user_id: int, file_ext: str):
    if queueDB.get(user_id) is None:
        formatDB[user_id] = file_ext
        queueDB[user_id] = {"videos": [], "subtitles": [], "audios": []}

    if file_ext not in VIDEO_EXTENSIONS:
        await m.reply_text("This Video Format is not allowed! Only send MP4, MKV, or WEBM.", quote=True)
        return

    editable = await m.reply_text("Please Wait ...", quote=True)
    max_videos = 10

    if len(queueDB[user_id]["videos"]) < max_videos:
        queueDB[user_id]["videos"].append(m.id)
        queueDB[user_id]["subtitles"].append(None)

        if len(queueDB[user_id]["videos"]) == 1:
            reply_ = await editable.edit(
                "**Send me more videos to merge them into a single file**",
                reply_markup=InlineKeyboardMarkup(
                    bMaker.makebuttons(["Cancel"], ["cancel"])
                ),
            )
            replyDB[user_id] = reply_.id
            return

        markup = await makeButtons(c, m, queueDB)
        reply_ = await editable.edit(
            text="Now send more videos or press **Merge Now**.", reply_markup=InlineKeyboardMarkup(markup)
        )
        replyDB[user_id] = reply_.id

    else:
        markup = await makeButtons(c, m, queueDB)
        await editable.edit("Max 10 videos allowed", reply_markup=InlineKeyboardMarkup(markup))

async def handle_audio_merge(c: Client, m: Message, user_id: int, file_ext: str):
    if queueDB.get(user_id) is None:
        queueDB[user_id] = {"videos": [], "subtitles": [], "audios": []}

    editable = await m.reply_text("Please Wait ...", quote=True)

    if len(queueDB[user_id]["videos"]) == 0:
        queueDB[user_id]["videos"].append(m.id)
        reply_ = await editable.edit(
            text="Now, send all the audios you want to merge",
            reply_markup=InlineKeyboardMarkup(
                bMaker.makebuttons(["Cancel"], ["cancel"])
            ),
        )
        replyDB[user_id] = reply_.id
        return

    if file_ext in AUDIO_EXTENSIONS:
        queueDB[user_id]["audios"].append(m.id)
        markup = await makeButtons(c, m, queueDB)
        reply_ = await editable.edit(
            text="Now send more audios or press **Merge Now**.", reply_markup=InlineKeyboardMarkup(markup)
        )
        replyDB[user_id] = reply_.id
    else:
        await m.reply("This Filetype is not valid for audio merging.", quote=True)

async def handle_subtitle_merge(c: Client, m: Message, user_id: int, file_ext: str):
    if queueDB.get(user_id) is None:
        queueDB[user_id] = {"videos": [], "subtitles": [], "audios": []}

    editable = await m.reply_text("Please Wait ...", quote=True)

    if len(queueDB[user_id]["videos"]) == 0:
        queueDB[user_id]["videos"].append(m.id)
        reply_ = await editable.edit(
            text="Now, send all the subtitles you want to merge",
            reply_markup=InlineKeyboardMarkup(
                bMaker.makebuttons(["Cancel"], ["cancel"])
            ),
        )
        replyDB[user_id] = reply_.id
        return

    if file_ext in SUBTITLE_EXTENSIONS:
        queueDB[user_id]["subtitles"].append(m.id)
        markup = await makeButtons(c, m, queueDB)
        reply_ = await editable.edit(
            text="Now send more subtitles or press **Merge Now**.", reply_markup=InlineKeyboardMarkup(markup)
        )
        replyDB[user_id] = reply_.id
    else:
        await m.reply("This Filetype is not valid for subtitle merging.", quote=True)

@mergeApp.on_message(filters.photo & filters.private)
async def photo_handler(c: Client, m: Message):
    user = UserSettings(m.chat.id, m.from_user.first_name)

    if not user.allowed:
        await m.reply_text(
            text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately, you can't use me\n\n**Contact: 🈲 @{Config.OWNER_USERNAME}** ",
            quote=True,
        )
        del user
        return
    
    msg = await m.reply_text("Saving Thumbnail...", quote=True)
    user.thumbnail = m.photo.file_id
    user.set()

    LOCATION = f"downloads/{m.from_user.id}_thumb.jpg"
    await c.download_media(message=m, file_name=LOCATION)
    await msg.edit_text("✅ Custom Thumbnail Saved!")
    del user


@mergeApp.on_message(filters.command(["extract"]) & filters.private)
async def media_extracter(c: Client, m: Message):
    user = UserSettings(uid=m.from_user.id, name=m.from_user.first_name)
    
    if not user.allowed:
        return

    if user.merge_mode != 4:
        await m.reply("Change settings and set mode to extract, then use the /extract command")
        return

    if m.reply_to_message is None:
        await m.reply("Reply to a video or document file with /extract to extract media.")
        return

    rmess = m.reply_to_message
    media = rmess.video or rmess.document
    
    if media:
        file_name = media.file_name
        if not file_name:
            await m.reply("File name not found; please contact @yashoswalyo.")
            return
        
        markup = bMaker.makebuttons(
            set1=["Audio", "Subtitle", "Cancel"],
            set2=[f"extract_audio_{rmess.id}", f"extract_subtitle_{rmess.id}", 'cancel'],
            isCallback=True,
            rows=2,
        )
        await m.reply(
            text="Choose from below what you want to extract?",
            quote=True,
            reply_markup=InlineKeyboardMarkup(markup),
        )


@mergeApp.on_message(filters.command(["help"]) & filters.private)
async def help_msg(c: Client, m: Message):
    await m.reply_text(
        text="""**Follow These Steps:

1) Send me a custom thumbnail (optional).
2) Send two or more videos you want to merge.
3) After sending all files, select merge options.
4) Select the upload mode.
5) Choose rename if you want to give a custom file name, otherwise press default.**""",
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close 🔐", callback_data="close")]]
        ),
    )


@mergeApp.on_message(filters.command(["about"]) & filters.private)
async def about_handler(c: Client, m: Message):
    await m.reply_text(
        text="""
aa
        """,
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("👨‍💻Developer👨‍💻", url="https://t.me/yashoswalyo")],
                [
                    InlineKeyboardButton(
                        "🏘Source Code🏘", url="https://github.com/yashoswalyo/MERGE-BOT"
                    ),
                    InlineKeyboardButton(
                        "🤔Deployed By🤔", url=f"https://t.me/{Config.OWNER_USERNAME}"
                    ),
                ],
                [InlineKeyboardButton("Close 🔐", callback_data="close")],
            ]
        ),
    )


@mergeApp.on_message(
    filters.command(["savethumb", "setthumb", "savethumbnail"]) & filters.private
)
async def save_thumbnail(c: Client, m: Message):
    if not m.reply_to_message or not m.reply_to_message.photo:
        await m.reply(text="Please reply to a valid photo")
        return

    await photo_handler(c, m.reply_to_message)


@mergeApp.on_message(filters.command(["showthumbnail"]) & filters.private)
async def show_thumbnail(c: Client, m: Message):
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    thumb_id = user.thumbnail
    location = f"downloads/{m.from_user.id}_thumb.jpg"

    try:
        if os.path.exists(location):
            await m.reply_photo(photo=location, caption="🖼️ Your custom thumbnail", quote=True)
        elif thumb_id:
            await c.download_media(message=thumb_id, file_name=location)
            await m.reply_photo(photo=location, caption="🖼️ Your custom thumbnail", quote=True)
        else:
            await m.reply_text(text="❌ Custom thumbnail not found", quote=True)
    except Exception as err:
        LOGGER.info(err)
        await m.reply_text(text="❌ Custom thumbnail not found", quote=True)


@mergeApp.on_message(filters.command(["deletethumbnail"]) & filters.private)
async def delete_thumbnail(c: Client, m: Message):
    user = UserSettings(m.from_user.id, m.from_user.first_name)
    user.thumbnail = None
    user.set()
    location = f"downloads/{m.from_user.id}_thumb.jpg"

    if os.path.exists(location):
        os.remove(location)
        await m.reply_text("✅ Deleted Successfully", quote=True)
    else:
        await m.reply_text(text="❌ Custom thumbnail not found", quote=True)


@mergeApp.on_message(filters.command(["ban", "unban"]) & filters.private)
async def ban_user(c: Client, m: Message):
    if m.from_user.id != int(Config.OWNER):
        await m.reply_text("**(Only for __OWNER__)\nCommand:**\n  `/ban <user_id>` or `/unban <user_id>`", quote=True)
        return

    command, user_id_str = m.text.split(' ', 1)
    try:
        user_id = int(user_id_str)
        if user_id == int(Config.OWNER):
            await m.reply_text("I can't ban/unban you, master.", quote=True)
            return

        user_obj = await c.get_users(user_id)
        udata = UserSettings(uid=user_id, name=user_obj.first_name)
        is_ban_command = command == "/ban"
        udata.banned = is_ban_command
        udata.allowed = not is_ban_command
        udata.set()

        status = "BANNED" if is_ban_command else "UNBANNED"
        await m.reply_text(f"Pooof, {user_obj.first_name} has been **{status}**", quote=True)

        message = (
            f"Dear {user_obj.first_name},\nYour account has been {'banned' if is_ban_command else 'unbanned'}. "
            f"Contact @{Config.OWNER_USERNAME} for more details."
        )
        await c.send_message(chat_id=user_id, text=message)
    except Exception as e:
        LOGGER.error(e)
        await m.reply_text(f"An error occurred: {str(e)}", quote=True)


async def showQueue(c: Client, cb: CallbackQuery):
    try:
        markup = await makeButtons(c, cb.message, queueDB)
        await cb.message.edit(
            text="Okay,\nNow Send Me Next Video or Press **Merge Now** Button!",
            reply_markup=InlineKeyboardMarkup(markup),
        )
    except ValueError:
        await cb.message.edit("Send some more videos")


async def delete_all(root):
    try:
        shutil.rmtree(root)
    except Exception as e:
        LOGGER.info(e)


async def makeButtons(bot: Client, m: Message, db: dict):
    user = UserSettings(m.chat.id, m.chat.first_name)
    markup = []

    items = []
    if user.merge_mode == 1:
        items = await bot.get_messages(chat_id=m.chat.id, message_ids=db.get(m.chat.id)["videos"])
    elif user.merge_mode in [2, 3]:
        items = await bot.get_messages(chat_id=m.chat.id, message_ids=db.get(m.chat.id).get("audios" if user.merge_mode == 2 else "subtitles"))
        items.insert(0, await bot.get_messages(chat_id=m.chat.id, message_ids=db.get(m.chat.id)["videos"][0]))

    for i in items:
        media = i.video or i.document or i.audio
        if media:
            markup.append([InlineKeyboardButton(media.file_name, callback_data=f"tryotherbutton")])

    markup.append([InlineKeyboardButton("🔗 Merge Now", callback_data="merge")])
    markup.append([InlineKeyboardButton("💥 Clear Files", callback_data="cancel")])
    return markup


LOGCHANNEL = Config.LOGCHANNEL
try:
    if not Config.USER_SESSION_STRING:
        raise KeyError("User session string not provided")

    LOGGER.info("Starting USER Session")
    userBot = Client(
        name="merge-bot-user",
        session_string=Config.USER_SESSION_STRING,
        no_updates=True,
    )
except KeyError as e:
    userBot = None
    LOGGER.warning("No User Session, Default Bot session will be used")

if __name__ == "__main__":
    try:
        with userBot:
            userBot.send_message(
                chat_id=int(LOGCHANNEL),
                text="Bot booted with Premium Account,\n\n  Thanks for using <a href='https://github.com/yashoswalyo/merge-bot'>this repo</a>",
                disable_web_page_preview=True,
            )
            user = userBot.get_me()
            Config.IS_PREMIUM = user.is_premium
    except Exception as err:
        LOGGER.error(f"{err}")
        Config.IS_PREMIUM = False

    mergeApp.run()

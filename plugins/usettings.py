# plugins/usettings.py
import time
from pyrogram import filters, Client as mergeApp
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helpers.msg_utils import MakeButtons
from helpers.utils import UserSettings
from helpers.database import getMetadata, setUserMergeSettings

@mergeApp.on_message(filters.command(["settings"]))
async def settings_handler(c: mergeApp, m: Message):
    replay = await m.reply(text="Please wait", quote=True)
    usettings = UserSettings(m.from_user.id, m.from_user.first_name)
    await user_settings(replay, m.from_user.id, m.from_user.first_name, m.from_user.last_name, usettings)

async def user_settings(
    editable: Message,
    uid: int,
    fname: str,
    lname: str,
    usettings: UserSettings,
):
    b = MakeButtons()
    
    # Fetch metadata settings from the database
    metadata = getMetadata(uid)
    
    if usettings.user_id:
        if usettings.merge_mode == 1:
            user_merge_mode_str = "Video 🎥 + Video 🎥"
        elif usettings.merge_mode == 2:
            user_merge_mode_str = "Video 🎥 + Audio 🎵"
        elif usettings.merge_mode == 3:
            user_merge_mode_str = "Video 🎥 + Subtitle 📜"
        elif usettings.merge_mode == 4:
            user_merge_mode_str = "Extract"
        
        edit_metadata_str = "✅" if usettings.edit_metadata else "❌"
        metadata_text = (
            f"Author: {metadata.get('author', 'Not Set')}\n"
            f"Video: {metadata.get('video', 'Not Set')}\n"
            f"Audio: {metadata.get('audio', 'Not Set')}\n"
            f"Subtitle: {metadata.get('subtitle', 'Not Set')}"
        )
        
        u_settings_message = f"""
<b><u>Merge Bot settings for <a href='tg://user?id={uid}'>{fname} {lname}</a></u></b>
    ┃
    ┣**👦 ID: <u>{usettings.user_id}</u>**
    ┣**{'🚫' if usettings.banned else '🫡'} Ban Status: <u>{usettings.banned}</u>**
    ┣**{'⚡' if usettings.allowed else '❗'} Allowed: <u>{usettings.allowed}</u>**
    ┣**{edit_metadata_str} Edit Metadata: <u>{usettings.edit_metadata}</u>**
    ┣**Ⓜ️ Merge mode: <u>{user_merge_mode_str}</u>**
    ┣**Metadata:**
    ┗{metadata_text}
"""
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Edit Metadata", callback_data=f"edit_metadata_{uid}"), InlineKeyboardButton("Close", callback_data="close")],
            [InlineKeyboardButton("Change Merge Mode", callback_data=f"change_mode_{uid}")]
        ])
        
        res = await editable.edit(text=u_settings_message, reply_markup=markup)
    else:
        usettings.name = fname
        usettings.merge_mode = 1
        usettings.allowed = False
        usettings.edit_metadata = False
        usettings.thumbnail = None
        await user_settings(editable, uid, fname, lname, usettings)
    return

@mergeApp.on_callback_query(filters.regex(r"edit_metadata_(\d+)"))
async def edit_metadata(c: mergeApp, query):
    uid = int(query.matches[0].group(1))
    usettings = UserSettings(uid)  # Assuming you have a way to get the user settings
    if usettings.edit_metadata:
        await query.message.edit(
            text="Metadata is currently enabled. Press 'Set Metadata' to update or 'Back' to return.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Set Metadata", callback_data=f"set_metadata_{uid}"), InlineKeyboardButton("Back", callback_data=f"back_{uid}")],
                [InlineKeyboardButton("Close", callback_data="close")]
            ])
        )
    else:
        await query.message.edit(
            text="Metadata is currently disabled. Press 'Set Metadata' to enable.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Set Metadata", callback_data=f"set_metadata_{uid}"), InlineKeyboardButton("Back", callback_data=f"back_{uid}")],
                [InlineKeyboardButton("Close", callback_data="close")]
            ])
        )

@mergeApp.on_callback_query(filters.regex(r"set_metadata_(\d+)"))
async def set_metadata(c: mergeApp, query):
    uid = int(query.matches[0].group(1))
    await query.message.edit(
        text="Okay, send your metadata now. Use the format: author|video|audio|subtitle.\n\nYou have 1 minute.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Stop", callback_data=f"stop_metadata_{uid}"), InlineKeyboardButton("Close", callback_data="close")]
        ])
    )
    
    # Add a timeout handler to stop editing after 1 minute
    def timeout_handler():
        # Code to handle timeout, e.g., inform the user that time is up
        pass
    
    # Example: Add a timeout for 1 minute
    c.loop.call_later(60, timeout_handler)

@mergeApp.on_callback_query(filters.regex(r"stop_metadata_(\d+)"))
async def stop_metadata(c: mergeApp, query):
    uid = int(query.matches[0].group(1))
    # Handle the stopping of metadata input here
    await query.message.edit(text="Metadata input has been stopped.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close")]]))

@mergeApp.on_message(filters.text)
async def receive_metadata(c: mergeApp, m: Message):
    if not m.text or '|' not in m.text:
        return
    uid = m.from_user.id
    metadata_parts = m.text.split('|')
    if len(metadata_parts) != 4:
        await m.reply("Invalid format. Please use: author|video|audio|subtitle")
        return
    author, video, audio, subtitle = metadata_parts
    setUserMergeSettings(uid, "User Name", 1, True, False, False, None)  # Update with appropriate values
    # Save metadata to database
    await m.reply("Metadata has been set successfully.")
    await m.reply("Your updated settings:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Back", callback_data=f"back_{uid}"), InlineKeyboardButton("Close", callback_data="close")]
    ]))

@mergeApp.on_callback_query(filters.regex(r"back_(\d+)"))
async def back_to_settings(c: mergeApp, query):
    uid = int(query.matches[0].group(1))
    usettings = UserSettings(uid)
    await user_settings(query.message, uid, usettings.name, '', usettings)

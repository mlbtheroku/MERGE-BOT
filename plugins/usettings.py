# plugins/usettings.py
import time
from pyrogram import filters, Client as mergeApp
from pyrogram.types import Message, InlineKeyboardMarkup
from helpers.msg_utils import MakeButtons
from helpers.utils import UserSettings


@mergeApp.on_message(filters.command(["settings"]))
async def f1(c: mergeApp, m: Message):
    # setUserMergeMode(uid=m.from_user.id,mode=1)
    replay = await m.reply(text="Please wait", quote=True)
    usettings = UserSettings(m.from_user.id, m.from_user.first_name)
    await userSettings(
        replay, m.from_user.id, m.from_user.first_name, m.from_user.last_name, usettings
    )


async def userSettings(
    editable: Message,
    uid: int,
    fname,
    lname,
    usettings: UserSettings,
):
    b = MakeButtons()
    if usettings.user_id:
        if usettings.merge_mode == 1:
            userMergeModeId = 1
            userMergeModeStr = "Video 🎥 + Video 🎥"
        elif usettings.merge_mode == 2:
            userMergeModeId = 2
            userMergeModeStr = "Video 🎥 + Audio 🎵"
        elif usettings.merge_mode == 3:
            userMergeModeId = 3
            userMergeModeStr = "Video 🎥 + Subtitle 📜"
        elif usettings.merge_mode == 4:
            userMergeModeId = 4
            userMergeModeStr = "Extract"
        
        editMetadataStr = "✅" if usettings.edit_metadata else "❌"
        metadata_display = "Metadata is currently disabled" if not usettings.edit_metadata else f"""
<b><u>Current Metadata for <a href='tg://user?id={uid}'>{fname} {lname}</a></u></b>
    ┃
    ┣**Author: <u>{usettings.author or "Not Set"}</u>**
    ┣**Video: <u>{usettings.video or "Not Set"}</u>**
    ┣**Audio: <u>{usettings.audio or "Not Set"}</u>**
    ┗**Subtitle: <u>{usettings.subtitle or "Not Set"}</u>**
"""

        uSettingsMessage = f"""
<b><u>Merge Bot settings for <a href='tg://user?id={uid}'>{fname} {lname}</a></u></b>
    ┃
    ┣**👦 ID: <u>{usettings.user_id}</u>**
    ┣**{'🚫' if usettings.banned else '🫡'} Ban Status: <u>{usettings.banned}</u>**
    ┣**{'⚡' if usettings.allowed else '❗'} Allowed: <u>{usettings.allowed}</u>**
    ┣**{'✅' if usettings.edit_metadata else '❌'} Edit Metadata: <u>{usettings.edit_metadata}</u>**
    ┗**Ⓜ️ Merge mode: <u>{userMergeModeStr}</u>**
"""
        if not usettings.edit_metadata:
            markup = b.makebuttons(
                ["Set Metadata", "Back", "Close"],
                [f"setMetadata_{uid}", "back", "close"],
                rows=1
            )
            res = await editable.edit(
                text=f"{metadata_display}\n{uSettingsMessage}",
                reply_markup=InlineKeyboardMarkup(markup)
            )
        else:
            markup = b.makebuttons(
                ["Edit", "Delete", "Back", "Close"],
                [f"editMetadata_{uid}", f"deleteMetadata_{uid}", "back", "close"],
                rows=2
            )
            res = await editable.edit(
                text=f"{metadata_display}\n{uSettingsMessage}",
                reply_markup=InlineKeyboardMarkup(markup)
            )
    else:
        usettings.name = fname
        usettings.merge_mode = 1
        usettings.allowed = False
        usettings.edit_metadata = False
        usettings.thumbnail = None
        await userSettings(editable, uid, fname, lname, usettings)
    return

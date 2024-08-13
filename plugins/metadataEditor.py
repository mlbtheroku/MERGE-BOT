# plugins/metadataEditor.py
from pyrogram import Client
from pyrogram.types import Message
from bot import mergeApp, LOGGER
from helpers.database import enableMetadataToggle, disableMetadataToggle, getUserMergeSettings
from config import Config

async def metaEditor(c: Client, m: Message):
    uid = m.from_user.id
    user_settings = await getUserMergeSettings(uid)
    
    if not user_settings:
        await m.reply_text("Your settings could not be found.")
        return

    command = m.text.split(maxsplit=1)[1].strip().lower() if len(m.text.split(maxsplit=1)) > 1 else ""

    if command == "enable":
        try:
            await enableMetadataToggle(uid)
            await m.reply_text("Metadata editing has been enabled.")
        except Exception as e:
            LOGGER.error(f"Error enabling metadata toggle for user {uid}: {e}")
            await m.reply_text("Failed to enable metadata editing.")
    elif command == "disable":
        try:
            await disableMetadataToggle(uid)
            await m.reply_text("Metadata editing has been disabled.")
        except Exception as e:
            LOGGER.error(f"Error disabling metadata toggle for user {uid}: {e}")
            await m.reply_text("Failed to disable metadata editing.")
    else:
        await m.reply_text("Invalid command. Use 'enable' or 'disable' to toggle metadata editing.")

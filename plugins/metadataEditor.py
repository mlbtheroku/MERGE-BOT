# plugins/metadataEditor.py
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from helpers.database import getUserMergeSettings, setUserMergeSettings, enableMetadataToggle, disableMetadataToggle
from config import Config

def get_metadata_keyboard(is_set: bool):
    status_emoji = "✅" if is_set else "❌"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{status_emoji} Metadata", callback_data="metadata_status")],
        [InlineKeyboardButton("Back", callback_data="back")]
    ])

def get_metadata_action_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Set Metadata", callback_data="set_metadata")],
        [InlineKeyboardButton("Back", callback_data="back"), InlineKeyboardButton("Close", callback_data="close")]
    ])

def get_metadata_details_keyboard(metadata):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Edit", callback_data="edit_metadata")],
        [InlineKeyboardButton("Delete", callback_data="delete_metadata")],
        [InlineKeyboardButton("Back", callback_data="back"), InlineKeyboardButton("Close", callback_data="close")]
    ])

def get_edit_metadata_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Stop Edit", callback_data="stop_edit")],
        [InlineKeyboardButton("Back", callback_data="back"), InlineKeyboardButton("Close", callback_data="close")]
    ])

@mergeApp.on_callback_query(filters.regex("metadata_status"))
async def handle_metadata_status(c: Client, cb: CallbackQuery):
    uid = cb.from_user.id
    user_settings = getUserMergeSettings(uid)
    is_set = user_settings and user_settings["user_settings"].get("edit_metadata", False)
    metadata = user_settings.get("user_settings", {}).get("metadata", {})
    await cb.message.edit(
        text=f"Your Current Metadata:\n"
             f"Author -> {metadata.get('author', 'Not Set')}\n"
             f"Video -> {metadata.get('video', 'Not Set')}\n"
             f"Audio -> {metadata.get('audio', 'Not Set')}\n"
             f"Subtitle -> {metadata.get('subtitle', 'Not Set')}",
        reply_markup=get_metadata_details_keyboard(metadata)
    )

@mergeApp.on_callback_query(filters.regex("set_metadata"))
async def handle_set_metadata(c: Client, cb: CallbackQuery):
    uid = cb.from_user.id
    enableMetadataToggle(uid, True)
    await cb.message.edit(
        text="Okay, Send Your Metadata Now, You Can Add Your Name Or Channel Name As Metadata.\n\n"
             "This Metadata Will Be Added On All Files (Beta Feature)\n\n"
             "Format:\n\n"
             "author|video|audio|subtitle\n\n"
             "Time Out = 1 Minute",
        reply_markup=get_edit_metadata_keyboard()
    )
    # Store user state or session for metadata entry

@mergeApp.on_message(filters.text)
async def handle_metadata_input(c: Client, m: Message):
    uid = m.from_user.id
    metadata_input = m.text.strip()
    parts = metadata_input.split('|')
    if len(parts) != 4:
        await m.reply_text("Invalid format. Please use: author|video|audio|subtitle")
        return

    author, video, audio, subtitle = parts
    await setUserMergeSettings(uid, name=None, mode=None, edit_metadata=True, banned=None, allowed=None, thumbnail=None)
    Database.mergebot.mergeSettings.update_one(
        {"_id": uid},
        {"$set": {"user_settings.metadata": {"author": author, "video": video, "audio": audio, "subtitle": subtitle}}}
    )
    
    await m.reply_text("Metadata has been updated.")
    # Update button status here

@mergeApp.on_callback_query(filters.regex("edit_metadata"))
async def handle_edit_metadata(c: Client, cb: CallbackQuery):
    await cb.message.edit(
        text="Send new metadata in the format:\n\n"
             "author|video|audio|subtitle",
        reply_markup=get_edit_metadata_keyboard()
    )
    # Store user state or session for metadata editing

@mergeApp.on_callback_query(filters.regex("delete_metadata"))
async def handle_delete_metadata(c: Client, cb: CallbackQuery):
    uid = cb.from_user.id
    await Database.mergebot.mergeSettings.update_one(
        {"_id": uid},
        {"$set": {"user_settings.metadata": {}}}
    )
    
    await cb.message.edit(
        text="Metadata has been deleted.",
        reply_markup=get_metadata_action_keyboard()
    )

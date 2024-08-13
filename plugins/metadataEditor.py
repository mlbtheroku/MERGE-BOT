# plugins/metadataEditor.py
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from helpers.database import (
    getUserMergeSettings, setUserMergeSettings, 
    enableMetadataToggle, disableMetadataToggle, 
    setMetadata, getMetadata
)
from config import Config

# Function to get the keyboard for showing metadata status
def get_metadata_status_keyboard(is_enabled: bool):
    status_emoji = "✅" if is_enabled else "❌"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{status_emoji} Metadata", callback_data="metadata_status")],
        [InlineKeyboardButton("Set Metadata", callback_data="set_metadata")],
        [InlineKeyboardButton("Back", callback_data="back"), InlineKeyboardButton("Close", callback_data="close")]
    ])

# Function to get the keyboard for setting metadata
def get_set_metadata_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Stop Edit", callback_data="stop_edit")],
        [InlineKeyboardButton("Back", callback_data="back"), InlineKeyboardButton("Close", callback_data="close")]
    ])

# Function to get the keyboard for metadata details
def get_metadata_details_keyboard(metadata):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Author -> {metadata.get('author', 'Not Set')}", callback_data="edit_metadata_author")],
        [InlineKeyboardButton(f"Video -> {metadata.get('video', 'Not Set')}", callback_data="edit_metadata_video")],
        [InlineKeyboardButton(f"Audio -> {metadata.get('audio', 'Not Set')}", callback_data="edit_metadata_audio")],
        [InlineKeyboardButton(f"Subtitle -> {metadata.get('subtitle', 'Not Set')}", callback_data="edit_metadata_subtitle")],
        [InlineKeyboardButton("Edit", callback_data="edit_metadata")],
        [InlineKeyboardButton("Delete", callback_data="delete_metadata")],
        [InlineKeyboardButton("Back", callback_data="back"), InlineKeyboardButton("Close", callback_data="close")]
    ])

# Function to show the current metadata status
@Client.on_callback_query(filters.regex("metadata_status"))
async def handle_metadata_status(c: Client, cb: CallbackQuery):
    uid = cb.from_user.id
    user_settings = getUserMergeSettings(uid)
    is_enabled = user_settings and user_settings["user_settings"].get("edit_metadata", False)
    metadata = getMetadata(uid)
    await cb.message.edit(
        text="Your Current Metadata:\n"
             f"Author -> {metadata.get('author', 'Not Set')}\n"
             f"Video -> {metadata.get('video', 'Not Set')}\n"
             f"Audio -> {metadata.get('audio', 'Not Set')}\n"
             f"Subtitle -> {metadata.get('subtitle', 'Not Set')}",
        reply_markup=get_metadata_status_keyboard(is_enabled)
    )

# Function to handle setting metadata
@Client.on_callback_query(filters.regex("set_metadata"))
async def handle_set_metadata(c: Client, cb: CallbackQuery):
    uid = cb.from_user.id
    enableMetadataToggle(uid)
    await cb.message.edit(
        text="Okay, Send Your Metadata Now. You Can Add Your Name Or Channel Name As Metadata.\n\n"
             "This Metadata Will Be Added On All Files (Beta Feature)\n\n"
             "Format:\n\n"
             "author|video|audio|subtitle\n\n"
             "Time Out = 1 Minute",
        reply_markup=get_set_metadata_keyboard()
    )

# Function to handle the input of metadata
@Client.on_message(filters.text)
async def handle_metadata_input(c: Client, m: Message):
    uid = m.from_user.id
    metadata_input = m.text.strip()
    parts = metadata_input.split('|')
    if len(parts) != 4:
        await m.reply_text("Invalid format. Please use: author|video|audio|subtitle")
        return

    author, video, audio, subtitle = parts
    setMetadata(uid, author, video, audio, subtitle)
    setUserMergeSettings(uid, name=None, mode=None, edit_metadata=True, banned=False, allowed=True, thumbnail=None)

    disableMetadataToggle(uid)
    await m.reply_text("Metadata has been set successfully.")
    await m.reply_text(
        "Your Current Metadata:\n"
        f"Author -> {author}\n"
        f"Video -> {video}\n"
        f"Audio -> {audio}\n"
        f"Subtitle -> {subtitle}",
        reply_markup=get_metadata_status_keyboard(True)
    )

# Function to handle editing metadata
@Client.on_callback_query(filters.regex("edit_metadata"))
async def handle_edit_metadata(c: Client, cb: CallbackQuery):
    uid = cb.from_user.id
    metadata = getMetadata(uid)
    await cb.message.edit(
        text="Your Current Metadata:\n"
             f"Author -> {metadata.get('author', 'Not Set')}\n"
             f"Video -> {metadata.get('video', 'Not Set')}\n"
             f"Audio -> {metadata.get('audio', 'Not Set')}\n"
             f"Subtitle -> {metadata.get('subtitle', 'Not Set')}",
        reply_markup=get_metadata_details_keyboard(metadata)
    )

# Handle the different metadata edit options
@Client.on_callback_query(filters.regex("edit_metadata_author"))
async def handle_edit_metadata_author(c: Client, cb: CallbackQuery):
    # Additional logic for editing author metadata
    pass

@Client.on_callback_query(filters.regex("edit_metadata_video"))
async def handle_edit_metadata_video(c: Client, cb: CallbackQuery):
    # Additional logic for editing video metadata
    pass

@Client.on_callback_query(filters.regex("edit_metadata_audio"))
async def handle_edit_metadata_audio(c: Client, cb: CallbackQuery):
    # Additional logic for editing audio metadata
    pass

@Client.on_callback_query(filters.regex("edit_metadata_subtitle"))
async def handle_edit_metadata_subtitle(c: Client, cb: CallbackQuery):
    # Additional logic for editing subtitle metadata
    pass

# Function to handle deleting metadata
@Client.on_callback_query(filters.regex("delete_metadata"))
async def handle_delete_metadata(c: Client, cb: CallbackQuery):
    uid = cb.from_user.id
    setMetadata(uid, author="", video="", audio="", subtitle="")
    await cb.message.edit(
        text="Metadata has been deleted.",
        reply_markup=get_metadata_status_keyboard(False)
    )

# Function to handle stopping metadata editing
@Client.on_callback_query(filters.regex("stop_edit"))
async def handle_stop_edit(c: Client, cb: CallbackQuery):
    await cb.message.edit(
        text="Editing stopped.",
        reply_markup=get_metadata_status_keyboard(True)
    )

# Function to handle going back
@Client.on_callback_query(filters.regex("back"))
async def handle_back(c: Client, cb: CallbackQuery):
    uid = cb.from_user.id
    user_settings = getUserMergeSettings(uid)
    is_set = user_settings and user_settings["user_settings"].get("edit_metadata", False)
    await cb.message.edit(
        text="Select an action:",
        reply_markup=get_metadata_status_keyboard(is_set)
    )

# Function to handle closing the message
@Client.on_callback_query(filters.regex("close"))
async def handle_close(c: Client, cb: CallbackQuery):
    await cb.message.delete()

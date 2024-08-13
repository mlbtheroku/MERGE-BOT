# helpers/database.py
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from pyrogram.types import CallbackQuery
from config import Config
from __init__ import LOGGER, MERGE_MODE

class Database(object):
    client = MongoClient(Config.DATABASE_URL)
    mergebot = client.MergeBot

async def addUser(uid, fname, lname):
    try:
        userDetails = {
            "_id": uid,
            "name": f"{fname} {lname}",
        }
        Database.mergebot.users.insert_one(userDetails)
        LOGGER.info(f"New user added id={uid}\n{fname} {lname} \n")
    except DuplicateKeyError:
        LOGGER.info(f"Duplicate Entry Found for id={uid}\n{fname} {lname} \n")
    return

async def broadcast():
    a = Database.mergebot.mergeSettings.find({})
    return a

async def allowUser(uid, fname, lname):
    try:
        Database.mergebot.allowedUsers.insert_one(
            {
                "_id": uid,
            }
        )
    except DuplicateKeyError:
        LOGGER.info(f"Duplicate Entry Found for id={uid}\n{fname} {lname} \n")
    return

async def allowedUser(uid):
    a = Database.mergebot.allowedUsers.find_one({"_id": uid})
    try:
        if uid == a["_id"]:
            return True
    except TypeError:
        return False

async def saveThumb(uid, fid):
    try:
        Database.mergebot.thumbnail.insert_one({"_id": uid, "thumbid": fid})
    except DuplicateKeyError:
        Database.mergebot.thumbnail.replace_one({"_id": uid}, {"thumbid": fid})

async def delThumb(uid):
    Database.mergebot.thumbnail.delete_many({"_id": uid})
    return True

async def getThumb(uid):
    res = Database.mergebot.thumbnail.find_one({"_id": uid})
    return res["thumbid"]

async def deleteUser(uid):
    Database.mergebot.mergeSettings.delete_many({"_id": uid})

async def addUserRcloneConfig(cb: CallbackQuery, fileId):
    try:
        await cb.message.edit("Adding file to DB")
        uid = cb.from_user.id
        Database.mergebot.rcloneData.insert_one({"_id": uid, "rcloneFileId": fileId})
    except Exception as err:
        LOGGER.info("Updating rclone")
        await cb.message.edit("Updating file in DB")
        uid = cb.from_user.id
        Database.mergebot.rcloneData.replace_one({"_id": uid}, {"rcloneFileId": fileId})
    await cb.message.edit("Done")
    return

async def getUserRcloneConfig(uid):
    try:
        res = Database.mergebot.rcloneData.find_one({"_id": uid})
        return res["rcloneFileId"]
    except Exception as err:
        return None

def getUserMergeSettings(uid: int):
    try:
        res_cur = Database.mergebot.mergeSettings.find_one({"_id": uid})
        return res_cur
    except Exception as e:
        LOGGER.info(e)
        return None

def setUserMergeSettings(uid: int, name: str, mode, edit_metadata, banned, allowed, thumbnail):
    modes = Config.MODES
    if uid:
        try:
            Database.mergebot.mergeSettings.insert_one(
                document={
                    "_id": uid,
                    "name": name,
                    "user_settings": {
                        "merge_mode": mode,
                        "edit_metadata": edit_metadata,
                        "metadata": {}
                    },
                    "isAllowed": allowed,
                    "isBanned": banned,
                    "thumbnail": thumbnail,
                }
            )
            LOGGER.info("User {} Mode updated to {}".format(uid, modes[mode - 1]))
        except Exception:
            Database.mergebot.mergeSettings.replace_one(
                filter={"_id": uid},
                replacement={
                    "name": name,
                    "user_settings": {
                        "merge_mode": mode,
                        "edit_metadata": edit_metadata,
                        "metadata": {}
                    },
                    "isAllowed": allowed,
                    "isBanned": banned,
                    "thumbnail": thumbnail,
                },
            )
            LOGGER.info("User {} Mode updated to {}".format(uid, modes[mode - 1]))
        MERGE_MODE[uid] = mode
    LOGGER.info(MERGE_MODE)

def enableMetadataToggle(uid: int):
    Database.mergebot.mergeSettings.update_one(
        {"_id": uid},
        {"$set": {"user_settings.edit_metadata": True}}
    )

def disableMetadataToggle(uid: int):
    Database.mergebot.mergeSettings.update_one(
        {"_id": uid},
        {"$set": {"user_settings.edit_metadata": False}}
    )

def setMetadata(uid: int, author: str, video: str, audio: str, subtitle: str):
    Database.mergebot.mergeSettings.update_one(
        {"_id": uid},
        {"$set": {"user_settings.metadata": {"author": author, "video": video, "audio": audio, "subtitle": subtitle}}}
    )

def getMetadata(uid: int):
    user = Database.mergebot.mergeSettings.find_one({"_id": uid})
    if user and "user_settings" in user and "metadata" in user["user_settings"]:
        return user["user_settings"]["metadata"]
    return {}

# helpers/ffmpeg_helper.py
import asyncio
import subprocess
import shutil
import os
import time
import ffmpeg
from pyrogram.types import CallbackQuery
from config import Config
from pyrogram.types import Message
from __init__ import LOGGER
from helpers.utils import get_path_size

async def MergeVideo(input_file: str, user_id: int, message: Message, format_: str):
    """
    This is for Merging Videos Together!
    :param `input_file`: input.txt file's location.
    :param `user_id`: Pass user_id as integer.
    :param `message`: Pass Editable Message for Showing FFmpeg Progress.
    :param `format_`: Pass File Extension.
    :return: This will return Merged Video File Path
    """
    output_vid = f"downloads/{str(user_id)}/[@yashoswalyo].{format_.lower()}"
    file_generator_command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        input_file,
        "-map",
        "0",
        "-c",
        "copy",
        output_vid,
    ]
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            *file_generator_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except NotImplementedError:
        await message.edit(
            text="Unable to Execute FFmpeg Command! Got `NotImplementedError` ...\n\nPlease run bot in a Linux/Unix Environment."
        )
        await asyncio.sleep(10)
        return None
    await message.edit("Merging Video Now ...\n\nPlease Keep Patience ...")
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    LOGGER.info(e_response)
    LOGGER.info(t_response)
    if os.path.lexists(output_vid):
        return output_vid
    else:
        return None

async def MergeSub(filePath: str, subPath: str, user_id: int, edit_metadata: bool):
    """
    This is for Merging Video + Subtitle Together.

    Parameters:
    - `filePath`: Path to Video file.
    - `subPath`: Path to subtitle file.
    - `user_id`: To get parent directory.
    - `edit_metadata`: Flag to determine if metadata should be updated.

    returns: Merged Video File Path
    """
    LOGGER.info("Generating mux command")
    muxcmd = ["ffmpeg", "-hide_banner", "-i", filePath, "-i", subPath]
    
    if edit_metadata:
        muxcmd += ["-metadata:s:s:0", f"title=Subtitle Track - tg@yashoswalyo"]

    muxcmd += [
        "-map", "0:v:0",
        "-map", "0:a:?",
        "-map", "0:s:?",
        "-map", "1:s",
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "srt",
        f"./downloads/{str(user_id)}/[@yashoswalyo]_softmuxed_video.mkv"
    ]
    
    LOGGER.info("Muxing subtitles")
    subprocess.call(muxcmd)
    orgFilePath = shutil.move(
        f"downloads/{str(user_id)}/[@yashoswalyo]_softmuxed_video.mkv", filePath
    )
    return orgFilePath

def MergeSubNew(filePath: str, subPath: str, user_id: int, file_list: list, edit_metadata: bool):
    """
    This method is for Merging Video + Subtitle(s) Together.

    Parameters:
    - `filePath`: Path to Video file.
    - `subPath`: Path to subtitle file.
    - `user_id`: To get parent directory.
    - `file_list`: List of all input files
    - `edit_metadata`: Flag to determine if metadata should be updated.

    returns: Merged Video File Path
    """
    LOGGER.info("Generating mux command")
    muxcmd = ["ffmpeg", "-hide_banner"]
    
    for i in file_list:
        muxcmd += ["-i", i]
    
    muxcmd += [
        "-map", "0:v:0",
        "-map", "0:a:?",
        "-map", "0:s:?"
    ]
    
    for j in range(1, len(file_list)):
        muxcmd += [
            "-map", f"{j}:s",
            "-metadata:s:s:{j}", f"title=Track {j+1} - tg@yashoswalyo"
        ]
    
    if edit_metadata:
        muxcmd += ["-metadata:s:s:0", f"title=Subtitle Track - tg@yashoswalyo"]

    muxcmd += [
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "srt",
        f"./downloads/{str(user_id)}/[@yashoswalyo]_softmuxed_video.mkv"
    ]
    
    LOGGER.info("Sub muxing")
    subprocess.call(muxcmd)
    return f"downloads/{str(user_id)}/[@yashoswalyo]_softmuxed_video.mkv"

def MergeAudio(videoPath: str, files_list: list, user_id: int, edit_metadata: bool):
    """
    This method is for Merging Audio Tracks with Video.

    Parameters:
    - `videoPath`: Path to Video file.
    - `files_list`: List of audio files.
    - `user_id`: To get parent directory.
    - `edit_metadata`: Flag to determine if metadata should be updated.

    returns: Merged Video File Path
    """
    LOGGER.info("Generating Mux Command")
    muxcmd = ["ffmpeg", "-hide_banner", "-i", videoPath]
    
    audioTracks = 0
    for i in files_list:
        muxcmd += ["-i", i]

    muxcmd += [
        "-map", "0:v:0",
        "-map", "0:a:?"
    ]
    
    for i in range(1, len(files_list)):
        muxcmd += [
            "-map", f"{i}:a",
            "-metadata:s:a:{audioTracks}", f"title=Track {audioTracks+1} - tg@yashoswalyo"
        ]
        audioTracks += 1

    if edit_metadata:
        muxcmd += ["-metadata:s:a:0", f"title=Audio Track - tg@yashoswalyo"]

    muxcmd += [
        "-map", "0:s:?",
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "copy",
        f"downloads/{str(user_id)}/[@yashoswalyo]_export.mkv"
    ]
    
    LOGGER.info(muxcmd)
    process = subprocess.call(muxcmd)
    LOGGER.info(process)
    return f"downloads/{str(user_id)}/[@yashoswalyo]_export.mkv"

async def cult_small_video(video_file, output_directory, start_time, end_time, format_):
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = (
        output_directory + str(round(time.time())) + "." + format_.lower()
    )
    file_generator_command = [
        "ffmpeg",
        "-ss", str(start_time),
        "-to", str(end_time),
        "-i", video_file,
        "-async", "1",
        "-strict", "-2",
        out_put_file_name,
    ]
    process = await asyncio.create_subprocess_exec(
        *file_generator_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    LOGGER.info(e_response)
    LOGGER.info(t_response)
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None

async def take_screen_shot(video_file, output_directory, ttl):
    """
    This functions generates custom_thumbnail / Screenshot.

    Parameters:
    - `video_file`: Path to video file.
    - `output_directory`: Path where to save thumbnail
    - `ttl`: Timestamp to generate ss

    returns: This will return path of screenshot
    """
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = os.path.join(output_directory, str(time.time()) + ".jpg")
    if video_file.upper().endswith(
        (
            "MKV", "MP4", "WEBM", "AVI", "MOV", "OGG", "WMV",
            "M4V", "TS", "MPG", "MTS", "M2TS", "3GP"
        )
    ):
        file_genertor_command = [
            "ffmpeg",
            "-ss", str(ttl),
            "-i", video_file,
            "-vframes", "1",
            out_put_file_name,
        ]
        process = await asyncio.create_subprocess_exec(
            *file_genertor_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        t_response = stdout.decode().strip()
    #
    if os.path.exists(out_put_file_name):
        return out_put_file_name
    else:
        return None

async def extractAudios(path_to_file, user_id):
    """
    Extracts audio streams from a video file.
    """
    dir_name = os.path.dirname(os.path.dirname(path_to_file))
    if not os.path.exists(path_to_file):
        return None
    if not os.path.exists(dir_name + "/extract"):
        os.makedirs(dir_name + "/extract")
    videoStreamsData = ffmpeg.probe(path_to_file)
    extract_dir = dir_name + "/extract"
    audios = [stream for stream in videoStreamsData.get("streams") if stream["codec_type"] == "audio"]
    
    for audio in audios:
        extractcmd = ["ffmpeg", "-hide_banner", "-i", path_to_file, "-map"]
        index = audio.get("index")
        if index is not None:
            extractcmd.append(f"0:{index}")
            output_file = (
                f"({audio['tags'].get('language', 'unknown')}) "
                f"{audio['tags'].get('title', 'unknown')}.{audio['codec_type']}.mka"
            ).replace(" ", ".")
            extractcmd += ["-c", "copy", f"{extract_dir}/{output_file}"]
            LOGGER.info(extractcmd)
            subprocess.call(extractcmd)
    
    if get_path_size(extract_dir) > 0:
        return extract_dir
    else:
        LOGGER.warning(f"{extract_dir} is empty")
        return None

async def extractSubtitles(path_to_file, user_id):
    """
    Extracts subtitle streams from a video file.
    """
    dir_name = os.path.dirname(os.path.dirname(path_to_file))
    if not os.path.exists(path_to_file):
        return None
    if not os.path.exists(dir_name + "/extract"):
        os.makedirs(dir_name + "/extract")
    videoStreamsData = ffmpeg.probe(path_to_file)
    extract_dir = dir_name + "/extract"
    subtitles = [stream for stream in videoStreamsData.get("streams") if stream["codec_type"] == "subtitle"]
    
    for subtitle in subtitles:
        extractcmd = ["ffmpeg", "-hide_banner", "-i", path_to_file, "-map"]
        index = subtitle.get("index")
        if index is not None:
            extractcmd.append(f"0:{index}")
            output_file = (
                f"({subtitle['tags'].get('language', 'unknown')}) "
                f"{subtitle['tags'].get('title', 'unknown')}.{subtitle['codec_type']}.mka"
            ).replace(" ", ".")
            extractcmd += ["-c", "copy", f"{extract_dir}/{output_file}"]
            LOGGER.info(extractcmd)
            subprocess.call(extractcmd)
    
    if get_path_size(extract_dir) > 0:
        return extract_dir
    else:
        LOGGER.warning(f"{extract_dir} is empty")
        return None

import os
import re
import json
import subprocess
from datetime import datetime

import requests
from dotenv import load_dotenv
from py_trans import PyTranslator
from openai import OpenAI

load_dotenv()

# openai assistant api 設定
api_key = os.getenv('api_key')
organization = os.getenv('organization')

client = OpenAI(
    organization=organization,
    api_key=api_key
)


def get_temp_filename(extension=".mp3"):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"{timestamp}{extension}"


def get_pid(url):
    return_text = requests.get(url).text
    pid = re.findall('var guid = "(.*?)"', return_text)[0]
    return pid


def get_video_info(pid):
    url = "http://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid=" + pid
    res = requests.get(url).text
    res = json.loads(res)
    title = res['title']
    hls_url = res['hls_url']
    tag = res['tag']
    video_date = res['f_pgmtime']
    length = res['video']['totalLength']
    return title, hls_url, tag, video_date, length


def download_and_convert(m3u8_url, output_filename):
    """CCTV獲取的是m3u8檔案，使用ffmpeg轉成mp3"""
    command = [
        'ffmpeg',
        '-i', m3u8_url,
        '-y',  # 強迫覆蓋已有的檔案
        '-vn',                 # 不包含視訊
        '-acodec', 'libmp3lame',  # MP3 編碼器
        '-q:a', '0',           # 高質量音頻
        output_filename        # 輸出檔案名稱
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg 轉換失敗：{e}")


def clean_up(file_path):
    os.remove(file_path)


def speech_to_text(output_filename):
    """使用openai語音轉文字"""
    with open(output_filename, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
    return transcription.text


def translate_text(text, dest='zh-TW'):
    """
    將字體翻譯成繁體中文
    arg：
        目標語言縮寫
        dest='zh-TW'

    Translate text using Google translate：translator.google(text, dest)
    Translate text using Translate.com：translator.translate_com(text, dest)
    """
    translator = PyTranslator()
    result = translator.google(text, dest)['translation']
    return result.replace("台", "臺")


def main(url):
    temp_filename = get_temp_filename()
    pid = get_pid(url)
    title, hls_url, tag, video_date, length = get_video_info(pid)
    download_and_convert(hls_url, temp_filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    
    exec_time = f"#執行時間：{timestamp}"
    title = f"標題：{translate_text(title)}"
    tag = f"影片標籤：{translate_text(tag)}"
    video_date = f"影片日期：{translate_text(video_date)}"
    price = f"此次消耗 {float(length)/60*0.006} 美金"

    video_info = f"{exec_time}\n\n{title}\n\n{tag}\n\n{video_date}"
    zh_text = translate_text(speech_to_text(temp_filename))

    clean_up(temp_filename)

    return video_info, price, zh_text

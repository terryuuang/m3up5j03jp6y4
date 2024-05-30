import os
import re
import json
import subprocess
from datetime import datetime

import requests
import streamlit as st
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


def download_and_convert(m3u8_url, output_filename, timeout=180):
    """使用ffmpeg轉換m3u8到mp3，並設定超時時間"""
    command = [
        'ffmpeg',
        '-i', m3u8_url,
        '-y',  # 強迫覆蓋已有的檔案
        '-vn',  # 不包含視頻
        '-acodec', 'libmp3lame',  # MP3 編碼器
        '-q:a', '5',  # 音質選擇0~9，越小音質越好
        output_filename  # 輸出檔案名稱
    ]
    try:
        # 設定超時，防止過長時間執行
        subprocess.run(command, check=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        st.error("轉換超時，請檢查網絡或來源文件。")
    except subprocess.CalledProcessError as e:
        st.error(f"FFmpeg 轉換失敗：{e}")
    except Exception as e:
        st.error(f"發生未預料的錯誤：{e}")


def clean_up(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        print(f"檔案找不到，無法刪除 {file_path}")

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
    result = translator.translate_dict(text, dest)['translation']
    return result.replace("台", "臺")


def main(url):
    try:
        temp_filename = get_temp_filename()

        pid = get_pid(url)
        title, hls_url, tag, video_date, length = get_video_info(pid)

        with st.spinner("下載影片中..."):
            download_and_convert(hls_url, temp_filename)

        if os.path.exists(temp_filename):
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            exec_time = f"#執行時間：{timestamp}"
            title = f"標題：{translate_text(title)}"
            tag = f"影片標籤：{translate_text(tag)}"
            video_date = f"影片日期：{translate_text(video_date)}"
            price = f"此次消耗 {float(length)/60*0.006} 美金"
            video_info = f"{exec_time}\n\n{title}\n\n{tag}\n\n{video_date}"
            
            with st.spinner("語音轉文字中..."):
                text = speech_to_text(temp_filename)
                
            zh_text = translate_text(text)
            clean_up(temp_filename)
            return video_info, price, zh_text
        else:
            raise FileNotFoundError("這個影片不存在或無法下載。")
    except Exception as e:
        clean_up(temp_filename)
        return str(e), "錯誤發生，請檢查網址是否正確。"
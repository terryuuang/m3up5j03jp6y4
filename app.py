import asyncio
from video_processing import *

import streamlit as st
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

# Telegram bot 設定
bot_token = os.getenv('bot_token')
chat_id = os.getenv('chat_id')
bot = Bot(token=bot_token)

async def send_telegram_message(message):
    """異步發送消息到 Telegram"""
    await bot.send_message(chat_id=chat_id, text=message)

def save_and_display_content(content, role="user"):
    """ 儲存和顯示streamlit對話紀錄 """
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        st.markdown(content)

 # 頁面設置
st.set_page_config(
    page_title='語音轉文字',
    page_icon='📨',
    layout='wide',
    initial_sidebar_state='auto'
)

# 設定 Streamlit 頁面的標題
st.title("CCTV語音轉文字")

# 初始化聊天室session
if "messages" not in st.session_state:
    st.session_state.messages = []

# 顯示歷史訊息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 使用 Streamlit 的 sidebar 功能創建側邊欄
with st.sidebar:
    # st.header("輸入CCTV新聞網址")
    cctv_url = st.text_input(label="輸入CCTV新聞網址", value="")

    submit_button = st.button("執行")

    if st.button("刪除紀錄"):
        # 將一個確認標誌設置到 session 狀態中
        st.session_state.confirmation_flag = True

    if 'confirmation_flag' in st.session_state and st.session_state.confirmation_flag:
        st.write("確定要刪除紀錄？")
        if st.button("確認"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        if st.button("取消"):
            del st.session_state.confirmation_flag
            st.rerun()


# 按下執行按鈕
if submit_button:
    video_info, zh_text, price = main(cctv_url)
    save_and_display_content(video_info)
    save_and_display_content(zh_text, "assistant")
    save_and_display_content(price, "assistant")
    asyncio.run(send_telegram_message(f"{video_info}\n{'===' * 2}\n{zh_text}\n{'===' * 2}\n{price}"))
    # https://tv.cctv.com/2024/05/04/VIDE9xeKNkzUDgejA654milq240504.shtml?spm=C52346.PQw42etIf8YI.Edvk0IT63y7P.3

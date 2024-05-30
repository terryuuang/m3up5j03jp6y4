import asyncio
import bcrypt
import os
import streamlit as st
from video_processing import *
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

# 環境變數中的明文帳號密碼
plain_user_name = os.getenv('user_name')
plain_user_password = os.getenv('user_password')

# 將明文密碼加密
hashed_password = bcrypt.hashpw(plain_user_password.encode('utf-8'), bcrypt.gensalt())

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
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.sidebar:
        st.header("用戶登入")
        input_username = st.text_input("用戶名")
        input_password = st.text_input("密碼", type="password")
        login_button = st.button("登入")

        if login_button:
            if input_username == plain_user_name and bcrypt.checkpw(input_password.encode('utf-8'), hashed_password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.sidebar.error("用戶名或密碼錯誤")

if st.session_state.authenticated:
    with st.sidebar:
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
else:
    st.warning("請先登入")

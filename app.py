from video_processing import *
import streamlit as st


def save_and_display_content(content, role="user"):
    """ 儲存和顯示streamlit對話紀錄 """
    st.session_state.messages.append({"role": role, "content": content})
    with st.chat_message(role):
        st.markdown(content)

 # 頁面設置
st.set_page_config(
    page_title='CCTV語音轉文字',
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
            st.experimental_rerun()

        if st.button("取消"):
            del st.session_state.confirmation_flag
            st.experimental_rerun()


# 按下執行按鈕
if submit_button:
    video_info, zh_text, price = main(cctv_url)
    save_and_display_content(video_info)
    save_and_display_content(zh_text, "assistant")
    save_and_display_content(price, "assistant")
    # https://tv.cctv.com/2024/05/04/VIDE9xeKNkzUDgejA654milq240504.shtml?spm=C52346.PQw42etIf8YI.Edvk0IT63y7P.3

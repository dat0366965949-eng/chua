import streamlit as st
import openai
from openai import OpenAI
import re

# 1. KIỂM TRA PHIÊN BẢN (Để bạn tự kiểm chứng)
v = openai.__version__

# 2. CẤU HÌNH API
try:
    API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    API_KEY = "SỬ_DỤNG_KEY_CỦA_BẠN_TẠI_ĐÂY"

client = OpenAI(api_key=API_KEY)

st.set_page_config(page_title="A Di Đà Phật - Trợ Lý Học Tu", layout="centered")

# GIAO DIỆN CHÙA
st.markdown("""
    <style>
    .stApp { background-color: #FFF9E6; }
    [data-testid="stSidebar"] { background-color: #F4D03F; }
    .stChatMessage { background-color: #FFFFFF; border: 1px solid #F1C40F; border-radius: 15px; }
    h1, h2, h3, p, span { color: #5D4037 !important; font-family: 'serif'; }
    </style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "assistant_id" not in st.session_state:
    st.session_state["assistant_id"] = None

def smart_display(text):
    clean_text = re.sub(r'【.*?】', '', text)
    keyword_match = re.search(r'IMAGE_KEYWORD:\s*([\w_]+)', clean_text)
    final_text = clean_text.split("IMAGE_KEYWORD:")[0]
    st.markdown(final_text)
    if keyword_match:
        keyword = keyword_match.group(1)
        img_url = f"https://image.pollinations.ai/prompt/{keyword}_buddhism_zen?width=800&height=500&nologo=true"
        st.image(img_url, caption="Hình ảnh thanh tịnh")

st.markdown("<h1 style='text-align: center;'>🪷 A Di Đà Phật</h1>", unsafe_allow_html=True)
st.caption(f"Phiên bản thư viện hiện tại: {v} (Cần >= 1.21.0)")

# 3. SIDEBAR - THỈNH KINH SÁCH
with st.sidebar:
    st.header("☸️ Kinh Sách")
    uploaded_file = st.file_uploader("Tải tài liệu (PDF/Docx/Txt)", type=['pdf', 'txt', 'docx'])
    
    if uploaded_file and st.session_state["assistant_id"] is None:
        if v < "1.21.0":
            st.error(f"LỖI: Máy chủ đang chạy bản OpenAI {v} quá cũ. Vui lòng Xóa App và Tạo lại trên Streamlit Cloud.")
        else:
            with st.spinner("Đang thỉnh tri thức..."):
                try:
                    # Tải file lên
                    file_obj = client.files.create(file=uploaded_file, purpose='assistants')
                    
                    # Tạo Vector Store
                    vector_store = client.beta.vector_stores.create(name="TempleStore")
                    
                    # Chờ file xử lý xong
                    client.beta.vector_stores.files.create_and_poll(
                        vector_store_id=vector_store.id, 
                        file_id=file_obj.id
                    )
                    
                    # Tạo Assistant v2 (Dùng tool_resources thay cho file_ids)
                    assist = client.beta.assistants.create(
                        name="Sư Thầy AI",
                        instructions="Bạn là trợ lý Chùa. Trả lời dựa trên file. Cuối câu luôn ghi IMAGE_KEYWORD: [từ khóa tiếng Anh]",
                        model="gpt-4o",
                        tools=[{"type": "file_search"}],
                        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
                    )
                    st.session_state["assistant_id"] = assist.id
                    st.success("Kinh sách đã nạp xong!")
                except Exception as e:
                    st.error(f"Lỗi hệ thống: {e}")

    if st.button("Xóa lịch sử"):
        st.session_state["messages"] = []
        st.rerun()

# 4. HIỂN THỊ CHAT
for m in st.session_state["messages"]:
    with st.chat_message(m["role"], avatar="🙏" if m["role"]=="user" else "🪷"):
        if m["role"] == "user":
            st.markdown(m["content"])
        else:
            smart_display(m["content"])

if prompt := st.chat_input("Bạch Thầy, con có điều chưa rõ..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🙏"):
        st.markdown(prompt)

    if st.session_state["assistant_id"]:
        with st.chat_message("assistant", avatar="🪷"):
            with st.spinner("Đang quán chiếu..."):
                thread = client.beta.threads.create(messages=[{"role": "user", "content": prompt}])
                run = client.beta.threads.runs.create_and_poll(
                    thread_id=thread.id, 
                    assistant_id=st.session_state["assistant_id"]
                )
                if run.status == 'completed':
                    msgs = client.beta.threads.messages.list(thread_id=thread.id)
                    ans = msgs.data[0].content[0].text.value
                    st.session_state["messages"].append({"role": "assistant", "content": ans})
                    smart_display(ans)
                    st.rerun()

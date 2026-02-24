import streamlit as st
import openai
from openai import OpenAI
import re

# Kiểm tra phiên bản thư viện (Để đảm bảo không bị lỗi cũ)
LIB_VERSION = openai.__version__

# 1. CẤU HÌNH API
try:
    API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    API_KEY = "SỬ_DỤNG_KEY_CỦA_BẠN_TẠI_ĐÂY"

client = OpenAI(api_key=API_KEY)

st.set_page_config(page_title="Trợ Lý Tâm Linh - Chùa Online", layout="centered")

# GIAO DIỆN CHÙA
st.markdown("""
    <style>
    .stApp { background-color: #FFF9E6; }
    [data-testid="stSidebar"] { background-color: #F4D03F; }
    h1, h2, h3, p, span { color: #5D4037 !important; font-family: 'serif'; }
    .stChatMessage { background-color: #FFFFFF; border: 1px solid #F1C40F; border-radius: 15px; }
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
        st.image(img_url, caption=f"Hình ảnh: {keyword}")

st.title("🪷 A Di Đà Phật - Trợ Lý Học Tu")
st.caption(f"Phiên bản hệ thống: {LIB_VERSION}") # Hiển thị để kiểm tra

# SIDEBAR
with st.sidebar:
    st.header("☸️ Kinh Sách")
    uploaded_file = st.file_uploader("Tải lên Kinh sách", type=['pdf', 'txt', 'docx'])
    
    if uploaded_file and st.session_state["assistant_id"] is None:
        # KIỂM TRA PHIÊN BẢN TRƯỚC KHI CHẠY
        if LIB_VERSION < "1.21.0":
            st.error("LỖI: Phiên bản thư viện OpenAI quá cũ. Hãy làm theo Bước 1 & 2 để nâng cấp lên 1.33.0")
        else:
            with st.spinner("Đang quán chiếu tài liệu..."):
                try:
                    # Tải file
                    file_obj = client.files.create(file=uploaded_file, purpose='assistants')
                    
                    # Tạo Vector Store
                    vector_store = client.beta.vector_stores.create(name="TempleStore")
                    
                    # Chờ xử lý file
                    client.beta.vector_stores.files.create_and_poll(
                        vector_store_id=vector_store.id, file_id=file_obj.id
                    )
                    
                    # Tạo Assistant
                    assist = client.beta.assistants.create(
                        name="Sư Thầy AI",
                        instructions="Bạn là một vị Trợ lý Tâm linh. Xưng hô A Di Đà Phật, Đạo hữu. Trả lời dựa trên file. Cuối câu ghi IMAGE_KEYWORD: [từ khóa tiếng Anh]",
                        tools=[{"type": "file_search"}],
                        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
                        model="gpt-4o"
                    )
                    st.session_state["assistant_id"] = assist.id
                    st.success("Kinh sách đã nạp xong!")
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    if st.button("Xóa lịch sử"):
        st.session_state["messages"] = []
        st.rerun()

# HIỂN THỊ CHAT
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
            with st.spinner("Đang suy ngẫm..."):
                thread = client.beta.threads.create(messages=[{"role": "user", "content": prompt}])
                run = client.beta.threads.runs.create_and_poll(
                    thread_id=thread.id, assistant_id=st.session_state["assistant_id"]
                )
                if run.status == 'completed':
                    messages = client.beta.threads.messages.list(thread_id=thread.id)
                    ans = messages.data[0].content[0].text.value
                    st.session_state["messages"].append({"role": "assistant", "content": ans})
                    smart_display(ans)
                    st.rerun()

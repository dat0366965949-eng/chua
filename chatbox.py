import streamlit as st
from openai import OpenAI
import openai
import re

# 1. CẤU HÌNH API
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
    h1, h2, h3, p, span { color: #5D4037 !important; font-family: 'serif'; }
    .stChatMessage { background-color: #FFFFFF; border: 1px solid #F1C40F; border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "assistant_id" not in st.session_state:
    st.session_state["assistant_id"] = None

# Hàm hiển thị thông minh (Văn bản sạch + Ảnh thanh tịnh)
def smart_display(text):
    clean_text = re.sub(r'【.*?】', '', text)
    keyword_match = re.search(r'IMAGE_KEYWORD:\s*([\w_]+)', clean_text)
    final_text = clean_text.split("IMAGE_KEYWORD:")[0]
    st.markdown(final_text)
    if keyword_match:
        keyword = keyword_match.group(1)
        img_url = f"https://image.pollinations.ai/prompt/{keyword}_buddhism_zen_peace?width=800&height=500&nologo=true"
        st.image(img_url, caption="Hình ảnh thanh tịnh")

st.markdown("<h1 style='text-align: center;'>🪷 A Di Đà Phật</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Trợ Lý Phật Pháp: Kinh Sách & Tri Thức Internet</p>", unsafe_allow_html=True)

# 2. HÀM TẠO ASSISTANT (Tự động thích nghi)
def get_temple_assistant(file_id=None):
    instruction_prompt = """
    Bạn là một vị Trợ lý Tâm linh tại Chùa, am hiểu sâu sắc về Phật pháp.
    NHIỆM VỤ:
    1. ƯU TIÊN KINH SÁCH: Nếu có tài liệu được tải lên, hãy tìm câu trả lời trong đó trước. Bắt đầu bằng "[Theo Kinh sách của Chùa]:".
    2. CHẾ ĐỘ GOOGLE/INTERNET: Nếu trong tài liệu không có thông tin, hãy dùng kiến thức rộng lớn của bạn (tri thức Phật học thế giới) để trả lời. Bắt đầu bằng "[Theo tri thức Phật học]:".
    3. PHONG CÁCH: Điềm đạm, từ bi. Xưng hô: A Di Đà Phật, Đạo hữu, Phật tử.
    4. ẢNH: Luôn kết thúc bằng 'IMAGE_KEYWORD: [từ khóa tiếng Anh]' để minh họa.
    """
    
    # Kiểm tra tính năng mới/cũ của OpenAI trên máy chủ
    try:
        if file_id and hasattr(client.beta, 'vector_stores'):
            # Cách mới (V2)
            v_store = client.beta.vector_stores.create(name="TempleData", file_ids=[file_id])
            return client.beta.assistants.create(
                name="Sư Thầy AI",
                instructions=instruction_prompt,
                model="gpt-4o",
                tools=[{"type": "file_search"}],
                tool_resources={"file_search": {"vector_store_ids": [v_store.id]}}
            )
        elif file_id:
            # Cách cũ (V1)
            return client.beta.assistants.create(
                name="Sư Thầy AI",
                instructions=instruction_prompt,
                model="gpt-4-turbo-preview",
                tools=[{"type": "retrieval"}],
                file_ids=[file_id]
            )
        else:
            # Chế độ AI thuần túy (Không có file)
            return client.beta.assistants.create(
                name="Sư Thầy AI",
                instructions=instruction_prompt,
                model="gpt-4o"
            )
    except:
        # Fallback cuối cùng nếu mọi cách đều lỗi
        return None

# 3. SIDEBAR - QUẢN LÝ
with st.sidebar:
    st.header("☸️ Thỉnh Kinh Sách")
    uploaded_file = st.file_uploader("Tải lên tài liệu của Chùa", type=['pdf', 'txt', 'docx'])
    
    if uploaded_file and st.session_state["assistant_id"] is None:
        with st.spinner("Đang thỉnh tri thức vào AI..."):
            file_obj = client.files.create(file=uploaded_file, purpose='assistants')
            st.session_state["assistant_id"] = get_temple_assistant(file_obj.id).id
            st.success("Kinh sách đã nạp xong!")

    if st.button("Xóa lịch sử hội thoại"):
        st.session_state["messages"] = []
        st.rerun()

# 4. CHAT LOGIC
if st.session_state["assistant_id"] is None:
    # Nếu chưa có file, tạo Assistant mặc định để vẫn chat được
    st.session_state["assistant_id"] = get_temple_assistant().id

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

    with st.chat_message("assistant", avatar="🪷"):
        with st.spinner("Đang quán chiếu tri thức..."):
            try:
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
            except Exception as e:
                st.error("A Di Đà Phật, máy chủ đang bận, xin đạo hữu thử lại sau giây lát.")

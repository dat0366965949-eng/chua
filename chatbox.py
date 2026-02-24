import streamlit as st
from openai import OpenAI
import re

# 1. CẤU HÌNH API
API_KEY = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=API_KEY)

st.set_page_config(page_title="Trợ Lý Tâm Linh - Chùa Online", layout="centered")

# 2. GIAO DIỆN MÀU VÀNG CHÙA (CSS)
st.markdown("""
    <style>
    /* Nền chính của ứng dụng */
    .stApp {
        background-color: #FFF9E6; /* Màu vàng nhạt thanh tịnh */
    }
    
    /* Thanh Sidebar bên trái */
    [data-testid="stSidebar"] {
        background-color: #F4D03F; /* Màu vàng đậm hoàng y */
        color: #5D4037;
    }

    /* Tiêu đề và chữ */
    h1, h2, h3, p {
        color: #5D4037 !important; /* Màu nâu đất trà */
        font-family: 'Times New Roman', serif;
    }

    /* Khung tin nhắn Chat */
    .stChatMessage {
        background-color: #FFFFFF;
        border: 1px solid #F1C40F;
        border-radius: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }

    /* Nút bấm */
    .stButton>button {
        background-color: #D4AC0D;
        color: white;
        border-radius: 20px;
        border: none;
    }
    
    /* Biểu tượng hoa sen trang trí */
    .lotus-header {
        text-align: center;
        font-size: 50px;
        color: #E67E22;
        margin-bottom: -20px;
    }
    </style>
""", unsafe_allow_html=True)

# Hàm hiển thị nội dung và ảnh minh họa Phật giáo
def smart_display(text):
    clean_text = re.sub(r'【.*?】', '', text) # Xóa mã hệ thống
    keyword_match = re.search(r'IMAGE_KEYWORD:\s*([\w_]+)', clean_text)
    
    final_text = clean_text.split("IMAGE_KEYWORD:")[0]
    st.markdown(final_text)
    
    if keyword_match:
        keyword = keyword_match.group(1)
        # Tạo ảnh thanh tịnh
        img_url = f"https://image.pollinations.ai/prompt/{keyword}_buddhism_style_peaceful?width=800&height=500&nologo=true"
        st.image(img_url, caption=f"Hình ảnh: {keyword.replace('_', ' ')}")

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "assistant_id" not in st.session_state:
    st.session_state["assistant_id"] = None

# Giao diện đầu trang
st.markdown('<div class="lotus-header">🪷</div>', unsafe_allow_html=True)
st.title("A Di Đà Phật - Trợ Lý Học Tu")
st.caption("Nơi tìm hiểu kinh pháp, giải đáp thắc mắc và hướng dẫn tu tập tại gia.")

# 3. SIDEBAR - QUẢN LÝ KINH SÁCH
with st.sidebar:
    st.markdown("## ☸️ Phật Pháp Nhiệm Màu")
    uploaded_file = st.file_uploader("Tải lên Kinh sách / Tài liệu Chùa (PDF/Docx)", type=['pdf', 'txt', 'docx'])
    
    if uploaded_file and st.session_state["assistant_id"] is None:
        with st.spinner("Đang thỉnh tri thức vào AI..."):
            file_obj = client.files.create(file=uploaded_file, purpose='assistants')
            v_store = client.beta.vector_stores.create(name="TempleData", file_ids=[file_obj.id])
            
            # CẤU HÌNH AI THÀNH NGƯỜI TƯ VẤN CHÙA
            instruction_prompt = """
            Bạn là một vị Trợ lý Tâm linh tại Chùa, am hiểu Phật pháp và có tấm lòng từ bi. 
            Nhiệm vụ của bạn:
            1. Ngôn ngữ: Điềm đạm, khiêm tốn. Dùng các từ như "A Di Đà Phật", "Thiện nam", "Tín nữ", "Đạo hữu", "Phật tử".
            2. Trả lời: Ưu tiên tìm trong file Kinh sách đã tải lên. Nếu không có, hãy dùng kiến thức Phật học chính thống để hướng dẫn tu tập, thiền định, nhân quả.
            3. Ảnh minh họa: Luôn chèn dòng 'IMAGE_KEYWORD: [từ khóa tiếng Anh]' ở cuối câu để minh họa sự thanh tịnh.
            Ví dụ: IMAGE_KEYWORD: lotus_flower hoặc IMAGE_KEYWORD: buddha_meditation.
            """
            
            assist = client.beta.assistants.create(
                name="Sư Thầy AI",
                instructions=instruction_prompt,
                tools=[{"type": "file_search"}],
                tool_resources={"file_search": {"vector_store_ids": [v_store.id]}},
                model="gpt-4o"
            )
            st.session_state["assistant_id"] = assist.id
            st.success("Kinh sách đã được nạp xong!")

    if st.button("Làm mới tâm thức (Xóa Chat)"):
        st.session_state["messages"] = []
        st.rerun()

# 4. HIỂN THỊ HỘI THOẠI
for m in st.session_state["messages"]:
    role_icon = "🙏" if m["role"] == "user" else "🪷"
    with st.chat_message(m["role"], avatar=role_icon):
        if m["role"] == "user":
            st.markdown(m["content"])
        else:
            smart_display(m["content"])

# 5. NHẬP CÂU HỎI
if prompt := st.chat_input("Bạch Thầy, con có điều chưa rõ..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🙏"):
        st.markdown(prompt)

    if not st.session_state["assistant_id"]:
        st.info("A Di Đà Phật, xin quý Phật tử hãy chờ thầy/cô tải kinh sách ở bên trái trước.")
    else:
        with st.chat_message("assistant", avatar="🪷"):
            with st.spinner("Đang quán chiếu câu trả lời..."):
                thread = client.beta.threads.create(messages=[{"role": "user", "content": prompt}])
                run = client.beta.threads.runs.create_and_poll(
                    thread_id=thread.id, 
                    assistant_id=st.session_state["assistant_id"]
                )
                if run.status == 'completed':
                    messages = client.beta.threads.messages.list(thread_id=thread.id)
                    ans = messages.data[0].content[0].text.value
                    st.session_state["messages"].append({"role": "assistant", "content": ans})
                    smart_display(ans)
                    st.rerun()

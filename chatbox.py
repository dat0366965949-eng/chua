import streamlit as st
from openai import OpenAI
import re

# 1) API KEY
try:
    API_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
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
if "vector_store_id" not in st.session_state:
    st.session_state["vector_store_id"] = None

# Hiển thị thông minh
def smart_display(text: str):
    clean_text = re.sub(r'【.*?】', '', text)
    keyword_match = re.search(r'IMAGE_KEYWORD:\s*([A-Za-z0-9_\- ]+)', clean_text)
    final_text = clean_text.split("IMAGE_KEYWORD:")[0].strip()
    st.markdown(final_text)

    if keyword_match:
        keyword = keyword_match.group(1).strip().replace(" ", "_")
        img_url = f"https://image.pollinations.ai/prompt/{keyword}_buddhism_zen_peace?width=800&height=500&nologo=true"
        st.image(img_url, caption="Hình ảnh thanh tịnh")

SYSTEM_INSTRUCTIONS = """
Bạn là một vị Trợ lý Tâm linh tại Chùa, am hiểu sâu sắc về Phật pháp.

NHIỆM VỤ:
1) ƯU TIÊN KINH SÁCH: Nếu có tài liệu được tải lên, hãy tìm câu trả lời trong đó trước.
   Bắt đầu bằng: [Theo Kinh sách của Chùa]:
2) NẾU KHÔNG CÓ/ KHÔNG THẤY TRONG TÀI LIỆU: trả lời theo tri thức Phật học phổ quát.
   Bắt đầu bằng: [Theo tri thức Phật học]:
3) PHONG CÁCH: Điềm đạm, từ bi. Xưng hô: A Di Đà Phật, Đạo hữu, Phật tử.
4) ẢNH: Luôn kết thúc bằng: IMAGE_KEYWORD: <từ khóa tiếng Anh>
YÊU CẦU: Trả lời rõ ràng, gợi ý thực hành (quán niệm/giới-định-tuệ) ngắn gọn nếu phù hợp.
"""

st.markdown("<h1 style='text-align: center;'>🪷 A Di Đà Phật</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Trợ Lý Phật Pháp: Kinh Sách & Tri Thức</p>", unsafe_allow_html=True)

# 2) SIDEBAR: upload -> file -> vector store
with st.sidebar:
    st.header("☸️ Thỉnh Kinh Sách")
    uploaded_file = st.file_uploader("Tải lên tài liệu của Chùa", type=["pdf", "txt", "docx"])

    if uploaded_file:
        with st.spinner("Đang thỉnh tri thức vào Chùa (tạo kho tra cứu)..."):
            # upload file
            file_obj = client.files.create(file=uploaded_file, purpose="assistants")

            # create vector store
            vstore = client.vector_stores.create(name="TempleData")
            st.session_state["vector_store_id"] = vstore.id

            # attach file to vector store
            client.vector_stores.files.create(
                vector_store_id=vstore.id,
                file_id=file_obj.id
            )

            st.success("Kinh sách đã nạp xong! Có thể hỏi đáp theo tài liệu.")

    if st.button("Xóa lịch sử hội thoại"):
        st.session_state["messages"] = []
        st.rerun()

# 3) Render chat history
for m in st.session_state["messages"]:
    with st.chat_message(m["role"], avatar="🙏" if m["role"] == "user" else "🪷"):
        if m["role"] == "user":
            st.markdown(m["content"])
        else:
            smart_display(m["content"])

# 4) Ask
if prompt := st.chat_input("Bạch Thầy, con có điều chưa rõ..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🙏"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🪷"):
        with st.spinner("Đang quán chiếu tri thức..."):
            try:
                # Nếu có vector store => bật file_search
                tools = []
                tool_resources = None

                if st.session_state["vector_store_id"]:
                    tools = [{"type": "file_search"}]
                    tool_resources = {
                        "file_search": {"vector_store_ids": [st.session_state["vector_store_id"]]}
                    }

                resp = client.responses.create(
                    model="gpt-4o-mini",
                    input=[
                        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                        *st.session_state["messages"],  # gồm cả prompt mới
                    ],
                    tools=tools,
                    tool_resources=tool_resources,
                )

                ans = resp.output_text
                st.session_state["messages"].append({"role": "assistant", "content": ans})
                smart_display(ans)

            except Exception as e:
                
                st.error("A Di Đà Phật, đã có lỗi kỹ thuật. Dưới đây là chi tiết lỗi:")
                st.exception(e)  # in nguyên lỗi ra

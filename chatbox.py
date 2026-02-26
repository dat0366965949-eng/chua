import streamlit as st
from openai import OpenAI
import re

# ==============================
# 1. CẤU HÌNH API
# ==============================

try:
    API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    API_KEY = "DAN_KEY_CUA_BAN_VAO_DAY"

client = OpenAI(api_key=API_KEY)

st.set_page_config(page_title="A Di Đà Phật - Trợ Lý Học Tu", layout="centered")

# ==============================
# 2. CSS GIAO DIỆN
# ==============================

st.markdown("""
<style>
.stApp { background-color: #FFF9E6; }
[data-testid="stSidebar"] { background-color: #F4D03F; }
h1, h2, h3, p, span { color: #5D4037 !important; font-family: serif; }
.stChatMessage {
    background-color: #FFFFFF;
    border: 1px solid #F1C40F;
    border-radius: 15px;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# 3. SESSION STATE
# ==============================

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "vector_store_id" not in st.session_state:
    st.session_state["vector_store_id"] = None

# ==============================
# 4. HIỂN THỊ THÔNG MINH
# ==============================

def smart_display(text):
    clean_text = re.sub(r'【.*?】', '', text)
    keyword_match = re.search(r'IMAGE_KEYWORD:\s*([A-Za-z0-9_\- ]+)', clean_text)

    final_text = clean_text.split("IMAGE_KEYWORD:")[0].strip()
    st.markdown(final_text)

    if keyword_match:
        keyword = keyword_match.group(1).strip().replace(" ", "_")
        img_url = f"https://image.pollinations.ai/prompt/{keyword}_buddhism_zen_peace?width=800&height=500&nologo=true"
        st.image(img_url, caption="Hình ảnh thanh tịnh")

# ==============================
# 5. SYSTEM PROMPT
# ==============================

SYSTEM_PROMPT = """
Bạn là một vị Trợ lý Tâm linh tại Chùa, am hiểu sâu sắc về Phật pháp.

NHIỆM VỤ:
1) Nếu có tài liệu được tải lên, hãy ưu tiên trả lời từ tài liệu đó.
   Bắt đầu bằng: [Theo Kinh sách của Chùa]:
2) Nếu không tìm thấy trong tài liệu, trả lời theo tri thức Phật học.
   Bắt đầu bằng: [Theo tri thức Phật học]:
3) Phong cách: điềm đạm, từ bi. Xưng hô: A Di Đà Phật, Đạo hữu.
4) Luôn kết thúc bằng: IMAGE_KEYWORD: <từ khóa tiếng Anh>
"""

# ==============================
# 6. HEADER
# ==============================

st.markdown("<h1 style='text-align:center;'>🪷 A Di Đà Phật</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Trợ Lý Phật Pháp: Kinh Sách & Tri Thức</p>", unsafe_allow_html=True)

# ==============================
# 7. SIDEBAR - UPLOAD FILE
# ==============================

with st.sidebar:
    st.header("☸️ Thỉnh Kinh Sách")

    uploaded_file = st.file_uploader(
        "Tải lên tài liệu của Chùa",
        type=["pdf", "txt", "docx"]
    )

    if uploaded_file:
        with st.spinner("Đang thỉnh tri thức vào AI..."):

            # Upload file
            file_obj = client.files.create(
                file=uploaded_file,
                purpose="assistants"
            )

            # Tạo vector store
            vstore = client.vector_stores.create(name="TempleData")
            st.session_state["vector_store_id"] = vstore.id

            # Thêm file và đợi index hoàn tất
            client.vector_stores.file_batches.create_and_poll(
                vector_store_id=vstore.id,
                file_ids=[file_obj.id],
            )

            st.success("Kinh sách đã nạp xong!")

    if st.button("Xóa lịch sử hội thoại"):
        st.session_state["messages"] = []
        st.rerun()

# ==============================
# 8. HIỂN THỊ LỊCH SỬ CHAT
# ==============================

for m in st.session_state["messages"]:
    with st.chat_message(m["role"], avatar="🙏" if m["role"]=="user" else "🪷"):
        if m["role"] == "user":
            st.markdown(m["content"])
        else:
            smart_display(m["content"])

# ==============================
# 9. CHAT LOGIC
# ==============================

if prompt := st.chat_input("Bạch Thầy, con có điều chưa rõ..."):

    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar="🙏"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🪷"):
        with st.spinner("Đang quán chiếu tri thức..."):
            try:

                # Chuẩn bị messages
                input_msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
                input_msgs += st.session_state["messages"]

                tools = []
                extra_args = {}

                # Nếu có vector store thì bật file_search
                if st.session_state["vector_store_id"]:
                    tools = [{"type": "file_search"}]

                    # Gắn vector store bằng attachments
                    if input_msgs[-1]["role"] == "user":
                        input_msgs[-1]["attachments"] = [
                            {
                                "type": "file_search",
                                "vector_store_id": st.session_state["vector_store_id"],
                            }
                        ]

                resp = client.responses.create(
                    model="gpt-4o-mini",
                    input=input_msgs,
                    tools=tools
                )

                answer = resp.output_text

                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": answer
                })

                smart_display(answer)

            except Exception as e:
                st.error("Đã xảy ra lỗi kỹ thuật:")
                st.exception(e)

import streamlit as st
from rag_pipeline import build_rag
from rag_prompt import RAG_PROMPT
from groq import Groq
import os
from dotenv import load_dotenv
import tempfile
import pymupdf

@st.cache_data
def render_pdf_page(file_bytes, page_number):

    doc = pymupdf.open(stream=file_bytes, filetype="pdf")

    page = doc.load_page(page_number)

    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(1.5, 1.5),
        alpha=False
    )

    image_bytes = pix.tobytes("png")

    doc.close()

    return image_bytes

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="DocuMind-AI", layout="wide")
st.title("DocuMind-AI")
st.text("Ask your PDF anything")
st.text("Select or upload a PDF from the sidebar to begin")

# ---------------- SESSION STATE ----------------
if "rag" not in st.session_state:
    st.session_state.rag = None

if "file_path" not in st.session_state:
    st.session_state.file_path = None

if "file_name" not in st.session_state:
    st.session_state.file_name = None


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.caption(
    """
DocuMind-AI is a RAG-powered PDF assistant that allows users to upload documents, retrieve relevant information using semantic search, and generate AI-based answers from document context.

Upload a PDF, preview the content, and ask questions naturally.
"""
)
    # st.header("Select Document")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    DATA_FOLDER = "sample_files"
    os.makedirs(DATA_FOLDER, exist_ok=True)

    pdf_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".pdf")]

    selected_pdf = st.selectbox("Or choose any sample file", ["None"] + pdf_files)

    file_path = None
    file_name = None

    # Priority: upload > sample
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            file_path = tmp.name
            file_name = uploaded_file.name

    elif selected_pdf != "None":
        file_path = os.path.join(DATA_FOLDER, selected_pdf)
        file_name = selected_pdf

    # -------- PROCESS BUTTON --------
    if st.button("Process Document", disabled=(file_path is None)):
        with st.spinner("Processing document..."):

            # Reset previous state
            st.session_state.rag = None

            rag = build_rag(file_path)

            st.session_state.rag = rag
            st.session_state.file_path = file_path
            st.session_state.file_name = file_name

        st.success(f"Successfully Processed {file_name}")


# ---------------- MAIN AREA ----------------

# -------- FILE INFO --------
if st.session_state.file_name:
    st.info(f"{st.session_state.file_name} loaded. Ask your questions below.")

# -------- PREVIEW --------
if st.session_state.file_path:

    st.subheader("Document Preview")

    try:
        with open(st.session_state.file_path, "rb") as f:
            pdf_bytes = f.read()

        doc = pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        total_pages = len(doc)
        doc.close()

        if total_pages > 0:

            page_number = st.number_input(
                "Select Page",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1
            )

            image_bytes = render_pdf_page(
                pdf_bytes,
                page_number - 1
            )

            st.image(
                image_bytes,
                use_container_width=True
            )

            st.caption(
                f"Page {page_number} of {total_pages}"
            )

        else:
            st.warning("This PDF contains no pages.")

    except Exception as e:

        st.warning("PDF preview is unavailable.")

        st.error(str(e))

# -------- CHAT --------
if st.session_state.rag:
    st.subheader("💬 Ask Questions")

    question = st.text_input("Ask something from the document:")

    if question:
        rag = st.session_state.rag
        results = rag.search(question, k=5)

        context = "\n\n".join(
            [f"(Page {d['page']}) {d['text']}" for d in results]
        )

        prompt = RAG_PROMPT.format(context=context, question=question)

        with st.spinner("Generating answer..."):
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "You are a strict RAG-based extraction assistant. Always rely only on provided context."},
                    {"role": "user", "content": prompt}
                ]
            )
        print(f"responses::\n{response}")
        answer = response.choices[0].message.content

        st.markdown("### ✅ Answer")
        st.write(answer)

        with st.expander("Explore retrieved context"):
            st.markdown(
        f"""
        <div style="height:200px; overflow-y:auto; font-size:13px; line-height:1.4;">
        {context}
        </div>
        """,
        unsafe_allow_html=True
    )

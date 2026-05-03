from docx import Document
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
# from pypdf import PdfReader
# import pdfplumber
import fitz
import re

class MyRAG:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.texts = []
        self.index = None

    def add_documents(self, docs):
        self.texts = docs
        embeddings = self.model.encode([d["text"] for d in docs])

        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(np.array(embeddings))

    def search(self, query, k=3):
        query_vec = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_vec), k)

        return [self.texts[i] for i in indices[0]]
    


def load_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

# def load_pdf(file_path):
#     reader = PdfReader(file_path)
#     text = ""

def load_pdf(file_path):
    doc = fitz.open(file_path)
    docs = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("blocks")
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))

        page_text = ""
        for b in blocks:
            page_text += b[4] + "\n"

        docs.append({
            "text": page_text.strip(),
            "page": page_num + 1
        })

    return docs

def load_docx(file_path):
    doc = Document(file_path)
    text = ""

    for para in doc.paragraphs:
        text += para.text + "\n"

    return text

def load_document(file_path):
    if file_path.endswith(".txt"):
        return load_txt(file_path)
    elif file_path.endswith(".pdf"):
        return load_pdf(file_path)
    elif file_path.endswith(".docx"):
        return load_docx(file_path)
    else:
        raise ValueError("Unsupported file type")

def chunk_text(text, size=500, overlap=100):
    sentences = re.split(r'(?<=[.!?]) +', text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= size:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
        else:
            chunks.append(current_chunk.strip())

            # 🔥 Add overlap
            overlap_text = current_chunk[-overlap:]
            current_chunk = overlap_text + " " + sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

# For loop on the "docs" list of dictionary

def process_documents(docs):
    chunked_docs = []

    for d in docs:
        chunks = chunk_text(d["text"])

        for chunk in chunks:
            chunked_docs.append({
                "text": chunk,
                "page": d["page"]
            })

    return chunked_docs
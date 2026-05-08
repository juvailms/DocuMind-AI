from groq import Groq
import os
from dotenv import load_dotenv
from rag_pipeline import MyRAG, load_document, process_documents
from rag_prompt import RAG_PROMPT

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

file_path = "sample_file.pdf"

docs = load_document(file_path)

chunked_docs = process_documents(docs)

rag = MyRAG()
rag.add_documents(chunked_docs)

def main():

    while True:
        question = input("\nAsk: ")

        results  = rag.search(question, k =5)
        context = "\n\n".join(
            [f"(Page {d['page']}) {d['text']}" for d in results]
        )
        # print (f"Here is the context :\n {context}")

        prompt = RAG_PROMPT.format(context=context, question=question)

        response=client.chat.completions.create(
            model = "llama-3.1-8b-instant",
            messages=[
        {"role": "system", "content": "You are a strict RAG-based extraction assistant. Always rely only on provided context."},
        {"role": "user", "content": prompt}
    ]
        )

        # print(response)
        print("\nAnswer: ", response.choices[0].message.content)

if __name__ == "__main__":
    main()
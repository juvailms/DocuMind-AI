from groq import Groq
import os
from dotenv import load_dotenv
from rag_pipeline import MyRAG, load_document, process_documents
from rag_prompt import RAG_PROMPT


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

file_path = "Juvail_LLM_Assign (1) (1).pdf"

docs = load_document(file_path)

chunked_docs = process_documents(docs)
print (f"here is the new new chunked_docs :\n {chunked_docs}")


rag = MyRAG()
rag.add_documents(chunked_docs)

def main():

    while True:
        question = input("\nAsk: ")

        results  = rag.search(question, k =5)
        # print (f"here is the context : {context}")
        context = "\n\n".join(
            [f"(Page {d['page']}) {d['text']}" for d in results]
        )
        print (f"here is the new new context :\n {context}")

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
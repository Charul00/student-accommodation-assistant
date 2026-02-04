from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os

def build_rag_chain():
    """
    Build a Retrieval Augmented Generation chain for policy questions.
    Returns a chain that can answer questions based on policy documents.
    """
    try:
        docs = []
        # Get the absolute path to policies directory
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        base_path = os.path.join(current_dir, "data", "policies")
        
        print(f"🔍 Loading policy documents from: {base_path}")

        if not os.path.exists(base_path):
            print(f"❌ Policy directory not found: {base_path}")
            return None

        # Load all text files from policies directory
        for file in os.listdir(base_path):
            if file.endswith(".txt"):
                file_path = os.path.join(base_path, file)
                print(f"📄 Loading: {file}")
                loader = TextLoader(file_path, encoding='utf-8')
                docs.extend(loader.load())

        if not docs:
            print("❌ No policy documents found!")
            return None

        print(f"✅ Loaded {len(docs)} policy documents")

        # Split documents into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

        chunks = splitter.split_documents(docs)
        print(f"✅ Created {len(chunks)} document chunks")

        # Create embeddings and vector store
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(chunks, embeddings)

        # Create LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )

        # Create prompt template
        prompt_template = """You are a helpful assistant answering questions about student accommodation policies. 
        Use the following context to answer the question. If you can't find the answer in the context, say "I don't have enough information to answer that question."

        Context: {context}
        Question: {question}

        Answer:"""

        prompt = ChatPromptTemplate.from_template(prompt_template)

        # Create retrieval chain using LCEL
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        retriever = vectorstore.as_retriever(k=3)
        
        qa_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        print("✅ RAG chain built successfully!")
        return qa_chain

    except Exception as e:
        print(f"❌ Error building RAG chain: {e}")
        return None
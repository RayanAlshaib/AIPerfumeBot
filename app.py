import streamlit as st
import os
import re
import chromadb
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

st.set_page_config(page_title="AI Perfume Bot", page_icon="✨")
st.title("🤖 خبير العطور الذكي")
st.markdown("مرحباً بك! اسألني عن أي عطر أو سعر.")

# --- الدالات الأساسية ---
def normalize_arabic(text):
    if not isinstance(text, str): return text
    text = re.sub("[أإآ]", "ا", text)
    text = re.sub("ة", "ه", text)
    text = re.sub(r"[\u064B-\u0652]", "", text)
    return text.strip()

@st.cache_resource
def load_bot():
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    else:
        st.error("GROQ_API_KEY not found in secrets!")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "chroma_db")
    
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    persistent_client = chromadb.PersistentClient(path=db_path)
    
    vector_db = Chroma(
        client=persistent_client,
        embedding_function=embeddings,
    )
    
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.1)
    return vector_db.as_retriever(search_kwargs={"k": 5}), llm

retriever, llm = load_bot()

template = """
أنت خبير عطور محترف. أجب على سؤال المستخدم بناءً على المعلومات التالية فقط.
إذا لم تجد الإجابة، قل أن العطر غير متوفر حالياً.
Context: {context}
Question: {input}
Answer (in Arabic):
"""
prompt = ChatPromptTemplate.from_template(template)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("كيف يمكنني مساعدتك اليوم؟"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        clean_input = normalize_arabic(user_input)
        response = rag_chain.invoke(clean_input)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
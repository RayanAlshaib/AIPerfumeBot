import pandas as pd
import os
import shutil
import re
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

def normalize_arabic(text):
    if not isinstance(text, str):
        return text
    text = re.sub("[أإآ]", "ا", text)
    text = re.sub("ة", "ه", text)
    text = re.sub(r"[\u064B-\u0652]", "", text)
    return text.strip()

FILE_NAME = "sample_data.csv"  
DB_DIR = "./chroma_db"

if os.path.exists(DB_DIR):
    try:
        shutil.rmtree(DB_DIR)
        print("🗑️ تم تنظيف قاعدة البيانات القديمة.")
    except Exception as e:
        print(f"⚠️ لم أستطع مسح المجلد تلقائياً (ربما لأنه مفتوح): {e}")
        print("💡 لا بأس، سنقوم بتحديث البيانات فوقها.")

df = pd.read_csv(FILE_NAME)

documents = []
for _, row in df.iterrows():
    raw_content = f"""
    الاسم بالعربي: {row['Name_AR']}
    English Name: {row['Name_EN']}
    Brand (الشركة): {row['Brand']}
    Category (التصنيف): {row['Category']}
    الأسعار (Prices):
    - 100g: {row['Price_100g']}
    - 250g: {row['Price_250g']}
    - 500g: {row['Price_500g']}
    - 1kg: {row['Price_1kg']}
    """
    
    clean_content = normalize_arabic(raw_content)
    
    documents.append(Document(page_content=clean_content, metadata={"source": str(row['Name_EN'])}))

print("🔄 جاري معالجة البيانات (Normalization & Embeddings)...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

vector_db = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory=DB_DIR
)

print(f"✅ تم بنجاح! تم فهرسة {len(documents)} عطر بنصوص موحدة.")
# AI Perfume Assistant (RAG-Powered)

An intelligent fragrance consultant that uses Large Language Models and Retrieval-Augmented Generation (RAG) to provide expert-level perfume recommendations and pricing info.

## 🎯 What it Does
This chatbot acts as a virtual fragrance expert. Unlike a standard AI, it doesn't "hallucinate" prices or stock; it retrieves real data from a specific dataset.
- Natural Language Understanding: Users can ask questions in English or Arabic .
- Context-Aware Retrieval: It searches through a database of over 200 perfumes to find the closest matches.
- Luxury Consulting: Provides structured details including brand history, and accurate pricing.

## 💡 Why I Built It
The fragrance industry is vast and often overwhelming for customers. I built this project to solve two main problems:
1. Data Accuracy: Traditional LLMs often give outdated or incorrect prices for specific luxury goods. Using RAG ensures the bot stays grounded in real inventory data.
2. Personalization at Scale: To demonstrate how AI can bridge the gap between a massive wholesale catalog and a personalized customer experience, providing a "high-end boutique" feel digitally.

## 🏗️ System Architecture
The project is built using a modern AI stack designed for speed and scalability:

- Orchestration: `LangChain` manages the flow between the user query, the database, and the AI model.
- Vector Database: `ChromaDB` stores the perfume data as mathematical "embeddings," allowing for semantic search.
- LLM: `Llama 3.3 70B` (via Groq API) serves as the reasoning engine for generating human-like responses.
- Embedding Model: `HuggingFace` multilingual models ensure the bot understands both Arabic and English perfectly.
- Frontend: `Streamlit` provides a clean, responsive web interface.

## ⚙️ How to Run It

### 1. Installation
Clone the repository and install the required dependencies:
```bash
git clone [https://github.com/RayanAlshaib/AIPerfumeBot.git](https://github.com/RayanAlshaib/AIPerfumeBot.git)
cd AIPerfumeBot
pip install -r requirements.txt

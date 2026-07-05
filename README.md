# AI Perfume Bot: State-Controlled B2B RAG Funnel ✨

A production-ready conversational AI consultant engineered to guide wholesale clients through a structured B2B sales funnel. Unlike fragile, standard chat wrappers that easily get derailed, this application implements a custom state machine to handle multi-step conversational routing, inventory validation, and custom multi-tier wholesale pricing calculations without funnel loop regression.

## 🛠️ Tech Stack
- Orchestration: `LangChain` manages the flow between the user query, the database, and the AI model.
- Vector Database: `ChromaDB` stores the perfume data as mathematical "embeddings," allowing for semantic search.
- LLM: `Llama 3.3 70B` (via Groq API) serves as the reasoning engine for generating human-like responses.
- Embedding Model: `HuggingFace` multilingual models ensure the bot understands both Arabic and English perfectly.
- Frontend: `Streamlit` provides a clean, responsive web interface.

---

## 🏗️ Architectural Core Wins (What I Solved)

### 1. Eliminating Funnel Loop Regression (State Machine Integration)
- The Problem: In multi-step sales funnels, LLMs frequently get confused by conversational side-tracks (e.g., a user asking for a quantity before selecting a brand, or changing their mind halfway through), causing standard models to reset the conversation or lose their position in the pipeline.
- The Solution: I bound the LangChain RAG pipeline to a Python backend state controller (`st.session_state`). The LLM prompt is executed dynamically based on the active structural state (`discovery`, `gender_filter`, `quantity_lock`, `price_reveal`), guaranteeing a strict conversion path.

### 2. Multi-Chain Intent Routing & Context Isolation
- The Problem: Passing short, conversational user modifications (like "yes", "ok", or "1 kg and a half") directly into a standard vector database retriever pulls random, irrelevant document chunks, degrading the context window and corrupting the LLM's pricing calculations.
- The Solution: I built an intent routing matrix in Python:
  * Intent Route A (Pricing): Catches numerical and weight adjustments, bypassing broad vector searches to look up data strictly tied to the cached `chosen_perfume` inside the session state.
  * Intent Route B (Catalog Check): Confirms real-time catalog matches, locking the specific product entity into memory so subsequent queries stay isolated to that data.

### 3. Dynamic Text Normalization
Integrated Arabic text preprocessing (`normalize_arabic`) using regex token parsing to harmonize standard text mutations (like Alef, Ta Marbuta, and Diacritics/Tashkeel). This ensures high-accuracy semantic vector matching across code-switched Arabic and English wholesale catalogs.

> 🔒 **Data Privacy Note:** The production dataset and exact proprietary wholesale pricing matrices have been omitted from this public repository. A simulated product architecture (`sample_data.csv`) is provided to demonstrate the chunking, embedding, and multi-tier pricing calculation capabilities of the RAG pipeline.

---

## 🚀 How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/RayanAlshaib/AIPerfumeBot.git](https://github.com/RayanAlshaib/AIPerfumeBot.git)
   cd AIPerfumeBot
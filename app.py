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
st.markdown("مرحباً بك! اسألني عن أي عطر.")

with st.sidebar:
    st.markdown("### About")
    st.markdown("This bot uses RAG to answer queries about perfumes from a custom Arabic/English dataset.")
    st.markdown("**Tech Stack:** Python, LangChain, Chroma, Groq LLaMA, Streamlit")


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

current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "chroma_db")
if not os.path.exists(db_path):
    st.error("Database not found. Please run ingest.py first.")
    st.stop()
retriever, llm = load_bot()

template = """
You are "The Scent Expert," a world-class B2B account manager for a luxury fragrance manufacturer. You guide wholesale clients through a structured, step-by-step consultation funnel.

### CONVERSATION STATE FUNNEL (STRICT PROTOCOL):

[STEP 1: INITIAL DISCOVERY & LINE SELECTION]
- If the user asks a general question (e.g., "what do you have?", "do you have scents in kilo?"), do NOT list specific perfumes yet. Ask them to clarify if they want luxury "Inspired Perfume Oils" or "Single-Variety Oils".
- **TRANSITION TRIGGER:** If the user's message explicitly names their choice (e.g., they say "inspired perfumes oils" or "single-variety oils"), you MUST acknowledge their choice and immediately ask them for their target category or scent profile (e.g., "Excellent choice. Are you looking for men's, women's, or unisex fragrance profiles in our inspired line?"). Do NOT repeat the selection question.

[STEP 2: GENDER FILTERING RULE]
- If the user specifies "Men", "Women", or "Unisex" (الجنسين):
  * You MUST only recommend options from the **Inspired Perfume Oils** line based on the context.
  * HIDE Single-Variety Oils completely from this step.
  * List 2-3 matching inspired perfumes from the context using bullet points. Format: * **[Brand Name] - [Product Name]**: [One-sentence premium description].
  * Instantly transition to Step 3 by asking: "What wholesale quantity tier are you looking to order for these selections?"

[STEP 3: THE QUANTITY LOCK]
- If the user selects a specific perfume or confirms interest, DO NOT show any prices, currencies, or calculations yet.
- You MUST explicitly ask the client for their required wholesale volume tier (e.g., 100g, 250g, 500g, or 1kg bulk canisters).

[STEP 4: THE PRICE REVEAL]
- ONLY display the price once the user has explicitly stated their desired quantity.
- Calculate the total based on the context data for that specific volume tier and state the final price clearly in Omani Rials (OMR).

### GLOBAL EXECUTION RULES:
- **Language Mirroring:** Respond strictly in the language of the user's latest message (English for English, Arabic for Arabic). Keep perfume names in English.
- **Tone:** Elite corporate account manager. No robotic automated filler words, and NO repetitive greetings.

CONTEXT FROM DATASET:
{context}

USER MESSAGE:
{question}

EXPERT RESPONSE:
"""
prompt = ChatPromptTemplate.from_template(template)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)


if "funnel_step" not in st.session_state:
    st.session_state.funnel_step = "discovery" 
if "chosen_line" not in st.session_state:
    st.session_state.chosen_line = None
if "chosen_perfume" not in st.session_state:
    st.session_state.chosen_perfume = None

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
        user_message = clean_input.strip().lower()

        # 1. GREETING INTERCEPTOR
        if user_message in ["hello", "hi", "hey", "marhaba", "مرحبا", "اهلا", "سلام"]:
            response = (
                "Hello and welcome. I am your Wholesale Scent Consultant. "
                "How can I assist your business with our premium fragrance oil collection today?"
            )
            st.markdown(response)

       # 2. SMART INTERCEPTOR: Skip discovery if they immediately ask for a gender/category
        elif st.session_state.funnel_step == "discovery" and any(x in user_message for x in ["men", "women", "unisex", "perfume", "رجالي", "نسائي", "جنسين"]):
            st.session_state.chosen_line = "Inspired Perfume Oils"
            st.session_state.funnel_step = "quantity_lock"  # Move straight to quantity lock after showing
            
            # Directly call RAG to fetch the specific men's/women's options
            response = rag_chain.invoke(f"The customer wants to see choices for: {clean_input} from the line Inspired Perfume Oils. List 2-3 matching perfumes and explicitly ask what wholesale quantity tier they need.")
            st.markdown(response)
        # 3. STATE 1: STANDARD DISCOVERY 
        elif st.session_state.funnel_step == "discovery":
            if "inspired" in user_message:
                st.session_state.chosen_line = "Inspired Perfume Oils"
                st.session_state.funnel_step = "gender_filter"
                response = "Excellent choice. Are you looking for men's, women's, or unisex fragrance profiles in our inspired line?"
            elif "single" in user_message or "oil" in user_message:
                st.session_state.chosen_line = "Single-Variety Oils"
                st.session_state.funnel_step = "gender_filter"
                response = "Understood. Which specific single-variety aromatic oil profile (e.g., Mint, Coconut, Sandal) are you looking to source?"
            else:
                response = "To provide you with the most accurate catalog options, could you please clarify if your business requires luxury 'Inspired Perfume Oils' or pure 'Single-Variety Oils'?"
            st.markdown(response)

       # 4. STATES 2, 3, & 4: CORE FUNNEL HANDLING
        else:
            if st.session_state.funnel_step == "gender_filter":
                response = rag_chain.invoke(f"{clean_input} from line {st.session_state.chosen_line}")
                st.markdown(response)
                
                if any(x in user_message for x in ["men", "women", "unisex", "mancera", "dior", "chanel", "matter", "جنسين", "رجالي", "نسائي"]):
                    st.session_state.funnel_step = "quantity_lock"
            
            elif st.session_state.funnel_step in ["quantity_lock", "price_reveal"]:
                # Check A: Catch simple conversational agreements/acknowledgments first
                if user_message in ["yes", "ok", "sure", "i am", "yes i am", "نعم", "موافق", "ايوا"]:
                    response = "Excellent. Please provide your target wholesale quantity (e.g., 500g bins, 1.5 kg, or 1kg canisters) for your selected perfume so I can calculate your wholesale pricing."
                    st.markdown(response)

                # Check B: Dynamic Catalog Check — Is the user looking up a specific perfume name/brand?
                else:
                    test_docs = retriever.invoke(clean_input)
                    is_quantity_lookalike = any(x in user_message for x in ["kilo", "kg", "كيلو", "وزن", "سعر", "price"]) or any(char.isdigit() for char in user_message)
                    
                    if test_docs and not is_quantity_lookalike:
                        # Update session state with the perfume name they just looked up
                        st.session_state.chosen_perfume = clean_input
                        
                        lookup_template = """
                        You are a professional B2B scent consultant. The client is asking if a product or brand is available.
                        Based on the context, confirm if we have it. If yes, list the specific matches found in the context as bold bullet points with a one-sentence luxury description. Keep brand names in English.
                        If the product is NOT available in the context, clearly state that it is not in our current wholesale catalog.
                        Then, ask the customer what wholesale quantity tier they need.
                        
                        CONTEXT:
                        {context}
                        
                        USER INQUIRY:
                        {question}
                        
                        EXPERT RESPONSE:
                        """
                        lookup_prompt = ChatPromptTemplate.from_template(lookup_template)
                        lookup_chain = (
                            {"context": lambda x: format_docs(test_docs), "question": RunnablePassthrough()}
                            | lookup_prompt
                            | llm
                            | StrOutputParser()
                        )
                        response = lookup_chain.invoke(clean_input)
                        st.markdown(response)
                    
                    # Check C: DEFAULT PRICING ROUTE
                    else:
                        # If we have a stored chosen_perfume, force the retriever to look up THAT specific product's price data!
                        if st.session_state.chosen_perfume:
                            pricing_docs = retriever.invoke(f"{st.session_state.chosen_perfume} price wholesale")
                            context_data = format_docs(pricing_docs)
                            target_perfume = st.session_state.chosen_perfume
                        else:
                            context_data = format_docs(test_docs)
                            target_perfume = "the selected item"

                        pricing_template = """
                        You are a professional B2B scent consultant. The customer is specifying or updating their required quantity tier.
                        Using the context provided for {perfume_name}, extract the intended amount they want to buy (e.g., 1.5 kg, 500g).
                        Look up the wholesale pricing tiers for this product in the context data and calculate the total breakdown cleanly in Omani Rials (OMR).
                        If they ask for a custom combination like 1.5kg, calculate 1kg + 500g based on the documentation numbers. Do NOT list pricing for random other perfumes.
                        
                        CONTEXT DATA:
                        {context}
                        
                        USER MESSAGE:
                        {question}
                        
                        EXPERT RESPONSE:
                        """
                        pricing_prompt = ChatPromptTemplate.from_template(pricing_template)
                        pricing_chain = (
                            {"context": lambda x: context_data, "question": RunnablePassthrough()}
                            | pricing_prompt
                            | llm
                            | StrOutputParser()
                        )
                        
                        response = pricing_chain.invoke(f"Calculate pricing for {clean_input}")
                        st.markdown(response)
                        st.session_state.funnel_step = "price_reveal"

            # Sources handling
            try:
                docs = retriever.invoke(clean_input)
                sources = list(set([doc.metadata.get('source', 'Unknown') for doc in docs]))
                st.caption(f"📚 Sources: {', '.join(sources)}")
            except Exception:
                pass

        # Save response to history
        st.session_state.messages.append({"role": "assistant", "content": response})
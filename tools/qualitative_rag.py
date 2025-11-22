# tools/qualitative_rag.py
import os
import json
import datetime
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import LlamaCpp
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_DB_DIR", "./db/chroma")
EMBED_MODEL_NAME = os.getenv("SENTENCE_EMBED_MODEL", "all-MiniLM-L6-v2")
LLAMA_MODEL_PATH = os.getenv("LLAMA_MODEL_PATH", None)
LLAMA_N_CTX = int(os.getenv("LLAMA_N_CTX", "2048"))

def get_embedding_model():
    return SentenceTransformerEmbeddings(model_name=EMBED_MODEL_NAME)

def get_llm():
    if not LLAMA_MODEL_PATH:
        raise RuntimeError("LLAMA_MODEL_PATH not set in .env")
    llm = LlamaCpp(model_path=LLAMA_MODEL_PATH, n_ctx=LLAMA_N_CTX, temperature=0.0, verbose=False)
    return llm

def build_or_get_chroma(data_dir: str, persist_dir: str = CHROMA_DIR):
    texts = []
    metadata = []
    splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=150)

    for fname in sorted(os.listdir(data_dir)):
        if not fname.lower().endswith(".pdf"):
            continue
        path = os.path.join(data_dir, fname)
        loader = PyPDFLoader(path)
        docs = loader.load()
        for d in docs:
            chunks = splitter.split_text(d.page_content)
            for i, chunk in enumerate(chunks):
                texts.append(chunk)
                metadata.append({"source": fname, "chunk": i})

    embeddings = get_embedding_model()
    chroma_db = Chroma.from_texts(texts=texts, embedding=embeddings, metadatas=metadata, persist_directory=persist_dir)
    chroma_db.persist()
    return chroma_db

def qualitative_query(chroma_db, query: str, topk:int=6) -> str:
    retriever = chroma_db.as_retriever(search_type="similarity", search_kwargs={"k": topk})
    docs = retriever.get_relevant_documents(query)
    joined = "\n\n---\n\n".join(d.page_content for d in docs)

    llm = get_llm()
    prompt = (
        "You are an analyst assistant. Based on the transcript snippets below, summarize recurring themes, management sentiment, "
        "forward-looking statements, risks and opportunities in concise bullet points.\n\n"
        f"Query: {query}\n\nDocuments:\n{joined}\n\nProvide the answer."
    )
    out = llm(prompt)
    return out

def qualitative_structured(chroma_db, query: str):
    raw = qualitative_query(chroma_db, query, topk=8)
    llm = get_llm()
    schema_prompt = (
        "You MUST return valid JSON only with keys: themes (list of short strings), "
        "management_sentiment (string), forward_looking_statements (list), risks (list), opportunities (list). "
        "Do not output anything else. If unsure, use empty lists or 'unknown'.\n\n"
        "Input notes:\n" + raw + "\n\nReturn JSON now."
    )
    out = llm(schema_prompt)
    try:
        obj = json.loads(out)
    except Exception:
        import re
        m = re.search(r"\{.*\}", out, re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group(0))
            except Exception:
                obj = None
        else:
            obj = None

    if not obj:
        obj = {
            "themes": [],
            "management_sentiment": raw.strip()[:400],
            "forward_looking_statements": [],
            "risks": [],
            "opportunities": []
        }

    obj["_raw_excerpt"] = raw[:4000]
    obj["_generated_at"] = datetime.datetime.utcnow().isoformat()
    return obj

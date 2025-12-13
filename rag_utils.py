import os
import hashlib
import logging
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter

import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec

# -------------------------
# Logging
# -------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# -------------------------
# Env
# -------------------------
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "agro-index")
DATA_DIR = os.getenv("DATA_DIR", "data")

# -------------------------
# Gemini (generation only)
# -------------------------
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in environment variables (.env)")

genai.configure(api_key=GOOGLE_API_KEY)
llm = genai.GenerativeModel("gemini-2.5-flash")

# -------------------------
# Local HF Embeddings (free)
# -------------------------
_LOCAL_EMB_MODEL = None
_LOCAL_EMB_DIM: Optional[int] = None

HF_EMB_MODEL_NAME = os.getenv(
    "HF_EMB_MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"  # 768 dim, multilingual
)

def _ensure_local_model() -> bool:
    global _LOCAL_EMB_MODEL, _LOCAL_EMB_DIM
    if _LOCAL_EMB_MODEL is not None:
        return True
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(HF_EMB_MODEL_NAME)
        _LOCAL_EMB_MODEL = model
        _LOCAL_EMB_DIM = len(model.encode("test"))
        logger.info("Loaded local embedding model: %s (dim=%s)", HF_EMB_MODEL_NAME, _LOCAL_EMB_DIM)
        return True
    except Exception as e:
        logger.exception("Failed to load SentenceTransformer model: %s", e)
        _LOCAL_EMB_MODEL = None
        _LOCAL_EMB_DIM = None
        return False

def generate_embedding(text: str) -> Optional[List[float]]:
    """Return normalized embedding vector (list[float]) from local HF model."""
    if not isinstance(text, str):
        # In case caller passes a Document by mistake
        text = getattr(text, "page_content", None) or str(text)

    if not _ensure_local_model():
        return None

    try:
        emb = _LOCAL_EMB_MODEL.encode(text, normalize_embeddings=True)
        return emb.tolist() if hasattr(emb, "tolist") else list(emb)
    except Exception as e:
        logger.exception("Local embedding failed: %s", e)
        return None

# -------------------------
# Pinecone
# -------------------------
if not PINECONE_API_KEY:
    raise ValueError("Missing PINECONE_API_KEY in environment variables (.env)")

pc = Pinecone(api_key=PINECONE_API_KEY)

# Make sure embedding model is available so we know dimension
if not _ensure_local_model():
    raise RuntimeError(
        "SentenceTransformers is not available. Install it:\n"
        "  pip install -U sentence-transformers torch\n"
    )

# Ensure dimension matches your Pinecone index
EMB_DIM = _LOCAL_EMB_DIM
if EMB_DIM != 768:
    raise RuntimeError(
        f"Embedding dimension mismatch: got {EMB_DIM}. "
        "Use a 768-dim model (e.g. paraphrase-multilingual-mpnet-base-v2 / all-mpnet-base-v2)."
    )

# Create index if missing
if INDEX_NAME not in pc.list_indexes().names():
    logger.info("Creating Pinecone index %s (dim=%s)", INDEX_NAME, EMB_DIM)
    pc.create_index(
        name=INDEX_NAME,
        dimension=EMB_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

index = pc.Index(INDEX_NAME)

# -------------------------
# PDF Load + Chunk
# -------------------------
def load_documents() -> List[Dict[str, Any]]:
    """
    Returns list of dict items:
      { "source": filename, "page": page_number, "text": extracted_text }
    """
    docs = []
    if not os.path.isdir(DATA_DIR):
        raise FileNotFoundError(f"DATA_DIR not found: {DATA_DIR}")

    for filename in os.listdir(DATA_DIR):
        if not filename.lower().endswith(".pdf"):
            continue

        path = os.path.join(DATA_DIR, filename)
        try:
            reader = PdfReader(path)
        except Exception as e:
            logger.warning("Failed to read PDF %s: %s", filename, e)
            continue

        for page_idx, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            text = text.strip()
            if not text:
                continue
            docs.append({
                "source": filename,
                "page": page_idx + 1,  # human-readable
                "text": text
            })

    logger.info("Loaded %s pages of text from PDFs in %s", len(docs), DATA_DIR)
    return docs

def chunk_documents(pages: List[Dict[str, Any]]):
    """
    Returns list of LangChain Document objects with metadata.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = []
    for p in pages:
        # Create Documents from the page text
        docs = splitter.create_documents([p["text"]], metadatas=[{
            "source": p["source"],
            "page": p["page"]
        }])
        chunks.extend(docs)
    logger.info("Created %s chunks", len(chunks))
    return chunks

def _stable_id(text: str, source: str, page: int, chunk_index: int) -> str:
    """
    Stable ID so re-indexing doesn't create duplicates.
    """
    h = hashlib.sha1(f"{source}|{page}|{chunk_index}|{text}".encode("utf-8")).hexdigest()
    return f"{source}-p{page}-c{chunk_index}-{h[:10]}"

def index_documents(chunks, batch_size: int = 50):
    """
    Upsert chunks into Pinecone in batches.
    """
    vectors_batch = []
    total_indexed = 0

    for i, chunk in enumerate(chunks):
        text = getattr(chunk, "page_content", None) or str(chunk)
        meta = getattr(chunk, "metadata", {}) or {}
        source = meta.get("source", "unknown")
        page = int(meta.get("page", 0) or 0)

        vec = generate_embedding(text)
        if vec is None:
            logger.warning("Skipping chunk %s: embedding failed", i)
            continue

        vid = _stable_id(text=text, source=source, page=page, chunk_index=i)

        vectors_batch.append({
            "id": vid,
            "values": vec,
            "metadata": {
                "text": text,
                "source": source,
                "page": page
            }
        })

        if len(vectors_batch) >= batch_size:
            index.upsert(vectors=vectors_batch)
            total_indexed += len(vectors_batch)
            vectors_batch = []

    if vectors_batch:
        index.upsert(vectors=vectors_batch)
        total_indexed += len(vectors_batch)

    logger.info("✅ Indexed %s vectors into Pinecone", total_indexed)
    return total_indexed

# -------------------------
# RAG Answer
# -------------------------
def get_answer(query: str) -> str:
    query = (query or "").strip()
    if not query:
        return "Veuillez écrire une question."

    qv = generate_embedding(query)
    if qv is None:
        return (
            "Désolé - impossible de calculer les embeddings localement. "
            "Vérifiez l'installation: pip install -U sentence-transformers torch"
        )

    try:
        results = index.query(vector=qv, top_k=4, include_metadata=True)
        matches = results.get("matches", []) if isinstance(results, dict) else []
    except Exception as e:
        logger.exception("Pinecone query failed: %s", e)
        return (
            "Désolé - la recherche dans la base a échoué (Pinecone). "
            "Vérifiez la clé Pinecone et l'index."
        )

    if not matches:
        context = ""
    else:
        # Build context with sources
        parts = []
        for m in matches:
            md = m.get("metadata", {}) or {}
            txt = md.get("text", "")
            src = md.get("source", "unknown")
            pg = md.get("page", "?")
            if txt:
                parts.append(f"[Source: {src}, page {pg}]\n{txt}")
        context = "\n\n".join(parts)

    instruction = (
        "Tu es Felah, un assistant agricole expert et amical.\n"
        "Réponds dans la langue de la question.\n"
        "Si c’est une salutation, réponds poliment.\n"
        "Sinon, donne une réponse claire, courte, structurée, pédagogique.\n"
        "Si le contexte est vide ou insuffisant, dis-le et réponds au mieux sans inventer.\n"
        "Termine toujours par : 'N’hésitez pas à poser une autre question.'"
    )

    prompt = (
        f"{instruction}\n\n"
        f"Contexte (extraits des documents) :\n{context}\n\n"
        f"Question : {query}\n"
        f"Réponse :"
    )

    try:
        return llm.generate_content(prompt).text
    except Exception as e:
        logger.exception("Gemini generation failed: %s", e)
        return (
            "Désolé - la génération de réponse a échoué (Gemini). "
            "Vérifiez la clé GOOGLE_API_KEY et votre accès au modèle."
        )

# -------------------------
# Optional: one-shot indexing helper
# -------------------------
def build_index():
    pages = load_documents()
    chunks = chunk_documents(pages)
    index_documents(chunks)

if __name__ == "__main__":
    # Example usage:
    # 1) python rag_utils.py  -> builds index
    # 2) then call get_answer("...") from your API
    build_index()
    print(get_answer("bonjour"))

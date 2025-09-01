import os
from typing import List
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from src.utils import logger

EMBEDDING_MODEL = None

def create_qdrant_client():
    """Create and return a Qdrant client connecting to localhost"""
    client = QdrantClient(host="localhost", port=6333)
    logger.info("Connected to Qdrant at localhost:6333")
    return client

def get_embedding_model():
    global EMBEDDING_MODEL
    if EMBEDDING_MODEL is None:
        EMBEDDING_MODEL = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-mpnet-base-v2",
            device="cpu",
            trust_remote_code=True
        )
    return EMBEDDING_MODEL

def check_and_create_qdrant_collection(client, collection_name: str):
    from qdrant_client.http.exceptions import UnexpectedResponse
    embed_model = get_embedding_model()
    
    # Get the embedding dimension by creating a test embedding
    try:
        # Method 1: Try to access the model's dimension directly if available
        if hasattr(embed_model, 'model') and hasattr(embed_model.model, 'get_sentence_embedding_dimension'):
            vector_size = embed_model.model.get_sentence_embedding_dimension()
        else:
            # Method 2: Create a test embedding to determine the dimension
            test_embedding = embed_model.get_text_embedding("test")
            vector_size = len(test_embedding)
    except Exception as e:
        # Method 3: Use the known dimension for the specific model
        logger.warning(f"Could not determine embedding dimension automatically: {e}")
        logger.info("Using default dimension 768 for all-mpnet-base-v2")
        vector_size = 768  # Default dimension for all-mpnet-base-v2
    
    try:
        client.get_collection(collection_name)
        logger.info(f"Collection '{collection_name}' already exists")
        return False
    except (UnexpectedResponse, ValueError):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info(f"Created new collection: '{collection_name}' with size {vector_size}")
        return True

def load_documents_from_chunks(chunk_dir: str) -> List[Document]:
    """Load processed text chunks as LlamaIndex Documents"""
    documents = []
    
    if not os.path.exists(chunk_dir):
        logger.warning(f"Directory {chunk_dir} does not exist")
        return documents
    
    for filename in os.listdir(chunk_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(chunk_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                if text.strip():
                    documents.append(Document(text=text, metadata={"source": filename}))
            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")
    
    logger.info(f"Loaded {len(documents)} documents from {chunk_dir}")
    return documents

def create_index(collection_name: str = "research_papers"):
    """Create a new vector index from processed documents using local embeddings"""
    client = create_qdrant_client()
    embed_model = get_embedding_model()
    check_and_create_qdrant_collection(client, collection_name)
    vector_store = QdrantVectorStore(
        client=client, 
        collection_name=collection_name
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    documents = load_documents_from_chunks("data/processed/")
    if not documents:
        logger.warning("No documents found to index. Run preprocessing first.")
        return None
    index = VectorStoreIndex.from_documents(
        documents, 
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True
    )
    logger.info(f"Index created successfully with {len(documents)} documents using local embeddings")
    return index

def list_collections():
    """List all available collections in Qdrant"""
    client = create_qdrant_client()
    try:
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        logger.info(f"Available collections: {collection_names}")
        return collection_names
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        return []

def delete_collection(collection_name: str):
    """Delete a collection from Qdrant"""
    client = create_qdrant_client()
    try:
        client.delete_collection(collection_name)
        logger.info(f"Deleted collection: {collection_name}")
        return True
    except Exception as e:
        logger.error(f"Error deleting collection {collection_name}: {e}")
        return False

def get_index(collection_name: str = "research_papers"):
    """Get existing index or create a new one with local embeddings"""
    try:
        client = create_qdrant_client()
        try:
            client.get_collection(collection_name)
        except Exception:
            logger.warning(f"Collection '{collection_name}' doesn't exist")
            return create_index(collection_name)
        
        vector_store = QdrantVectorStore(
            client=client, 
            collection_name=collection_name
        )
        embed_model = get_embedding_model()
        index = VectorStoreIndex.from_vector_store(
            vector_store, 
            embed_model=embed_model
        )
        logger.info(f"Loaded existing index from collection '{collection_name}' with local embeddings")
        return index
    except Exception as e:
        logger.error(f"Error loading index: {e}")
        logger.info("Creating new index with local embeddings...")
        return create_index(collection_name)
from llama_index.core import VectorStoreIndex
from llama_index.llms.openai import OpenAI
from .indexer import get_index
from src.utils import logger

def setup_query_engine(collection_name: str = "research_papers"):
    """Set up the query engine with the specified index"""
    try:
        index = get_index(collection_name)
        if index is None:
            raise ValueError("No index available. Please run indexing first.")
        query_engine = index.as_query_engine(
            llm=OpenAI(model="gpt-4.1-nano"),
            similarity_top_k=3,
            response_mode="tree_summarize"
        )
        # tree summairzer better for longer context + more logic preserving but if being cost effective take compact
        return query_engine
    except Exception as e:
        logger.error(f"Error setting up query engine: {e}")
        raise

def query_research(query: str, collection_name: str = "research_papers"):
    """Query the research papers and return a summarized answer"""
    logger.info(f"Querying: {query}")
    
    try:
        query_engine = setup_query_engine(collection_name)
        response = query_engine.query(query)
        return response
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return None

def display_answer(response):
    """Display the response in a formatted way"""
    if response is None:
        print("No response received. Check if indexing was completed.")
        return
        
    print(f"Answer: {response.response}")
    
    if hasattr(response, 'source_nodes') and response.source_nodes:
        print("\nSources:")
        for i, source_node in enumerate(response.source_nodes, 1):
            source = source_node.metadata.get('source', 'Unknown')
            similarity = getattr(source_node, 'score', None)
            sim_text = f" (Similarity: {similarity:.3f})" if similarity else ""
            print(f"  {i}. {source}{sim_text}")
    else:
        print("\n  No specific sources referenced")
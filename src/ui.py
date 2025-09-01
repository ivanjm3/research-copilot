import streamlit as st
import os
import sys
from pathlib import Path
import tempfile
from typing import List, Dict, Any
import pandas as pd

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest import download_papers, fetch_papers
from src.preprocess import process_all_papers
from src.indexer import create_index, get_index, list_collections, delete_collection
from src.query import query_research, display_answer
from src.utils import logger

# Page configuration
st.set_page_config(
    page_title="Research Copilot",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .paper-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
    }
    .summary-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'selected_papers' not in st.session_state:
    st.session_state.selected_papers = []
if 'current_collection' not in st.session_state:
    st.session_state.current_collection = "research_papers"

def initialize_session():
    """Initialize session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.chat_history = []
        st.session_state.selected_papers = []
        st.session_state.current_collection = "research_papers"

def display_chat_message(role, content):
    """Display a chat message"""
    with st.chat_message(role):
        st.markdown(content)

def display_chat_history():
    """Display the chat history"""
    for role, content in st.session_state.chat_history:
        display_chat_message(role, content)

def get_paper_metadata():
    """Get metadata for papers in the data/raw directory"""
    papers = []
    raw_dir = "data/raw"
    if os.path.exists(raw_dir):
        for filename in os.listdir(raw_dir):
            if filename.endswith('.pdf'):
                papers.append({
                    'filename': filename,
                    'path': os.path.join(raw_dir, filename),
                    'title': filename.replace('.pdf', '').replace('_', ' ')
                })
    return papers

def summarize_paper(paper_path: str, query: str = "Provide a comprehensive summary of this paper") -> str:
    """Summarize a single paper"""
    try:
        # Create a temporary collection for this paper
        collection_name = f"temp_{os.path.basename(paper_path).replace('.pdf', '')[:20]}"
        
        # Process and index this single paper
        with st.spinner(f"Processing {os.path.basename(paper_path)}..."):
            # Create temp directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Process the single paper
                from src.preprocess import process_paper
                process_paper(paper_path, temp_dir)
                
                # Create index
                client = None
                try:
                    from src.indexer import create_qdrant_client, check_and_create_qdrant_collection
                    from llama_index.vector_stores.qdrant import QdrantVectorStore
                    from llama_index.core import StorageContext, VectorStoreIndex
                    from src.indexer import load_documents_from_chunks
                    
                    client = create_qdrant_client()
                    check_and_create_qdrant_collection(client, collection_name)
                    
                    vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
                    storage_context = StorageContext.from_defaults(vector_store=vector_store)
                    
                    documents = load_documents_from_chunks(temp_dir)
                    if documents:
                        index = VectorStoreIndex.from_documents(
                            documents, 
                            storage_context=storage_context
                        )
                        
                        # Query for summary
                        query_engine = index.as_query_engine(
                            similarity_top_k=3,
                            response_mode="tree_summarize"
                        )
                        response = query_engine.query(f"{query}. Include key findings, methodology, and contributions.")
                        return str(response)
                finally:
                    # Clean up temporary collection
                    if client:
                        try:
                            client.delete_collection(collection_name)
                        except:
                            pass
        
        return "Could not generate summary for this paper."
    except Exception as e:
        logger.error(f"Error summarizing paper: {e}")
        return f"Error generating summary: {str(e)}"

def compare_papers(papers: List[Dict], comparison_query: str) -> str:
    """Compare multiple papers"""
    try:
        # Create a temporary collection for comparison
        collection_name = "temp_comparison"
        
        with st.spinner("Processing papers for comparison..."):
            # Process all selected papers
            all_documents = []
            for paper in papers:
                paper_path = paper['path']
                with tempfile.TemporaryDirectory() as temp_dir:
                    from src.preprocess import process_paper
                    process_paper(paper_path, temp_dir)
                    
                    from src.indexer import load_documents_from_chunks
                    documents = load_documents_from_chunks(temp_dir)
                    for doc in documents:
                        doc.metadata['paper_title'] = paper['title']
                    all_documents.extend(documents)
            
            if not all_documents:
                return "No content found in selected papers for comparison."
            
            # Create index for comparison
            from src.indexer import create_qdrant_client, check_and_create_qdrant_collection
            from llama_index.vector_stores.qdrant import QdrantVectorStore
            from llama_index.core import StorageContext, VectorStoreIndex
            
            client = create_qdrant_client()
            check_and_create_qdrant_collection(client, collection_name)
            
            vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            index = VectorStoreIndex.from_documents(
                all_documents, 
                storage_context=storage_context
            )
            
            # Query for comparison
            query_engine = index.as_query_engine(
                similarity_top_k=10,
                response_mode="tree_summarize"
            )
            response = query_engine.query(
                f"Compare and contrast these research papers. {comparison_query} "
                f"Focus on methodologies, findings, contributions, and relationships between them. "
                f"Papers: {[p['title'] for p in papers]}"
            )
            
            # Clean up
            try:
                client.delete_collection(collection_name)
            except:
                pass
            
            return str(response)
    except Exception as e:
        logger.error(f"Error comparing papers: {e}")
        return f"Error generating comparison: {str(e)}"

def main():
    initialize_session()
    
    st.markdown('<h1 class="main-header">🔬 Research Copilot</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Collection selection
        collections = list_collections()
        collection_names = [coll.name for coll in collections] if collections else ["research_papers"]
        selected_collection = st.selectbox(
            "Select Collection",
            collection_names,
            index=0
        )
        st.session_state.current_collection = selected_collection
        
        st.header("📥 Data Management")
        
        # Paper ingestion
        with st.expander("Download New Papers"):
            search_query = st.text_input("Search Query", "transformer architecture")
            max_results = st.slider("Number of Papers", 1, 20, 5)
            if st.button("Download Papers"):
                with st.spinner("Downloading papers..."):
                    try:
                        downloaded = download_papers(search_query, "data/raw/", max_results)
                        st.success(f"Downloaded {len(downloaded)} papers!")
                    except Exception as e:
                        st.error(f"Error downloading papers: {e}")
        
        # Preprocessing
        if st.button("Process Papers"):
            with st.spinner("Processing papers..."):
                try:
                    processed = process_all_papers("data/raw/", "data/processed/")
                    st.success(f"Processed {len(processed)} chunks!")
                except Exception as e:
                    st.error(f"Error processing papers: {e}")
        
        # Indexing
        if st.button("Build/Update Index"):
            with st.spinner("Building index..."):
                try:
                    index = create_index(selected_collection)
                    if index:
                        st.success("Index built successfully!")
                    else:
                        st.error("Failed to build index")
                except Exception as e:
                    st.error(f"Error building index: {e}")
        
        st.header("📊 Statistics")
        papers = get_paper_metadata()
        st.write(f"**Papers Downloaded:** {len(papers)}")
        
        processed_dir = "data/processed"
        if os.path.exists(processed_dir):
            chunks = [f for f in os.listdir(processed_dir) if f.endswith('.txt')]
            st.write(f"**Text Chunks:** {len(chunks)}")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "📄 Paper Library", "🔍 Compare Papers"])
    
    with tab1:  # Chat tab
        st.header("Chat with Your Research Papers")
        
        # Display chat history
        display_chat_history()
        
        # Chat input
        if prompt := st.chat_input("Ask a question about your research papers..."):
            # Add user message to chat history
            st.session_state.chat_history.append(("user", prompt))
            display_chat_message("user", prompt)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = query_research(prompt, selected_collection)
                        if response:
                            st.markdown(response.response)
                            st.session_state.chat_history.append(("assistant", response.response))
                            
                            # Show sources
                            with st.expander("View Sources"):
                                if hasattr(response, 'source_nodes') and response.source_nodes:
                                    for i, source_node in enumerate(response.source_nodes, 1):
                                        source = source_node.metadata.get('source', 'Unknown')
                                        st.write(f"{i}. {source}")
                                else:
                                    st.write("No sources referenced")
                        else:
                            st.error("Failed to get response. Please check if indexing was completed.")
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_history.append(("assistant", error_msg))
    
    with tab2:  # Paper Library tab
        st.header("Your Research Paper Library")
        
        papers = get_paper_metadata()
        
        if not papers:
            st.info("No papers found. Download some papers first!")
        else:
            # Paper selection for comparison
            selected_indices = st.multiselect(
                "Select papers for comparison:",
                options=[i for i in range(len(papers))],
                format_func=lambda x: papers[x]['title'][:50] + "..." if len(papers[x]['title']) > 50 else papers[x]['title']
            )
            
            st.session_state.selected_papers = [papers[i] for i in selected_indices]
            
            # Display papers
            for i, paper in enumerate(papers):
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div class="paper-card">
                            <h4>{paper['title']}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("📝 Summarize", key=f"summarize_{i}"):
                            with st.spinner("Generating summary..."):
                                summary = summarize_paper(paper['path'])
                                st.markdown(f"""
                                <div class="summary-box">
                                    <h5>Summary</h5>
                                    <p>{summary}</p>
                                </div>
                                """, unsafe_allow_html=True)
            
            # Show selected papers for comparison
            if st.session_state.selected_papers:
                st.subheader("Selected for Comparison")
                for paper in st.session_state.selected_papers:
                    st.write(f"- {paper['title']}")
    
    with tab3:  # Compare Papers tab
        st.header("Compare Research Papers")
        
        if not st.session_state.selected_papers:
            st.info("Select papers for comparison in the Paper Library tab first!")
        else:
            st.write("**Papers selected for comparison:**")
            for paper in st.session_state.selected_papers:
                st.write(f"- {paper['title']}")
            
            comparison_query = st.text_input(
                "Comparison focus (optional):",
                "Compare the methodologies, findings, and contributions"
            )
            
            if st.button("🔍 Compare Selected Papers"):
                with st.spinner("Analyzing and comparing papers..."):
                    comparison = compare_papers(st.session_state.selected_papers, comparison_query)
                    
                    st.markdown("### Comparison Results")
                    st.markdown(f"""
                    <div class="summary-box">
                        <p>{comparison}</p>
                    </div>
                    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
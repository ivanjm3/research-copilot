import argparse
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from src.ingest import download_papers
from src.preprocess import process_all_papers
from src.indexer import create_index, get_index, list_collections, delete_collection
from src.query import query_research, display_answer
from src.utils import logger

def main():
    parser = argparse.ArgumentParser(description="research copilot")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Ingest
    ingest_parser = subparsers.add_parser("ingest", help="Download research papers")
    ingest_parser.add_argument("query", help="Search query for arXiv")
    ingest_parser.add_argument("--max-results", type=int, default=10, 
                              help="Maximum number of papers to download")
    
    # Preprocess command
    preprocess_parser = subparsers.add_parser("preprocess", help="Process downloaded papers")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Create vector index")
    index_parser.add_argument("--collection", default="research_papers", 
                             help="Qdrant collection name")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query research papers")
    query_parser.add_argument("question", help="Your research question")
    query_parser.add_argument("--collection", default="research_papers", 
                             help="Qdrant collection name")
    
    # List collections command
    subparsers.add_parser("list-collections", help="List all collections in Qdrant")
    
    # Delete collection command
    delete_parser = subparsers.add_parser("delete-collection", help="Delete a collection")
    delete_parser.add_argument("collection_name", help="Name of collection to delete")
    
    ui_parser = subparsers.add_parser("ui", help="Launch Streamlit UI")
    args = parser.parse_args()
    
    if args.command == "ingest":
        logger.info(f"Downloading papers for query: {args.query}")
        download_papers(args.query, "data/raw/", args.max_results)
        
    elif args.command == "preprocess":
        logger.info("Processing papers...")
        process_all_papers("data/raw/", "data/processed/")
        
    elif args.command == "index":
        logger.info(f"Creating index for collection: {args.collection}")
        create_index(args.collection)
        
    elif args.command == "query":
        logger.info(f"Querying: {args.question}")
        response = query_research(args.question, args.collection)
        display_answer(response)
        
    elif args.command == "list-collections":
        collections = list_collections()
        if collections:
            print("Available collections:")
            for coll in collections:
                print(f"  - {coll.name}")
        else:
            print("No collections found")
            
    elif args.command == "delete-collection":
        if delete_collection(args.collection_name):
            print(f"Successfully deleted collection: {args.collection_name}")
        else:
            print(f"Failed to delete collection: {args.collection_name}")
    elif args.command == "ui":
        import subprocess
        import os
        streamlit_app_path = os.path.join(os.path.dirname(__file__), "ui.py")
        subprocess.run(["streamlit", "run", streamlit_app_path])      
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
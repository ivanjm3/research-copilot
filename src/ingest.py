import arxiv
import os
from typing import List, Optional
from urllib.request import urlretrieve
from src.utils import logger


def fetch_papers(query: str,max_results: int ,sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance) -> List[arxiv.Result]:
    # Fetch paper metadata from arXiv API
    logger.info(f"Fetching papers for query: {query}")
    client = arxiv.Client()
    search = arxiv.Search(query=query,max_results=max_results,sort_by=sort_by)
    results = list(client.results(search))
    logger.info(f"Found {len(results)} papers")
    return results

def download_paper(result: arxiv.Result, output_dir: str) -> str:
    # Download a paper PDF to the specified directory
    os.makedirs(output_dir, exist_ok=True)
    title = result.title.replace(" ", "_").replace("/", "_")
    filename = f"{result.updated.year}_{title}.pdf"
    filepath = os.path.join(output_dir, filename)
    logger.info(f"Downloading: {result.title}")
    urlretrieve(result.pdf_url, filepath)
    return filepath

def download_papers(query: str, output_dir: str,max_results: Optional[int] = None) -> List[str]:
    # Main function to fetch and download papers
    from .utils import get_env_var
    if max_results is None:
        max_results = int(get_env_var("ARXIV_MAX_RESULTS", 7))
    papers = fetch_papers(query, max_results)
    downloaded_files = []
    for paper in papers:
        try:
            filepath = download_paper(paper, output_dir)
            downloaded_files.append(filepath)
        except Exception as e:
            logger.error(f"Failed to download {paper.title}: {e}")
    
    return downloaded_files
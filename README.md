Research Copilot 🔬

A powerful AI-powered research assistant that helps you discover, analyze, and query academic papers from arXiv. Built with LlamaIndex and Qdrant for intelligent document retrieval and question-answering.
Features

    📥 Paper Ingestion: Automated download of research papers from arXiv API

    🔍 Text Processing: PDF text extraction, cleaning, and intelligent chunking

    🧠 Vector Indexing: Qdrant-based vector storage with OpenAI embeddings

    💬 Natural Language Querying: Ask questions about your research papers

    📊 Streamlit UI: User-friendly interface for paper management and exploration

    📄 Individual Summarization: Get AI-generated summaries of specific papers

    🔍 Multi-Paper Comparison: Compare methodologies and findings across multiple papers

Project Structure
```bash
research-copilot/
├── .env                  # API keys, DB URL, etc.
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── data/
│   ├── raw/              # Downloaded PDFs
│   ├── processed/        # Extracted & cleaned text chunks
│   └── index/            # Vector DB metadata
├── src/
│   ├── __init__.py
│   ├── main.py           # CLI entry point
│   ├── ui.py            # 5.Streamlit web interface
│   ├── ingest.py         # 1.Fetch + download papers
│   ├── preprocess.py     # 2. chunker
│   ├── indexer.py        # 3.embedding
│   ├── query.py          # 4.Query engine + summarization
│   └── utils.py          # Common helpers
└── notebooks/
    └── playground.ipynb  # Experiments
```

Prerequisites

    Python 3.8+

    Docker (for Qdrant)

    OpenAI API key

Installation

    Clone and setup environment:
```bash
git clone <your-repo-url>
cd research-copilot
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

    Install dependencies:
```bash
uv pip install -r requirements.txt
```

    Setup Qdrant with Docker:
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

    Configure environment:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```


Quick Start
CLI Interface

    
```bash
#Download papers:
python -m src.main ingest "transformer architecture" --max-results 5

#Process papers:
python -m src.main preprocess

#Build index:
python -m src.main index

#Query your papers:
python -m src.main query "What are the key innovations in transformer architecture?"
```

Web Interface
```bash
# Launch the Streamlit UI
python -m src.main ui
# or
streamlit run src/ui.py
```

Web Interface Features

    Chat Interface: Natural conversation with your research papers

    Paper Library: Browse and manage downloaded papers

    Individual Summaries: Get detailed summaries of specific papers

    Comparative Analysis: Compare methodologies across multiple papers

    Visual Statistics: See download and processing metrics



```mermaid
graph TB
    %% Styling
    classDef user fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef api fill:#bbdefb,stroke:#0d47a1,stroke-width:2px;
    classDef process fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px;
    classDef storage fill:#ffecb3,stroke:#ff6f00,stroke-width:2px;
    classDef ai fill:#fce4ec,stroke:#880e4f,stroke-width:2px;
    classDef ui fill:#e8eaf6,stroke:#283593,stroke-width:2px;

    %% User Input
    USER[User Research Interest]:::user
    
    %% Data Ingestion Layer
    ARXIV[arXiv API]:::api
    PDF[PDF Download]:::process
    RAW[Raw PDF Storage<br/>data/raw/]:::storage
    
    USER --> ARXIV
    ARXIV --> PDF
    PDF --> RAW

    %% Text Processing Layer
    EXTRACT[Text Extraction<br/>PyMuPDF]:::process
    CLEAN[Text Cleaning]:::process
    CHUNK[Text Chunking]:::process
    PROCESSED[Processed Text Storage<br/>data/processed/]:::storage
    
    RAW --> EXTRACT
    EXTRACT --> CLEAN
    CLEAN --> CHUNK
    CHUNK --> PROCESSED

    %% Vector Indexing Layer
    DOCS[Document Objects<br/>LlamaIndex]:::process
    EMBED[Embedding Generation<br/>OpenAI API]:::api
    QDRANT[Qdrant Vector Database<br/>localhost:6333]:::storage
    INDEX[Vector Index<br/>data/index/]:::storage
    
    PROCESSED --> DOCS
    DOCS --> EMBED
    EMBED --> QDRANT
    QDRANT --> INDEX

    %% Query Processing Layer
    QUERY[User Question]:::user
    RETRIEVE[Semantic Search<br/>& Retrieval]:::process
    LLM[LLM Processing<br/>OpenAI GPT]:::ai
    ANSWER[Summarized Answer]:::user
    
    QUERY --> RETRIEVE
    RETRIEVE --> LLM
    LLM --> ANSWER
    RETRIEVE -.-> QDRANT

    %% User Interface Layer
    CLI[Command Line Interface<br/>src/main.py]:::ui
    STREAMLIT[Web Interface<br/>Streamlit UI]:::ui
    CHAT[Chat Interface]:::ui
    COMPARE[Paper Comparison]:::ui
    SUMMARIZE[Individual Summaries]:::ui
    
    CLI --> CHAT
    STREAMLIT --> CHAT
    STREAMLIT --> COMPARE
    STREAMLIT --> SUMMARIZE
    CHAT -.-> QUERY
    COMPARE -.-> QUERY
    SUMMARIZE -.-> QUERY

    %% Internal Data Flow
    subgraph "Data Pipeline"
        direction LR
        ARXIV --> PDF --> RAW --> EXTRACT --> CLEAN --> CHUNK --> PROCESSED --> DOCS --> EMBED --> QDRANT --> INDEX
    end

    subgraph "Query Pipeline"
        direction LR
        QUERY --> RETRIEVE --> LLM --> ANSWER
    end

    subgraph "User Interfaces"
        direction TB
        CLI
        STREAMLIT
    end

    %% Legend
    subgraph "Legend"
        L_USER[User Input/Output]:::user
        L_API[External API]:::api
        L_PROCESS[Processing]:::process
        L_STORAGE[Storage]:::storage
        L_AI[AI Component]:::ai
        L_UI[Interface]:::ui
    end
```
"""Document ingestion script for ChromaDB."""
import hashlib
import os
import re
import shutil
import sys
from datetime import datetime
from typing import Set, Tuple

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Now import the rest
import pandas as pd  # noqa: E402
from loguru import logger  # noqa: E402
from watchdog.observers import Observer  # noqa: E402
from watchdog.events import FileSystemEventHandler  # noqa: E402
from langchain_community.document_loaders import (  # noqa: E402
    PyPDFLoader,
    UnstructuredHTMLLoader,
    UnstructuredWordDocumentLoader
)
from langchain_huggingface import HuggingFaceEmbeddings  # noqa: E402
from databases.chroma_config import get_chroma_client  # noqa: E402

# -------------------------
# LF changes -->
# -------------------------

from chromadb.api.types import EmbeddingFunction, Documents

# Adapter to wrap LangChain HuggingFace embedding in Chroma-compatible function
class LangChainEmbeddingAdapter(EmbeddingFunction[Documents]):
    def __init__(self, ef):
        self.ef = ef
    def __call__(self, input: Documents):
        return self.ef.embed_documents(input)

# Create HuggingFace embeddings object
hf_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Wrap in Chroma adapter
adapted_embeddings = LangChainEmbeddingAdapter(hf_embeddings)

# -------------------------
# <-- LF changes
# -------------------------

# Constants
WATCH_FOLDER = "docs/landing"
DONE_FOLDER = "docs/done"
# Use centralized logs folder
LOGS_FOLDER = os.path.join(project_root, "logs/docs_loader")
TRACKING_FILE = "processed_files.csv"

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def get_file_hash(file_path: str) -> str:
    """Generate MD5 hash of file content."""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def get_processed_files() -> Tuple[Set[str], Set[str]]:
    """Get list of already processed files and their hashes."""
    if os.path.exists(TRACKING_FILE):
        df = pd.read_csv(TRACKING_FILE)
        return set(df['filename'].tolist()), set(df['content_hash'].tolist())
    return set(), set()


def add_processed_file(filename: str, file_path: str, content_hash: str):
    """Add file to processed files tracking."""
    new_row = pd.DataFrame([{
        'filename': filename,
        'original_path': file_path,
        'content_hash': content_hash,
        'processed_date': datetime.now().isoformat()
    }])
    
    if os.path.exists(TRACKING_FILE):
        df = pd.read_csv(TRACKING_FILE)
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        df = new_row
    
    df.to_csv(TRACKING_FILE, index=False)


def get_campaign_id_from_filename(filename: str) -> str:
    """
    Extract campaign ID from filename using regex.
    Example filename: "campaign_101_summary_report.pdf"
    """
    match = re.search(r'campaign_(\d+)_', filename)
    return match.group(1) if match else None


def get_loader_for_file(file_path: str):
    """Get appropriate document loader based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return PyPDFLoader(file_path)
    elif ext in ['.html', '.htm']:
        return UnstructuredHTMLLoader(file_path)
    elif ext == '.docx':
        return UnstructuredWordDocumentLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str, max_chars: int = 2000) -> list[str]:
    """Split text into chunks respecting sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    
    for sent in sentences:
        if len(current) + len(sent) + 1 <= max_chars:
            current += " " + sent if current else sent
        else:
            chunks.append(current.strip())
            current = sent
    if current:
        chunks.append(current.strip())
    return chunks


class DocumentHandler(FileSystemEventHandler):
    """Handler for document ingestion events."""
    
    def on_created(self, event):
        """Handle new document creation events."""
        if not event.is_directory:
            file_ext = os.path.splitext(event.src_path)[1].lower()
            if file_ext in ['.pdf', '.html', '.htm', '.docx']:
                filename = os.path.basename(event.src_path)
                content_hash = get_file_hash(event.src_path)
                processed_files, processed_hashes = get_processed_files()
                
                # Check both filename and content hash
                is_processed = (
                    filename in processed_files or
                    content_hash in processed_hashes
                )
                if is_processed:
                    logger.info(f"Skipping already processed file: {filename}")
                    # Move to done folder without reprocessing
                    done_path = os.path.join(DONE_FOLDER, filename)
                    shutil.move(event.src_path, done_path)
                    logger.info(
                        f"Moved {filename} to done folder (already processed)"
                    )
                else:
                    logger.info(f"New document detected: {event.src_path}")
                    self.ingest_document(event.src_path)

    def ingest_document(self, file_path: str):
        """Process and ingest a document into ChromaDB."""
        try:
            filename = os.path.basename(file_path)
            content_hash = get_file_hash(file_path)
            
            # Get appropriate loader and load document
            loader = get_loader_for_file(file_path)
            docs = loader.load()
            
            # Extract campaign ID and prepare metadata
            campaign_id = get_campaign_id_from_filename(file_path)
            metadata = {
                'source': file_path,
                'campaign_id': campaign_id,
                'file_type': os.path.splitext(filename)[1].lower(),
                'ingestion_date': datetime.now().isoformat()
            }
            
            # Process document content
            client = get_chroma_client()

            # /*
            # collection = client.get_or_create_collection(
            #     name="campaign_reports",
            #     embedding_function=embeddings,
            #     metadata={
            #         "description": (
            #             "Campaign performance reports and documentation"
            #         )
            #     }
            # )
            # */

            collection = client.get_or_create_collection(
                name="campaign_reports",
                embedding_function=adapted_embeddings,
                metadata={
                    "description": (
                        "Campaign performance reports and documentation"
                    )
                }
            )

            
            # Split content into sections and chunks
            full_text = "\n".join(doc.page_content for doc in docs)
            headers = [
                "Executive Summary",
                "Campaign Overview",
                "Key Metrics",
                "Performance Insights",
                "Recommendations"
            ]
            
            pattern = r"(" + "|".join(map(re.escape, headers)) + ")"
            parts = re.split(pattern, full_text)
            
            # Process each section
            for i in range(1, len(parts), 2):
                header = parts[i].strip()
                content = parts[i+1].strip() if i+1 < len(parts) else ""
                
                # Split section into smaller chunks
                subchunks = chunk_text(content)
                for j, chunk in enumerate(subchunks):
                    doc_id = (
                        f"{campaign_id}_"
                        f"{header.lower().replace(' ', '_')}_"
                        f"{j}"
                    )
                    
                    # Add to ChromaDB with metadata
                    collection.add(
                        documents=[f"{header}\n{chunk}"],
                        ids=[doc_id],
                        metadatas=[{
                            **metadata,
                            "section": header,
                            "part": j
                        }]
                    )
                    logger.debug(
                        f"Added chunk {j} of section '{header}' "
                        f"with ID: {doc_id}"
                    )
            
            # Move file to done folder
            done_path = os.path.join(DONE_FOLDER, filename)
            shutil.move(file_path, done_path)
            logger.info(f"Moved {filename} to done folder")
            
            # Add to processed files tracking
            add_processed_file(filename, file_path, content_hash)
            logger.info(f"Added {filename} to processed files tracking")
            
            logger.success(f"Successfully ingested: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to ingest {file_path}: {e}")


if __name__ == "__main__":
    # Create required directories
    os.makedirs(WATCH_FOLDER, exist_ok=True)
    os.makedirs(DONE_FOLDER, exist_ok=True)
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    
    # Configure logging
    logger.add(
        f"{LOGS_FOLDER}/ingest.log",
        rotation="1 week",
        retention="4 weeks",
        level="INFO"
    )
    
    # Start document watcher
    logger.info(f"Starting document watcher for folder: {WATCH_FOLDER}")
    event_handler = DocumentHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_FOLDER, recursive=False)
    observer.start()
    
    logger.info(f"Watching folder: {WATCH_FOLDER} for new documents...")
    try:
        while True:
            observer.join(1)  # Check every second
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Shutting down document watcher.")
    observer.join()
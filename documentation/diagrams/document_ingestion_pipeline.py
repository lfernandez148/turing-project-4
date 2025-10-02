#!/usr/bin/env python3
"""
Document Ingestion Pipeline Diagram for Campaign Performance Assistant
Updated to reflect current pipeline and simplified architecture
"""

from diagrams import Diagram, Cluster
from diagrams.programming.language import Python
from diagrams.generic.storage import Storage

# Create the diagram
with Diagram("Campaign Performance Assistant - Document Ingestion Pipeline", 
             show=False, 
             filename="document_ingestion_pipeline",
             direction="LR"):  # Left-Right for clear pipeline flow
    
    # Document Sources (leftmost)
    with Cluster("Document Sources"):
        doc_types = Storage("""Document Types:
• PDF Files
• HTML Files  
• DOCX Files""")
    
    # Processing Pipeline (center)
    with Cluster("Processing Pipeline"):
        file_monitor = Python("File Monitor")
        doc_loaders = Python("Document Loaders")
        text_processor = Python("Text Chunking")
    
    # AI & Storage (center-right)
    with Cluster("AI & Storage"):
        embeddings = Python("Embeddings")
        chroma = Storage("ChromaDB")
    
    # System Services (rightmost)
    with Cluster("System Services"):
        file_mgmt = Storage("Files Done")
    
    # Simplified Pipeline Flow
    doc_types >> file_monitor
    file_monitor >> doc_loaders
    doc_loaders >> text_processor
    text_processor >> embeddings
    embeddings >> chroma
    
    # File management
    doc_loaders >> file_mgmt 
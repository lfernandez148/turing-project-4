#!/usr/bin/env python3
"""
System Architecture Diagram for Campaign Performance Assistant
"""

from diagrams import Diagram, Cluster
from diagrams.programming.framework import FastAPI
from diagrams.programming.language import Python
from diagrams.firebase.base import Firebase
from diagrams.generic.compute import Rack
from diagrams.generic.storage import Storage
from diagrams.generic.database import SQL
from diagrams.onprem.client import Client
from diagrams.generic.device import Mobile
from diagrams.programming.flowchart import Decision

# Create the diagram
with Diagram("Campaign Performance AI Assistant - System Architecture", 
             show=False, 
             filename="system_architecture",
             direction="TB"):  # Top-Bottom with Frontend at top, rest horizontal
    
    # Frontend Layer
    with Cluster("Frontend"):
        streamlit = Python("Streamlit UI")
        mobile = Mobile("Mobile Access")
        client = Client("Web Browser")
    
    # Backend Services
    with Cluster("Backend"):
        # AI/Agents Sub-cluster
        with Cluster("AI/Agents"):
            langgraph = Python("LangGraph")
            langchain = Python("LangChain")
            llm = Python("OpenAI/LM Studio")
            tool_selection = Python("Tool Selection")
            response_gen = Python("Response Generator")
        
        # Vector DB Sub-cluster
        with Cluster("Vector DB"):
            doc_ingestion = Python("Document Loader")
            chroma = Storage("ChromaDB")
        
        # API Sub-cluster
        with Cluster("API"):
            fastapi = FastAPI("FastAPI")
        
        # Data Storage
        sqlite = SQL("SQLite DB")
        
        # System Services
        logging = Python("Logging")
        memory_mgmt = Python("Memory Mgmt")
        token_tracking = Python("Token Tracking")
    
    # Authentication
    with Cluster("Authentication"):
        firebase_auth = Firebase("Firebase Auth")
    
    # Frontend to External Authentication
    streamlit >> firebase_auth
    mobile >> firebase_auth
    client >> firebase_auth
    
    # External Auth to Backend AI Processing
    firebase_auth >> langgraph
    
    # Backend AI Agent workflow
    langgraph >> tool_selection
    tool_selection >> response_gen
    
    # AI to Backend services
    langgraph >> langchain
    langchain >> llm
    langchain >> fastapi
    
    # Backend data flow
    data_retriever >> fastapi
    data_retriever >> chroma
    fastapi >> sqlite
    
    # Document processing in backend
    doc_ingestion >> chroma 
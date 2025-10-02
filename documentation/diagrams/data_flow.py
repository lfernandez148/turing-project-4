#!/usr/bin/env python3
"""
Data Flow Diagram for Campaign Performance Assistant
Updated to reflect Firebase Auth, LangGraph, Token Tracking, Memory Management, and removal of Grafana Loki
"""

from diagrams import Diagram, Cluster
from diagrams.programming.language import Python
from diagrams.programming.framework import FastAPI
from diagrams.generic.database import SQL
from diagrams.generic.storage import Storage
from diagrams.firebase.base import Firebase
from diagrams.onprem.client import Client
from diagrams.generic.compute import Rack
from diagrams.programming.flowchart import Decision

# Create the diagram
with Diagram("Campaign Performance Assistant - Data Flow", 
             show=False, 
             filename="data_flow",
             direction="LR"):  # Left-Right for better horizontal flow
    
    # Frontend Layer (very left)
    with Cluster("Frontend Layer"):
        streamlit = Python("Streamlit UI")
    
    # User Input (positioned at the very left, connecting to frontend)
    user = Client("User Query")
    
    # Authentication Layer (right of Frontend Layer)
    with Cluster("Authentication"):
        firebase_auth = Firebase("Firebase Auth")
    
    # AI Agent Layer (center, spread horizontally)
    with Cluster("AI Agent Layer"):
        # Top row of AI components
        langgraph = Python("LangGraph")
        query_analyzer = Decision("Query Analyzer")
        langchain = Python("LangChain")
        
        # Bottom row of AI components  
        llm = Python("OpenAI/LM Studio")
        tools = Python("LLM Tools")
        response_gen = Python("Response Generator")
    
    # Data Sources (right side)
    with Cluster("Data Sources"):
        fastapi = FastAPI("FastAPI")
    
    # Data Flow
    user >> streamlit
    streamlit >> firebase_auth
    firebase_auth >> langgraph
    
    # AI Agent workflow
    langgraph >> query_analyzer
    query_analyzer >> langchain
    langchain >> llm
    langchain >> tools
    
    # Data access
    tools >> fastapi
    
    # Response Flow
    llm >> response_gen
    response_gen >> streamlit
    tools >> streamlit
    fastapi >> streamlit 
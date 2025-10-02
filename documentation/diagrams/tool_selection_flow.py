#!/usr/bin/env python3
"""
Tool Selection Flow Diagram for Campaign Performance Assistant
Updated to reflect LangGraph agent architecture and current tools
"""

from diagrams import Diagram, Cluster
from diagrams.programming.language import Python
from diagrams.programming.framework import FastAPI
from diagrams.generic.storage import Storage
from diagrams.onprem.client import Client
from diagrams.firebase.base import Firebase
from diagrams.programming.flowchart import Decision

# Create the diagram
with Diagram("Campaign Performance Assistant - Tool Selection Flow", 
             show=False, 
             filename="tool_selection_flow",
             direction="LR"):  # Left-Right for better workflow visualization
    
    # User Input (leftmost)
    user = Client("User Query")
    
    # Frontend
    with Cluster("Frontend"):
        streamlit = Python("Streamlit UI")
    
    # LangGraph Agent System (center)
    with Cluster("LangGraph Agent System"):
        langgraph = Python("LangGraph")
        query_analyzer = Decision("Query Analyzer")
        tool_selector = Python("Tool Selector")
    
    # Available Tools (listed as text with better formatting)
    with Cluster("Available Tools"):
        tools_list = Python("""Tool Library:
• search_campaign_documents       
• get_campaign_by_id             
• get_top_campaigns_by_metric    
• get_campaigns_by_topic         
• get_campaigns_by_segment       
• get_campaign_summary_stats     
• compare_campaigns_by_id        
• create_campaign_chart          """)
    
    # Data Sources (simplified)
    with Cluster("Data Sources"):
        fastapi = FastAPI("FastAPI")
        chroma = Storage("ChromaDB")
    
    # Response Generation (simplified)
    with Cluster("Response Generation"):
        response_gen = Python("Response Generator")
    
    # Simplified LangGraph Flow
    user >> streamlit
    streamlit >> langgraph
    
    # LangGraph Agent Workflow
    langgraph >> query_analyzer
    query_analyzer >> tool_selector
    
    # Tool Selection (simplified - single connection to tool library)
    tool_selector >> tools_list
    
    # Tools access data sources
    tools_list >> chroma
    tools_list >> fastapi
    
    # Response flow back to frontend
    tools_list >> response_gen
    response_gen >> streamlit 
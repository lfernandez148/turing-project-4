#!/usr/bin/env python3
"""
API Endpoints Diagram for Campaign Performance Assistant
Updated to reflect current endpoints and simplified architecture
"""

from diagrams import Diagram, Cluster
from diagrams.programming.framework import FastAPI
from diagrams.programming.language import Python
from diagrams.onprem.client import Client

# Create the diagram
with Diagram("Campaign Performance Assistant - API Endpoints", 
             show=False, 
             filename="api_endpoints",
             direction="TB"):  # Top-Bottom for better horizontal endpoint layout
    
    # Client (leftmost)
    client = Client("API Client")
    
    # FastAPI Application (center)
    with Cluster("FastAPI Application"):
        fastapi = FastAPI("FastAPI Server")
    
    # API Endpoints (organized by category)
    with Cluster("System Endpoints"):
        root_endpoint = Python("GET /")
        health_endpoint = Python("GET /health")
        auth_verify = Python("GET /auth/verify")
    
    with Cluster("Campaign Endpoints"):
        campaign_endpoints = Python("""Campaigns:
GET
/campaigns/{id}
/campaigns/all
/campaigns/summary
/campaigns/top/{metric}
/campaigns/topic/{topic}
/campaigns/segment/{segment}
/campaigns/compare/{id1}/{id2}
""")
    
    with Cluster("Documentation Endpoints"):
        swagger_docs = Python("GET /docs")
        redoc_docs = Python("GET /redoc")
    
    # Security & Data (simplified)
    with Cluster("Backend Services"):
        security = Python("""
API Key Auth 
+ 
Rate Limiting
""")
        data_layer = Python("SQLite Database")
    
    # Simplified Flow Connections
    client >> fastapi
    
    # FastAPI serves individual endpoints
    fastapi >> root_endpoint
    fastapi >> health_endpoint
    fastapi >> auth_verify
    fastapi >> campaign_endpoints
    fastapi >> swagger_docs
    fastapi >> redoc_docs
    
    # Security and data access
    campaign_endpoints >> security
    security >> data_layer 
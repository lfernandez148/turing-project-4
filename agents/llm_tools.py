# llm_tools.py
from langchain.tools import tool
from loguru import logger
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb
import requests
from app.chart_utils import get_available_charts
import os
from dotenv import load_dotenv
import httpx

from databases.chroma_config import get_chroma_client  # noqa: E402
from chromadb.api.types import EmbeddingFunction, Documents

# Load environment variables
load_dotenv()

# FastAPI configuration from environment
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "sk-test-1234567890abcdef")
WEB_BASE_URL = os.getenv("WEB_BASE_URL", "http://localhost:8080")

# ChromaDB configuration
CHROMA_HOST = os.getenv("CHROMA_SERVER_HOST", "localhost")
CHROMA_PORT = os.getenv("CHROMA_SERVER_HTTP_PORT", "8030")

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


def get_chroma_client():
    """Get a configured ChromaDB client for the containerized instance."""
    logger.info(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
    
    try:
        # Initialize client for containerized ChromaDB
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            ssl=False
        )
        
        logger.info("Successfully connected to ChromaDB")
        return client
        
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {e}")
        raise


# Initialize ChromaDB client
try:
    chroma_client = get_chroma_client()
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
    raise


def make_api_request(endpoint: str, method: str = "GET") -> dict:
    """Helper function to make API requests with consistent error handling."""
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        else:
            # Handle other methods if needed
            return {"success": False, "error": "Method not supported"}
            
        if not response.ok:
            error_detail = (
                response.json().get('detail', 'Unknown error')
                if response.content else 'API error'
            )
            return {
                "success": False,
                "error": error_detail,
                "status_code": response.status_code
            }
            
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool("search_documents")
def search_documents(query: str) -> str:
    """Search for campaign information in uploaded documents.
    Use this for executive summaries, performance insights, and recommendations
    from uploaded documents."""
    logger.info("Searching campaign documents")
    
    # Query ChromaDB collection
    try:

        logger.info("Before calling get_chroma_client()")
        client = get_chroma_client()
        logger.info("After A calling get_chroma_client()")
        collection = client.get_or_create_collection(
            name="campaign_reports",
            embedding_function=adapted_embeddings,
            metadata={
                "description": (
                    "Campaign performance reports and documentation"
                )
            }
        )
        logger.info("After B calling get_chroma_client()")

        results = collection.query(
            query_texts=[query],
            n_results=3,
            include=['documents', 'metadatas']
        )
        
        logger.info("After C calling get_chroma_client()")

    except Exception as e:
        logger.error(f"ChromaDB search failed: {e}")
        return f"Error: Document search failed - {str(e)}"
        
    if not results['documents'][0]:
        return "No relevant documents found."
    
    # Filter and format results
    filtered_results = []
    for doc in results['documents'][0]:  # documents is a list of lists
        if doc.strip():
            filtered_results.append(doc.strip())

    if not filtered_results:
        logger.info("No documents met similarity threshold")
        return {
            "type": "text",
            "message": "No relevant campaign documents found.",
            "source": "Vector Database (no relevant documents)"
        }
    
    logger.info(f"Found {len(filtered_results)} relevant documents")
    context = "\n".join(filtered_results)
    
    # Create source information
    sources = []
    for metadata in results['metadatas'][0]:  # metadatas is a list of lists
        source = "Unknown document"
        if metadata:
            source = metadata.get('source', 'Unknown document')
        sources.append(source)
    
    # Deduplicate sources
    unique_sources = list(set(sources))
    source_info = f"Vector Database ({', '.join(unique_sources)})"
    logger.info(f"source_info: {source_info}")
    
    return {
        "type": "text",
        "message": f"Found relevant campaign information:\n\n{context}",
        "source": source_info
    }


@tool
def get_campaign_by_id(campaign_id: int) -> dict:
    """Get structured campaign data from the database for a specific campaign ID.
    Use this when users ask for specific metrics, numbers, or structured data 
    about a campaign (opens, clicks, conversion rates, audience size, etc.).
    Examples: "campaign 101 metrics", "how many opens did campaign 102 get", 
    "what is the conversion rate for campaign 103", "audience size for campaign 104"
    """
    logger.info(f"Getting campaign details for ID: {campaign_id}")
    
    result = make_api_request(f"/campaigns/{campaign_id}")
    
    if result["success"]:
        campaign = result["data"]
        return {
            "type": "text",
            "message": f"""
Campaign {campaign_id} Details:
- Topic: {campaign['campaign_topic']}
- Date: {campaign['campaign_date']}
- Customer Segment: {campaign['customer_segment']}
- Audience Size: {campaign['audience_size']:,}
- Sent: {campaign['sent']:,}
- Opens: {campaign['opens']:,}
- Clicks: {campaign['clicks']:,}
- Conversions: {campaign['conversions']:,}
- Open Rate: {campaign['open_rate']}%
- Click Rate: {campaign['click_rate']}%
- Conversion Rate: {campaign['conversion_rate']}%
            """.strip(),
            "source": "Campaign Database (campaigns table)"
        }
    else:
        return {
            "type": "text",
            "message": f"Campaign {campaign_id} not found: {result['error']}",
            "source": "Campaign Database (API error)"
        }


@tool
def get_top_campaigns_by_metric(metric: str = '', limit: int = 5) -> dict:
    """Get top performing campaigns by a specific metric and return as a table.
    Use this when users ask for "top campaigns", "best performing", "rankings", 
    "table of campaigns", or want to compare campaigns by a specific metric.
    Examples: "top 5 campaigns by conversion rate", "best campaigns by opens",
    "show me the top campaigns", "rank campaigns by clicks", 
    "show me a table of top 10 campaigns by conversion rate",
    "table of top campaigns by opens", "top campaigns table"
    """
    if not metric:
        metric = 'opens'
    logger.info(f"Getting top {limit} campaigns by {metric}")
    
    result = make_api_request(f"/campaigns/top/{metric}?limit={limit}")
    
    if result["success"]:
        data = result["data"]
        table_result = {
            "type": "table",
            "columns": ["campaign_id", "campaign_topic", "customer_segment", 
                       "conversion_rate"],
            "rows": [
                {
                    "campaign_id": c["campaign_id"],
                    "campaign_topic": c["campaign_topic"],
                    "customer_segment": c["customer_segment"],
                    "conversion_rate": c["conversion_rate"],
                }
                for c in data["campaigns"]
            ],
            "message": f"Top {data['limit']} campaigns by {data['metric']}:",
            "source": "Campaign Database (campaigns table)"
        }
        logger.info(f"Returning table dict: {table_result}")
        return table_result
    else:
        return {
            "type": "error",
            "message": f"Error: {result['error']}",
            "source": "Campaign Database (API error)"
        }


@tool
def get_campaigns_by_topic(topic: str) -> dict:
    """Get all campaigns for a specific topic from the database.
    Use this when users ask about campaigns by topic, theme, or subject.
    Examples: "campaigns about loyalty", "fitness campaigns", "promotional campaigns",
    "show me all campaigns for topic X"
    """
    logger.info(f"Getting campaigns for topic: {topic}")
    
    result = make_api_request(f"/campaigns/topic/{topic}")
    
    if result["success"]:
        data = result["data"]
        message = f"Campaigns for topic '{topic}' ({data['count']} found):\n\n"
        for campaign in data['campaigns']:
            message += f"Campaign {campaign['campaign_id']}:\n"
            message += f"  Segment: {campaign['customer_segment']}\n"
            message += f"  Conversion Rate: {campaign['conversion_rate']}%\n"
            message += f"  Opens: {campaign['opens']:,}, Clicks: {campaign['clicks']:,}, Conversions: {campaign['conversions']:,}\n\n"
        return {
            "type": "text",
            "message": message.strip(),
            "source": "Campaign Database (campaigns table)"
        }
    else:
        return {
            "type": "text",
            "message": f"Error retrieving campaigns for topic '{topic}': {result['error']}",
            "source": "Campaign Database (API error)"
        }


@tool
def get_campaigns_by_segment(segment: str) -> dict:
    """Get all campaigns for a specific customer segment from the database.
    Use this when users ask about campaigns by audience, customer type, or segment.
    Examples: "campaigns for fitness enthusiasts", "retail customer campaigns",
    "previous customer campaigns", "show me campaigns for segment X"
    """
    logger.info(f"Getting campaigns for segment: {segment}")
    
    result = make_api_request(f"/campaigns/segment/{segment}")
    
    if result["success"]:
        data = result["data"]
        message = f"Campaigns for segment '{segment}' ({data['count']} found):\n\n"
        for campaign in data['campaigns']:
            message += f"Campaign {campaign['campaign_id']} ({campaign['campaign_date']}):\n"
            message += f"  Topic: {campaign['campaign_topic']}\n"
            message += f"  Conversion Rate: {campaign['conversion_rate']}%\n"
            message += f"  Opens: {campaign['opens']:,}, Clicks: {campaign['clicks']:,}, Conversions: {campaign['conversions']:,}\n\n"
        return {
            "type": "text",
            "message": message.strip(),
            "source": "Campaign Database (campaigns table)"
        }
    else:
        return {
            "type": "text",
            "message": f"Error retrieving campaigns for segment '{segment}': {result['error']}",
            "source": "Campaign Database (API error)"
        }


@tool
def get_campaign_summary_stats() -> dict:
    """Get summary statistics for all campaigns from the database.
    Use this when users ask for overall statistics, averages, totals, or summary data.
    Examples: "summary statistics", "overall campaign performance", "average metrics",
    "total campaign stats", "how are all campaigns performing"
    """
    logger.info("Getting campaign summary statistics")
    
    result = make_api_request("/campaigns/summary")
    
    if result["success"]:
        stats = result["data"]
        return {
            "type": "text",
            "message": f"""
Campaign Summary Statistics:
- Total Campaigns: {stats['total_campaigns']:,}
- Average Conversion Rate: {stats['average_conversion_rate']}%
- Average Open Rate: {stats['average_open_rate']}%
- Average Click Rate: {stats['average_click_rate']}%
- Total Conversions: {stats['total_conversions']:,}
- Total Opens: {stats['total_opens']:,}
- Total Clicks: {stats['total_clicks']:,}
            """.strip(),
            "source": "Campaign Database (campaigns table)"
        }
    else:
        return {
            "type": "text",
            "message": f"Error retrieving summary statistics: {result['error']}",
            "source": "Campaign Database (API error)"
        }


@tool
def compare_campaigns_by_id(campaign_id1: int, campaign_id2: int) -> dict:
    """Compare two campaigns side by side from the database.
    Use this when users want to compare two specific campaigns or see differences.
    Examples: "compare campaign 101 and 102", "campaign 101 vs 102", 
    "how do campaigns 103 and 104 compare", "difference between campaign X and Y"
    """
    logger.info(f"Comparing campaigns {campaign_id1} and {campaign_id2}")
    
    result = make_api_request(f"/campaigns/compare/{campaign_id1}/{campaign_id2}")
    
    if result["success"]:
        data = result["data"]
        c1, c2 = data['campaign_1'], data['campaign_2']
        
        return {
            "type": "text",
            "message": f"""
Campaign Comparison:
{campaign_id1} vs {campaign_id2}

Campaign {c1['campaign_id']} ({c1['campaign_topic']}):
  Segment: {c1['customer_segment']}
  Conversion Rate: {c1['conversion_rate']}%
  Open Rate: {c1['open_rate']}%
  Click Rate: {c1['click_rate']}%
  Opens: {c1['opens']:,}, Clicks: {c1['clicks']:,}, Conversions: {c1['conversions']:,}
  Audience: {c1['audience_size']:,}

Campaign {c2['campaign_id']} ({c2['campaign_topic']}):
  Segment: {c2['customer_segment']}
  Conversion Rate: {c2['conversion_rate']}%
  Open Rate: {c2['open_rate']}%
  Click Rate: {c2['click_rate']}%
  Opens: {c2['opens']:,}, Clicks: {c2['clicks']:,}, Conversions: {c2['conversions']:,}
  Audience: {c2['audience_size']:,}
            """.strip(),
            "source": "Campaign Database (campaigns table)"
        }
    else:
        return {
            "type": "text",
            "message": f"Error comparing campaigns: {result['error']}",
            "source": "Campaign Database (API error)"
        }


@tool
def create_campaign_chart(chart_type: str) -> dict:
    """Create and display a chart for campaign data visualization.
    
    Available chart types:
    - audience_by_topic: Bar chart showing audience volume by campaign topic
    - conversion_rate: Bar chart showing top campaigns by conversion rate
    - segment_performance: Bar chart showing performance by customer segment
    - trends: Line chart showing performance trends over time
    """
    logger.info(f"Creating chart: {chart_type}")
    
    available_charts = get_available_charts()
    if chart_type not in available_charts:
        return {
            "type": "error",
            "message": f"Invalid chart type. Available types: {', '.join(available_charts)}",
            "source": "Chart Generation Tool"
        }
    # Do NOT call display_chart here. Just return the chart type and message.
    return {
        "type": "chart",
        "chart_type": chart_type,
        "message": f"📊 {chart_type.replace('_', ' ').title()}",
        "source": "Chart Generation Tool (Plotly + Campaign Database)"
    }


@tool
def get_campaign_images(campaign_id: int) -> dict:
    """Get campaign images or assets from web server that has images.
    Use this when users ask for get images or assets related to a specific campaign.
    Examples: "images for campaign 101", "assets for campaign 102", 
    "what images or assets are available for campaign 103"
    """
    logger.info(f"Fetching images for campaign ID: {campaign_id}")

    image_url = f"{WEB_BASE_URL}/images/public/campaign-{campaign_id}.jpg"
    headers = {"Authorization": "Bearer protected-access-key"}
    
    with httpx.Client() as client:
        try:
            response = client.get(image_url, headers=headers)
            response.raise_for_status()

            return {
                "type": "image",
                "image_url": image_url, 
                "message": f"Images for campaign {campaign_id}.",
                "source": "Images"
            }

        except Exception as e:
            logger.error(f"External request error: {e}")
            return {
                "type": "image",
                "image_url": "",
                "message": f"No images found for campaign {campaign_id}.",
                "source": "Images"
            }


# List of all available tools for the LLM
LLM_TOOLS = [
    search_documents,
    get_campaign_by_id,
    get_top_campaigns_by_metric,
    get_campaigns_by_topic,
    get_campaigns_by_segment,
    get_campaign_summary_stats,
    compare_campaigns_by_id,
    create_campaign_chart,
    get_campaign_images
]
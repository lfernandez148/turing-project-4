# chatbot.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any
from loguru import logger
from dotenv import load_dotenv
from pydantic import BaseModel
from .llm_tools import LLM_TOOLS
from .token_tracking import TokenTracker
from .util_memory import MemoryManager, load_conversation_history
from .util_deepseek import (
    parse_deepseek_tool_calls,
    clean_deepseek_content,
    process_deepseek_response
)
from databases.sqlite_config import SQLiteConfig
import os
import ast
import sqlite3
import sys

# Add parent directory to path for centralized logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


class ChatbotResponse(BaseModel):
    """Pydantic model for standardized chatbot responses."""
    type: str
    message: str
    source: Optional[str] = ""
    data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create_text_response(
        cls, message: str, source: str = ""
    ) -> "ChatbotResponse":
        """Create a text response."""
        return cls(type="text", message=message, source=source)
    
    @classmethod
    def create_table_response(
        cls,
        message: str = "Here are the results",
        data: Dict[str, Any] = None
    ) -> "ChatbotResponse":
        """Create a table response."""
        return cls(type="table", message=message, data=data)
    
    @classmethod
    def create_chart_response(
        cls,
        message: str = "Here are the results",
        data: Dict[str, Any] = None
    ) -> "ChatbotResponse":
        """Create a chart response."""
        return cls(type="chart", message=message, data=data)

    @classmethod
    def create_image_response(
        cls,
        message: str = "Here are the results",
        data: Dict[str, Any] = None
    ) -> "ChatbotResponse":
        """Create a image response."""
        return cls(type="image", message=message, data=data)

    @classmethod
    def create_error_response(
        cls,
        message: str = ("I couldn't find relevant campaign information. "
                        "Please try rephrasing or ask about a specific "
                        "campaign, metric, topic or segment!")
    ) -> "ChatbotResponse":
        """Create an error response."""
        return cls(type="text", message=message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        result = {
            "type": self.type,
            "message": self.message
        }
        if self.source:
            result["source"] = self.source
        if self.data is not None:
            result["data"] = self.data
        return result


# Configuration: Choose between OpenAI and LM Studio
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234")

# LangSmith Configuration
if os.getenv("LANGCHAIN_TRACING_V2").lower() == "true":
    logger.info("LangSmith enabled")
    os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "campaign-performance-assistant")
    logger.info("LangSmith tracing enabled")
else:
    logger.info("LangSmith disabled")

# Initialize LLM based on configuration
if USE_LOCAL_LLM:
    logger.info("Using local LLM via LM Studio")
    llm = ChatOpenAI(
        base_url=f"{LM_STUDIO_URL}/v1",
        api_key="not-needed",  # LM Studio doesn't require API key
        temperature=0,
        model="local-model"  # This can be any name since LM Studio ignores it
    )
else:
    logger.info("Using OpenAI")
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-3.5-turbo"  # or any other OpenAI model
    )

# LangGraph checkpointer
db_path = SQLiteConfig.get_conversations_db()
conn = sqlite3.connect(db_path, check_same_thread=False)
checkpointer = SqliteSaver(conn)

# Initialize token tracker
token_tracker = TokenTracker(conn)

# Initialize memory manager
memory_manager = MemoryManager(checkpointer, conn)


def message_reducer(existing: Sequence[BaseMessage], new: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    """Keep only the last n messages to prevent unlimited growth."""

    # Combine existing and new messages
    all_messages = list(existing) + list(new)

    # Keep only the last n messages
    n = 10
    last_n_messages = all_messages[-n:]
    valid_messages = []
    add_all_the_rest = False
    for msg in last_n_messages:
        if isinstance(msg, HumanMessage) or add_all_the_rest: # If it's a human message or we already decided to add all
            add_all_the_rest = True
            valid_messages.append(msg)
    
    return valid_messages


# Define the state for the agent
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], message_reducer]
    data: dict


def chat_query_with_custom_agent(
    user_query: str, thread_id: str = "default", user_id: str = None
) -> Dict[str, Any]:
    """Use custom LangGraph agent with SQLite checkpointer."""
    logger.info(
        f"Processing query with LangGraph agent: {user_query} "
        f"[Thread: {thread_id}, User: {user_id}]"
    )
    
    # Track tokens - simple counters
    total_input_tokens = 0
    total_output_tokens = 0
    
    try:
        # Use all tools from llm_tools
        all_tools = LLM_TOOLS
        
        # Create a tool lookup dictionary
        tools_dict = {tool.name: tool for tool in all_tools}
        
        # Bind tools to the LLM
        llm_with_tools = llm.bind_tools(all_tools)
        
        # Define the agent node with Deepseek tool call parsing
        def call_model(state):
            nonlocal total_input_tokens, total_output_tokens
            messages = state["messages"]
            logger.info(f"\n\n messages:\n {messages}")

            data = state.get("data", {})
            
            # Log conversation context for debugging
            logger.info(
                f"call_model() - Processing {len(messages)} messages "
                f"for User: {user_id}, Thread: {thread_id}"
            )
            logger.info(f"Message types: {[type(msg).__name__ for msg in messages]}")
            logger.info(f"Data: {data}")
            
            response = llm_with_tools.invoke(messages)
            
            # Check if this is a Deepseek model response with custom tool format
            if hasattr(response, 'content') and '[TOOL_REQUEST]' in response.content:
                logger.info("Detected Deepseek tool call format, parsing...")
                logger.info(f"Original content: {response.content}")
                
                # Parse Deepseek's tool calls
                tool_calls = parse_deepseek_tool_calls(response.content)
                
                if tool_calls:
                    logger.info(f"Parsed {len(tool_calls)} tool calls: {tool_calls}")
                    
                    # Clean the content by removing tool request markers and think blocks
                    cleaned_content = clean_deepseek_content(response.content)
                    
                    # Create a new message with proper tool calls and cleaned content
                    response = AIMessage(
                        content=cleaned_content,
                        tool_calls=tool_calls
                    )
                    logger.info(f"Created new message with tool calls: {response.tool_calls}")
            
            # Also clean content for responses without tool calls but with think blocks or tool results
            elif hasattr(response, 'content') and ('<think>' in response.content or '[TOOL_RESULT]' in response.content):
                logger.info("Detected Deepseek thinking blocks or tool results, cleaning...")
                cleaned_content = clean_deepseek_content(response.content)
                response = AIMessage(content=cleaned_content)
                logger.info("Cleaned thinking blocks and tool results from content")
            
            # Simple token tracking - extract from response if available
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                total_input_tokens += usage.get('input_tokens', 0)
                total_output_tokens += usage.get('output_tokens', 0)
                logger.info(f"Tokens - Input: {usage.get('input_tokens', 0)}, Output: {usage.get('output_tokens', 0)}")
            
            return {"messages": [response]}
        
        # Define the tool execution node
        def call_tools(state):
            logger.info(f"call_tools() - Thread: {thread_id}")
            messages = state["messages"]
            data = state.get("data", {})
            last_message = messages[-1]

            # Execute tool calls
            tool_messages = []
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call["args"]
                
                if tool_name in tools_dict:
                    try:
                        response = tools_dict[tool_name].invoke(tool_input)
                        tool_message = ToolMessage(
                            content=str(response),
                            name=tool_name,
                            tool_call_id=tool_call["id"]
                        )
                        tool_messages.append(tool_message)

                        if isinstance(response, dict) and response.get('type') in ['table']:
                            logger.info(f"response: is table")
                            data = response

                        if isinstance(response, dict) and response.get('type') in ['chart']:
                            logger.info(f"response: is chart")
                            data = response

                        if isinstance(response, dict) and response.get('type') in ['image']:
                            logger.info(f"response: is image")
                            image_url = response.get("image_url", "")
                            if image_url:
                                data = response

                    except Exception as e:
                        error_message = ToolMessage(
                            content=f"Error executing tool {tool_name}: {str(e)}",
                            name=tool_name,
                            tool_call_id=tool_call["id"]
                        )
                        tool_messages.append(error_message)
                else:
                    error_message = ToolMessage(
                        content=f"Unknown tool: {tool_name}",
                        name=tool_name,
                        tool_call_id=tool_call["id"]
                    )
                    tool_messages.append(error_message)
            
            return {
                "messages": tool_messages,
                "data": data
            }
        
        # Define the condition to decide next step
        def should_continue(state):
            messages = state["messages"]
            last_message = messages[-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            return END
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", call_tools)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                END: END
            }
        )
        
        # Add edge from tools back to agent
        workflow.add_edge("tools", "agent")

        # Compile the graph with SQLite checkpointer
        app = workflow.compile(checkpointer=checkpointer)
        
        # Enhanced thread config with user info
        thread_config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id or "anonymous"
            }
        }
        
        logger.info(f"Thread config: {thread_config}")
        
        # Load conversation history from SQLite and build initial messages
        conversation_history = load_conversation_history(token_tracker, user_id or "anonymous", thread_id, limit=10)
        
        # Debug: Log what conversation history we loaded
        if conversation_history:
            logger.info(f"Loaded conversation history:")
            for i, msg in enumerate(conversation_history):
                logger.info(f"  {i+1}. {type(msg).__name__}: {msg.content[:100]}...")
        else:
            logger.info("No conversation history found")
        
        # Initialize with priming sequence
        initial_messages = [
            SystemMessage(content=(
                "You are ONLY a Campaign Analytics Assistant. "
                "You MUST reject ANY non-campaign queries immediately."
            )),
            # Prime with example exchange
            HumanMessage(content="Tell me a joke"),
            AIMessage(content=(
                "I am a Campaign Analytics Assistant. I can only provide "
                "information about campaign performance data."
            )),
            HumanMessage(content="How are you today?"),
            AIMessage(content=(
                "I am a Campaign Analytics Assistant. I can only provide "
                "information about campaign performance data."
            )),
            # Reinforce with strict system message
            SystemMessage(content=(
                "You are a Campaign Performance Assistant with a strict focus on campaign analytics data. "
                "Your responses MUST be based ONLY on: "
                "1. Information from previous conversations in our chat history "
                "2. Data retrieved through campaign data tools "
                "3. Direct campaign performance metrics and analytics "
                
                "STRICT RULES: "
                "- NEVER create, invent, or make up any information "
                "- NEVER tell jokes or engage in casual conversation "
                "- NEVER provide responses about topics outside of campaign performance "
                "- If information is not in the chat history or available through tools, respond ONLY with: 'I can only provide information about campaign performance based on available data.' "
                
                "WORKFLOW: "
                "1. First, check conversation history for relevant information "
                "2. If history doesn't contain the answer, use campaign data tools "
                "3. If neither source has the information, provide the standard response "
                
                "Remember: You are an analytics tool, not a conversational AI. "
                "Stay focused only on campaign performance data and metrics."
            ))
        ]
                
        # Add conversation history after system messages
        initial_messages.extend(conversation_history)
        
        # Add current user query
        initial_messages.append(HumanMessage(content=user_query))
        
        logger.info(f"Initial messages count: {len(initial_messages)} (including {len(conversation_history)} from history)")
        logger.info(f"Initial messages:\n{initial_messages}")
        
        # Run the agent with populated conversation history
        logger.info("\n Before: app.invoke with populated history")
        result = app.invoke(
            {"messages": initial_messages, "data": {}}, 
            config=thread_config  # This enables session persistence
        )
        logger.info("\n After: app.invoke with populated history")

        # Save token usage if we tracked any tokens
        if total_input_tokens > 0 or total_output_tokens > 0:
            token_tracker.save_token_usage(
                user_id=user_id or "anonymous",
                thread_id=thread_id,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens
            )

        # Get the final AI message
        final_message = result["messages"][-1]
        final_message_content = final_message.content
        logger.info(f"Final message content: {final_message_content}")

        # If agent explicitly says it doesn't have information, return that
        if "I don't have any information on that." in final_message_content:
            return ChatbotResponse.create_text_response(
                message=final_message_content
            ).to_dict()

        data = result["data"]

        # Check if we got a table from tools
        if isinstance(data, dict) and data.get('type') == 'table':
            logger.info("final_answer: is table")
            return ChatbotResponse.create_table_response(
                message="Here are the results",
                data=data
            ).to_dict()
        
        # Check if we got a chart from tools
        if isinstance(data, dict) and data.get('type') == 'chart':
            logger.info("final_answer: is chart")
            return ChatbotResponse.create_chart_response(
                message="Here are the results",
                data=data
            ).to_dict()

        # Check if we got a chart from tools
        if isinstance(data, dict) and data.get('type') == 'image':
            logger.info("final_answer: is image")
            return ChatbotResponse.create_image_response(
                message="Here are the results",
                data=data
            ).to_dict()

        # Check if tools were used and if they provided meaningful data
        tool_messages = [msg for msg in result["messages"] if isinstance(msg, ToolMessage)]
        
        if tool_messages:
            # Tools were used - check if they provided meaningful data
            meaningful_data = False
            source_info = None
            
            for tool_msg in tool_messages:
                try:
                    tool_content_dict = ast.literal_eval(tool_msg.content)
                    if "No relevant campaign documents found" not in tool_msg.content:
                        if "not found" not in tool_msg.content.lower() and "error" not in tool_msg.content.lower():
                            meaningful_data = True
                            source_info = tool_content_dict.get('source')
                            break
                except (ValueError, SyntaxError):
                    # If content isn't a valid Python literal, check as string
                    if "No relevant campaign documents found" not in tool_msg.content:
                        if "not found" not in tool_msg.content.lower() and "error" not in tool_msg.content.lower():
                            meaningful_data = True
                            break
            
            # If tools were used but didn't find meaningful data, update the message
            if not meaningful_data:
                final_message_content = (
                    "I couldn't find relevant campaign information for your question. "
                    "Please try rephrasing or ask about a specific campaign, metric, topic or segment!"
                )
                source_info = None
        else:
            # No tools were used - agent answered from conversation history or knowledge
            # Keep the agent's response as-is
            logger.info("No tools used - agent responded from conversation history or knowledge")
            source_info = None
        
        return ChatbotResponse.create_text_response(
            message=final_message_content,
            source=source_info if source_info else None
        ).to_dict()
        
    except Exception as e:
        logger.error(f"Error in custom LangGraph agent: {e}")
        return ChatbotResponse.create_error_response(
            message=(
                "I couldn't find relevant campaign information for your "
                "question. Please try rephrasing or ask about a specific "
                "campaign, metric, topic or segment!"
            )
        ).to_dict()


def chat_query(user_query: str, thread_id: str = "default",
               user_id: str = None) -> Dict[str, Any]:
    """Main chat function - uses LangGraph agent with SQLite checkpointer."""
    return chat_query_with_custom_agent(user_query, thread_id, user_id)


def clear_memory(thread_id: str = "default", user_id: str = None):
    """Clear conversation history for a specific thread."""
    return memory_manager.clear_memory(thread_id, user_id)


def get_memory_stats(thread_id: str = "default", user_id: str = None):
    """Get statistics about conversation history for a thread."""
    return memory_manager.get_memory_stats(thread_id, user_id)

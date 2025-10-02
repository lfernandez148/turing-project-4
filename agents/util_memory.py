"""Memory utilities for chatbot conversation management."""

from loguru import logger
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from typing import Dict, Any, List


class MemoryManager:
    """Manages conversation memory and history for the chatbot."""
    
    def __init__(self, checkpointer: SqliteSaver, conn: sqlite3.Connection):
        """Initialize the memory manager."""
        self.checkpointer = checkpointer
        self.conn = conn
    
    def clear_memory(self, thread_id: str = "default", user_id: str = None) -> Dict[str, Any]:
        """Clear conversation history for a specific thread."""
        try:
            # Use the same database connection that the checkpointer uses
            cursor = self.conn.cursor()
            
            # Clear all checkpoints for this specific thread_id
            cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            self.conn.commit()
            
            logger.info(f"Cleared conversation history for thread: {thread_id}, user: {user_id}")
            return {"status": "success", "thread_id": thread_id, "user_id": user_id}
            
        except Exception as e:
            logger.error(f"Error clearing memory for thread {thread_id}, user {user_id}: {e}")
            return {"status": "error", "message": str(e)}

    def get_memory_stats(self, thread_id: str = "default", user_id: str = None) -> Dict[str, Any]:
        """Get statistics about conversation history for a thread."""
        try:
            thread_config = {
                "configurable": {
                    "thread_id": thread_id,
                    "user_id": user_id or "anonymous"
                }
            }
            
            # Get current state for this thread
            checkpoint_tuple = self.checkpointer.get_tuple(thread_config)
            if checkpoint_tuple and checkpoint_tuple.checkpoint:
                messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
                return {
                    "thread_id": thread_id,
                    "user_id": user_id,
                    "total_messages": len(messages),
                    "user_messages": len([m for m in messages if isinstance(m, HumanMessage)]),
                    "ai_messages": len([m for m in messages if isinstance(m, AIMessage)]),
                    "storage": "SQLite",
                    "status": "active" if messages else "empty"
                }
            else:
                return {
                    "thread_id": thread_id,
                    "user_id": user_id,
                    "total_messages": 0,
                    "storage": "SQLite",
                    "status": "empty"
                }
                
        except Exception as e:
            logger.error(f"Error getting memory stats for thread {thread_id}, user {user_id}: {e}")
            return {
                "thread_id": thread_id,
                "user_id": user_id,
                "status": "error",
                "message": str(e)
            }

    def load_conversation_history(self, user_id: str, thread_id: str, token_tracker, limit: int = 20) -> List[BaseMessage]:
        """Load conversation history from SQLite and convert to LangChain messages."""
        try:
            # Get chat history from database (only text messages for context)
            history = token_tracker.get_chat_history(user_id, thread_id, limit * 2)  # Get more to account for filtering
            
            messages = []
            text_message_count = 0
            
            for record in history:
                # Only include text messages for conversation context
                if record.get("response_type") == "text" and text_message_count < limit:
                    if record["role"] == "user":
                        messages.append(HumanMessage(content=record["content"]))
                        text_message_count += 1
                    elif record["role"] == "assistant":
                        messages.append(AIMessage(content=record["content"]))
                        text_message_count += 1
            
            logger.info(f"Loaded {len(messages)} text messages from chat history for thread {thread_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error loading conversation history: {e}")
            return []


# Standalone functions for backward compatibility
def load_conversation_history(token_tracker, user_id: str, thread_id: str, limit: int = 20) -> List[BaseMessage]:
    """Standalone function to load conversation history."""
    memory_manager = MemoryManager(None, None)
    return memory_manager.load_conversation_history(user_id, thread_id, token_tracker, limit)

"""Utilities for handling Deepseek model responses and tool calls."""

import re
import json
from loguru import logger
from langchain_core.messages import AIMessage
from typing import List, Dict, Any


def parse_deepseek_tool_calls(content: str) -> List[Dict[str, Any]]:
    """Parse Deepseek's custom tool call format and convert to LangChain format."""
    tool_calls = []
    
    # Pattern to match [TOOL_REQUEST]...json...[END_TOOL_REQUEST]
    pattern = r'\[TOOL_REQUEST\]\s*(\{.*?\})\s*\[END_TOOL_REQUEST\]'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for i, match in enumerate(matches):
        try:
            # Parse the JSON tool request
            tool_data = json.loads(match.strip())
            
            # Convert to LangChain tool call format
            tool_call = {
                "id": f"call_{i}_{tool_data['name']}",
                "name": tool_data["name"],
                "args": tool_data.get("arguments", {})
            }
            tool_calls.append(tool_call)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool call JSON: {match}, error: {e}")
            continue
    
    return tool_calls


def clean_deepseek_content(content: str) -> str:
    """Remove tool request markers, tool results, and thinking blocks from content for cleaner display."""
    # Remove [TOOL_REQUEST]....[END_TOOL_REQUEST] blocks
    pattern = r'\[TOOL_REQUEST\].*?\[END_TOOL_REQUEST\]'
    cleaned = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Remove [TOOL_RESULT]....[END_TOOL_RESULT] blocks
    tool_result_pattern = r'\[TOOL_RESULT\].*?\[END_TOOL_RESULT\]'
    cleaned = re.sub(tool_result_pattern, '', cleaned, flags=re.DOTALL)
    
    # Remove <think>...</think> blocks
    think_pattern = r'<think>.*?</think>'
    cleaned = re.sub(think_pattern, '', cleaned, flags=re.DOTALL)
    
    # Clean up extra whitespace and newlines
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned.strip())
    
    return cleaned


def process_deepseek_response(response: AIMessage) -> AIMessage:
    """Process a Deepseek response to handle tool calls and clean content."""
    if not hasattr(response, 'content'):
        return response
    
    content = response.content
    
    # Check if this is a Deepseek model response with custom tool format
    if '[TOOL_REQUEST]' in content:
        logger.info("Detected Deepseek tool call format, parsing...")
        logger.info(f"Original content: {content}")
        
        # Parse Deepseek's tool calls
        tool_calls = parse_deepseek_tool_calls(content)
        
        if tool_calls:
            logger.info(f"Parsed {len(tool_calls)} tool calls: {tool_calls}")
            
            # Clean the content by removing tool request markers and think blocks
            cleaned_content = clean_deepseek_content(content)
            
            # Create a new message with proper tool calls and cleaned content
            response = AIMessage(
                content=cleaned_content,
                tool_calls=tool_calls
            )
            logger.info(f"Created new message with tool calls: {response.tool_calls}")
    
    # Also clean content for responses without tool calls but with think blocks or tool results
    elif '<think>' in content or '[TOOL_RESULT]' in content:
        logger.info("Detected Deepseek thinking blocks or tool results, cleaning...")
        cleaned_content = clean_deepseek_content(content)
        response = AIMessage(content=cleaned_content)
        logger.info("Cleaned thinking blocks and tool results from content")
    
    return response

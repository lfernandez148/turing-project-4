#!/usr/bin/env python3
"""
Generate Memory Management diagram for Campaign Assistant
Based on the Mermaid diagram in README_V2.md
"""

import graphviz
import os

def create_memory_management_diagram():
    """Create a memory management diagram showing the dual-layer memory system."""
    
    # Create a new directed graph
    dot = graphviz.Digraph(
        'memory_management',
        comment='Campaign Assistant Memory Management',
        format='png'
    )
    
    # Set graph attributes for better layout
    dot.attr(rankdir='TB', size='12,10', dpi='300')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial', fontsize='10')
    dot.attr('edge', fontname='Arial', fontsize='9')
    
    # Define color scheme
    colors = {
        'input': '#E8F5E8',
        'agent': '#E3F2FD',
        'memory': '#FFEBEE',
        'short_term': '#FFF3E0',
        'long_term': '#F3E5F5',
        'storage': '#E0F2F1',
        'output': '#E8F5E8'
    }
    
    # Add nodes
    dot.node('user_query', 'User Query', 
             fillcolor=colors['input'], 
             shape='ellipse',
             style='filled,bold')
    
    dot.node('langgraph_agent', 'LangGraph Agent\n\n• Query processing\n• Tool selection\n• Response generation', 
             fillcolor=colors['agent'])
    
    dot.node('memory_layer', 'Memory Layer\n\n• Context management\n• History retrieval\n• State coordination', 
             fillcolor=colors['memory'],
             shape='diamond')
    
    dot.node('short_term_memory', 'Short-Term Memory\n\n• Session context\n• Active conversation\n• Tool usage history\n• Real-time state', 
             fillcolor=colors['short_term'])
    
    dot.node('long_term_memory', 'Long-Term Memory\n\n• Persistent history\n• Cross-session data\n• User preferences\n• Analytics data', 
             fillcolor=colors['long_term'])
    
    dot.node('session_state', 'Session State\n\n• Current conversation\n• LangGraph checkpoints\n• Temporary data\n• Active tools', 
             fillcolor=colors['storage'])
    
    dot.node('sqlite_database', 'SQLite Database\n\n• conversations.db\n• token_usage table\n• chat_history table\n• user sessions', 
             fillcolor=colors['storage'])
    
    dot.node('response_generation', 'Response Generation\n\n• Context-aware responses\n• Memory integration\n• Source attribution\n• Formatted output', 
             fillcolor=colors['agent'])
    
    dot.node('user_response', 'User Response', 
             fillcolor=colors['output'],
             shape='ellipse',
             style='filled,bold')
    
    dot.node('save_to_database', 'Save to Database\n\n• Store conversation\n• Update context\n• Track tokens\n• Maintain history', 
             fillcolor=colors['storage'])
    
    # Add edges
    dot.edge('user_query', 'langgraph_agent', 'Process Query')
    
    dot.edge('langgraph_agent', 'memory_layer', 'Access Memory')
    
    dot.edge('memory_layer', 'short_term_memory', 'Session Context')
    dot.edge('memory_layer', 'long_term_memory', 'Historical Context')
    
    dot.edge('short_term_memory', 'session_state', 'Current State')
    dot.edge('long_term_memory', 'sqlite_database', 'Persistent Storage')
    
    dot.edge('session_state', 'response_generation', 'Context Data')
    dot.edge('sqlite_database', 'response_generation', 'Historical Data')
    
    dot.edge('response_generation', 'user_response', 'Generated Response')
    
    dot.edge('user_response', 'save_to_database', 'Store Interaction')
    dot.edge('save_to_database', 'long_term_memory', 'Update History')
    
    return dot

def main():
    """Generate the Memory Management diagram."""
    print("🎨 Generating Memory Management Diagram...")
    
    # Create the diagram
    dot = create_memory_management_diagram()
    
    # Set output directory
    output_dir = '/Users/lolo/shared/projects/turing/sprint-3/project-23/documentation/diagrams'
    output_file = os.path.join(output_dir, 'memory_management')
    
    # Render the diagram
    try:
        dot.render(output_file, cleanup=True)
        print(f"✅ Diagram saved to: {output_file}.png")
        
        # Also save the source code
        with open(f"{output_file}.gv", 'w') as f:
            f.write(dot.source)
        print(f"✅ Source code saved to: {output_file}.gv")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating diagram: {e}")
        return False

if __name__ == "__main__":
    main()
